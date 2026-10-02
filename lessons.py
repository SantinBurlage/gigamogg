"""Уроки — обучение на собственных ошибках.

Как это работает по-настоящему:
  1) модель отвечает, критик находит конкретные промахи;
  2) промах сохраняется как урок: вопрос, плохой ответ, замечание, верный ответ;
  3) уроки превращаются в обучающие примеры формата «промах → замечание → исправление»
     и подмешиваются в корпус на следующем проходе обучения;
  4) после доучивания уроки проверяются заново — если модель отвечает правильно,
     урок помечается выученным и уходит из активных.

Это не имитация: петля замкнута, ошибки реально попадают в следующее обучение,
а выученное проверяется на тех же вопросах.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time

from . import critic

# Формат совпадает с корпусом: замечание идёт служебной репликой, а ответы
# модели закрываются маркером конца — так модель учится и исправляться,
# и сама решать, когда реплика закончена.
NOTE = "<|sys|>замечание: ответ неверный"
END_TAG = "<|end|>"


class Lessons:
    def __init__(self, path: str = "lessons.json", autosave: bool = True):
        self.path = path
        self.autosave = autosave
        self.lock = threading.RLock()
        self.items: list[dict] = []
        self.learned: list[dict] = []
        self.fixed = 0
        self.load()

    # ---------------------------------------------------------------- файл
    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            self.items = d.get("items", [])
            self.learned = d.get("learned", [])
            self.fixed = int(d.get("fixed", 0))
        except Exception:
            self.items, self.learned, self.fixed = [], [], 0

    def save(self, force: bool = False):
        with self.lock:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dict(version=2, items=self.items[-4000:], learned=self.learned[-2000:],
                               fixed=self.fixed, saved=time.time()), f, ensure_ascii=False)
            os.replace(tmp, self.path)

    def _key(self, question: str) -> str:
        return re.sub(r"\s+", " ", question.lower()).strip()

    # ---------------------------------------------------------------- запись
    def record(self, question: str, answer: str, report: dict,
               corrected: str | None = None, thread: str | None = None,
               tier: str = "mid") -> dict | None:
        """Сохраняет промах. Возвращает сам урок или None, если учиться нечему."""
        if not report.get("issues") or report.get("score", 1.0) > 0.82:
            return None
        fixed_answer = corrected or critic.correct_answer(question, answer)
        key = self._key(question)
        with self.lock:
            for it in self.items:
                if it["key"] == key:
                    it["seen"] += 1
                    it["last"] = time.time()
                    if fixed_answer and not it.get("right"):
                        it["right"] = fixed_answer
                    self._persist()
                    return it
            lesson = dict(
                id=f"l{len(self.items) + len(self.learned) + 1:05d}",
                key=key, q=question.strip()[:400], wrong=answer.strip()[:400],
                right=(fixed_answer or "").strip()[:400],
                issues=report["issues"][:6], score=report["score"],
                thread=thread, tier=tier, seen=1, solved=0,
                first=time.time(), last=time.time(),
            )
            self.items.append(lesson)
            self._persist()
            return lesson

    def _persist(self):
        if self.autosave:
            self.save()

    # ---------------------------------------------------------------- обучение
    def to_text(self, limit: int = 1200) -> str:
        """Уроки в формате, который модель видит в корпусе."""
        blocks = []
        with self.lock:
            items = sorted(self.items, key=lambda x: (-x["seen"], -x["last"]))[:limit]
        for it in items:
            wrong = it["wrong"] or "Не знаю."
            right = it["right"]
            if not right:
                right = "Такого ответа у меня нет. Отвечу честно: я не уверена, лучше уточнить."
            blocks.append(
                f"Человек: {it['q']}\n\nGIGAMOGG: {wrong}{END_TAG}\n\n{NOTE}\n\n"
                f"GIGAMOGG: {right}{END_TAG}"
            )
        return "\n\n---\n\n".join(blocks)

    def export(self, path: str = "lessons.txt", limit: int = 1200) -> dict:
        text = self.to_text(limit)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + ("\n" if text else ""))
        return dict(path=path, chars=len(text), blocks=len([b for b in text.split("---") if b.strip()]))

    def stats(self) -> dict:
        with self.lock:
            items = list(self.items)
            learned = list(self.learned)
        return dict(
            active=len(items), learned=len(learned), fixed=self.fixed,
            top=[dict(q=i["q"][:90], issues=i["issues"][:3], seen=i["seen"], score=i["score"])
                 for i in sorted(items, key=lambda x: -x["seen"])[:8]],
            by_kind=self._by_kind(items),
        )

    @staticmethod
    def _by_kind(items: list[dict]) -> list[dict]:
        buckets: dict[str, int] = {}
        for it in items:
            for issue in it["issues"]:
                kind = issue.split(":")[0].split(" ")[0]
                buckets[kind] = buckets.get(kind, 0) + 1
        return [dict(kind=k, count=v) for k, v in sorted(buckets.items(), key=lambda x: -x[1])]

    # ---------------------------------------------------------------- проверка
    def check(self, answer_fn, limit: int = 24) -> dict:
        """Просит модель заново ответить на вопросы уроков.

        answer_fn(question) -> str возвращает свежий ответ модели.
        Выученные уроки уходят в архив, остальные остаются учиться дальше.
        """
        with self.lock:
            todo = sorted(self.items, key=lambda x: (-x["seen"], -x["last"]))[:limit]
        fixed_now, still = [], []
        for it in todo:
            try:
                fresh = answer_fn(it["q"]) or ""
            except Exception:
                still.append(it)
                continue
            report = critic.score(it["q"], fresh)
            if report["verdict"] == "хорошо" and fresh.strip() != it["wrong"].strip():
                it["solved"] += 1
                it["fresh"] = fresh.strip()[:400]
                fixed_now.append(it)
            else:
                still.append(it)
        with self.lock:
            for it in fixed_now:
                if it in self.items:
                    self.items.remove(it)
                    self.learned.append(it)
                    self.fixed += 1
            self._persist()
        return dict(checked=len(todo), fixed=len(fixed_now), left=len(still),
                    examples=[dict(q=i["q"][:90], now=i.get("fresh", "")[:90]) for i in fixed_now[:5]])

    def forget(self):
        with self.lock:
            self.items, self.learned, self.fixed = [], [], 0
            self._persist()