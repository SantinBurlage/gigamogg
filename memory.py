"""Нити — память GIGAMOGG.

Нить это один разговор: тема, набор реплик, ключевые слова, вектор темы и
связи с другими нитями. Нити настоящие: лежат на диске в threads.json, умеют
находиться по смыслу, помнят оценку ответов и переживают перезапуск.

Разметка вектора темы сделана на хешировании слов — без внешних библиотек,
но работает как обычная мешковая модель: близкие по смыслу нити находят друг друга.
"""
from __future__ import annotations

import json
import math
import os
import re
import threading
import time
import uuid
from collections import Counter

DIM = 256
_WORD = re.compile(r"[а-яёa-z0-9]{2,}")
_STOP = {
    "это", "что", "как", "так", "все", "всё", "для", "или", "его", "её", "ее", "они",
    "она", "оно", "был", "была", "были", "есть", "уже", "ещё", "еще", "мне", "меня",
    "тебя", "вас", "нас", "там", "тут", "здесь", "когда", "тогда", "чтобы", "если",
    "the", "and", "you", "are", "for", "with", "что-то", "этот", "эта", "эти",
}


def stem(w: str) -> str:
    """Примитивная нормализация: убираем частые окончания, чтобы «космос» и «космоса» совпали."""
    for suf in ("иями", "ями", "ами", "ией", "иях", "ах", "ях", "ов", "ев", "ий", "ый",
                "ой", "ая", "ое", "ые", "ие", "ам", "ям", "ом", "ем", "ах", "у", "ю",
                "а", "я", "ы", "и", "е", "о", "ь"):
        if len(w) - len(suf) >= 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def keywords(text: str, limit: int = 12) -> list[str]:
    words = [stem(w) for w in _WORD.findall(text.lower())]
    words = [w for w in words if w not in _STOP and len(w) > 2]
    return [w for w, _ in Counter(words).most_common(limit)]


def vector(text: str) -> list[float]:
    """Мешок слов с хешированием в DIM измерений, нормированный по длине."""
    v = [0.0] * DIM
    for w in (stem(x) for x in _WORD.findall(text.lower())):
        if w in _STOP or len(w) < 3:
            continue
        h = hash(w)
        v[h % DIM] += 1.0
        v[(h // DIM) % DIM] += 0.5           # второе измерение снижает число случайных совпадений
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def now() -> float:
    return time.time()


class Thread:
    def __init__(self, data: dict):
        self.id: str = data.get("id") or uuid.uuid4().hex[:12]
        self.title: str = data.get("title") or "Новая нить"
        self.created: float = data.get("created", now())
        self.updated: float = data.get("updated", now())
        self.turns: list[dict] = data.get("turns", [])
        self.tier: str = data.get("tier", "mid")
        self.tags: list[str] = data.get("tags", [])
        self.vector: list[float] = data.get("vector") or []
        self.links: list[str] = data.get("links", [])
        self.rating: float = float(data.get("rating", 0.0))
        self.fixed: int = int(data.get("fixed", 0))      # сколько раз модель сама исправлялась
        self.heat: float = float(data.get("heat", 0.0))
        self.pinned: bool = bool(data.get("pinned"))
        self.owner: str = data.get("owner", "")           # привязка к пользователю (username)
        if not self.vector:
            self.recompute()

    # ---------------------------------------------------------------- свойства
    @property
    def size(self) -> int:
        return len(self.turns)

    @property
    def last(self) -> str:
        for t in reversed(self.turns):
            if t.get("role") == "bot":
                return t.get("text", "")
        return ""

    @property
    def alive(self) -> float:
        """Свежесть нити: затухает примерно за неделю, но подогревается новыми репликами."""
        age = max(0.0, now() - self.updated)
        decay = math.exp(-age / (7 * 86400))
        weight = min(1.0, 0.25 + self.size / 40)
        return round(decay * weight + self.heat * 0.15, 4)

    # ---------------------------------------------------------------- работа
    def recompute(self):
        text = self.title + " " + " ".join(
            t.get("text", "") for t in self.turns[:40]
        )
        self.vector = vector(text)
        kw = keywords(text)
        self.tags = kw[:6]
        if self.turns and self.title == "Новая нить":
            first = next((t["text"] for t in self.turns if t.get("role") == "user"), "")
            if first:
                self.title = (first[:48] + "…") if len(first) > 48 else first

    def add(self, role: str, text: str, tier: str | None = None, meta: dict | None = None):
        self.turns.append(dict(role=role, text=text, at=now(),
                               tier=tier or self.tier, **(meta or {})))
        self.tier = tier or self.tier
        self.updated = now()
        self.heat = min(1.0, self.heat + 0.05)
        self.recompute()

    def context(self, limit: int = 12, drop_system: bool = True) -> list[dict]:
        out = []
        for t in self.turns[-limit:]:
            if drop_system and t.get("role") == "system" and t.get("meta") is None:
                pass
            out.append(dict(role=t.get("role"), text=t.get("text", "")))
        return out

    def rate(self, value: float):
        value = max(-1.0, min(1.0, float(value)))
        self.rating = round(self.rating * 0.7 + value * 0.3, 4)
        self.heat = min(1.0, max(0.0, self.heat + value * 0.1))
        self.updated = now()

    def summary(self, deep: bool = False) -> dict:
        d = dict(id=self.id, title=self.title, created=self.created, updated=self.updated,
                 size=self.size, tier=self.tier, tags=self.tags, rating=round(self.rating, 3),
                 heat=round(self.alive, 4), fixed=self.fixed, pinned=self.pinned,
                 links=self.links, preview=self.last[:140], owner=self.owner)
        if deep:
            d["turns"] = self.turns
            d["keywords"] = self.tags
        return d

    def dump(self) -> dict:
        return dict(id=self.id, title=self.title, created=self.created, updated=self.updated,
                    turns=self.turns, tier=self.tier, tags=self.tags, vector=self.vector,
                    links=self.links, rating=self.rating, fixed=self.fixed, heat=self.heat,
                    pinned=self.pinned, owner=self.owner)


class ThreadStore:
    """Хранилище нитей с автосохранением. Все операции под одним замком."""

    def __init__(self, path: str = "threads.json", autosave: bool = True):
        self.path = path
        self.autosave = autosave
        self.lock = threading.RLock()
        self.threads: dict[str, Thread] = {}
        self.dirty = False
        self.load()

    # ---------------------------------------------------------------- файл
    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            for d in data.get("threads", []):
                t = Thread(d)
                self.threads[t.id] = t
        except Exception:
            self.threads = {}

    def save(self, force: bool = False):
        with self.lock:
            if not (self.dirty or force):
                return
            tmp = self.path + ".tmp"
            payload = dict(version=2, saved=now(),
                           threads=[t.dump() for t in self.threads.values()])
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, self.path)
            self.dirty = False

    def maybe_save(self):
        self.dirty = True
        if self.autosave:
            self.save()

    # ---------------------------------------------------------------- нити
    def create(self, title: str | None = None, tier: str = "mid", tags=None, owner: str = "") -> Thread:
        with self.lock:
            t = Thread(dict(title=title or "Новая нить", tier=tier, tags=list(tags or []), owner=owner))
            self.threads[t.id] = t
            self.maybe_save()
            return t

    def get(self, tid: str) -> Thread | None:
        return self.threads.get(tid)

    def ensure(self, tid: str | None, tier: str = "mid", owner: str = "") -> Thread:
        with self.lock:
            if tid and tid in self.threads:
                return self.threads[tid]
            t = self.threads.get(tid) if tid else None
            return t or self.create(tier=tier, owner=owner)

    def drop(self, tid: str) -> bool:
        with self.lock:
            ok = self.threads.pop(tid, None) is not None
            for t in self.threads.values():
                if tid in t.links:
                    t.links = [x for x in t.links if x != tid]
            self.maybe_save()
            return ok

    def rename(self, tid: str, title: str) -> bool:
        with self.lock:
            t = self.threads.get(tid)
            if not t:
                return False
            t.title = title.strip()[:80] or t.title
            t.updated = now()
            self.maybe_save()
            return True

    def pin(self, tid: str, value: bool | None = None) -> bool:
        with self.lock:
            t = self.threads.get(tid)
            if not t:
                return False
            t.pinned = (not t.pinned) if value is None else bool(value)
            self.maybe_save()
            return t.pinned

    # ---------------------------------------------------------------- поиск
    def list(self, order: str = "heat", limit: int = 100, owner: str = "") -> list[dict]:
        with self.lock:
            items = list(self.threads.values())
        # Фильтрация по владельцу: каждый пользователь видит только свои чаты
        if owner:
            items = [t for t in items if t.owner == owner or t.owner == ""]
        keys = {
            "heat": lambda t: (t.pinned, t.alive),
            "new": lambda t: (t.pinned, t.updated),
            "old": lambda t: (t.pinned, -t.updated),
            "size": lambda t: (t.pinned, t.size),
            "rating": lambda t: (t.pinned, t.rating),
        }
        items.sort(key=keys.get(order, keys["heat"]), reverse=True)
        return [t.summary() for t in items[:limit]]

    def search(self, query: str, limit: int = 8) -> list[tuple[Thread, float]]:
        qv = vector(query)
        qk = set(keywords(query))
        scored = []
        with self.lock:
            items = list(self.threads.values())
        for t in items:
            sem = cosine(qv, t.vector)
            overlap = len(qk & set(t.tags)) / max(1, len(qk))
            score = sem * 0.65 + overlap * 0.35
            score *= 0.6 + 0.4 * t.alive          # свежие нити важнее
            if t.pinned:
                score += 0.1
            if score > 0.03:
                scored.append((t, round(score, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def recall(self, query: str, exclude: str | None = None, limit: int = 3,
               min_score: float = 0.08) -> list[dict]:
        """Что вспомнить по теме запроса: короткие выжимки из похожих нитей."""
        out = []
        for t, score in self.search(query, limit=limit + 2):
            if t.id == exclude or score < min_score:
                continue
            lines = [f"{'Человек' if x['role'] == 'user' else 'GIGAMOGG'}: {x['text']}"
                     for x in t.turns[-4:]]
            out.append(dict(id=t.id, title=t.title, score=score, text="\n".join(lines)))
            if len(out) >= limit:
                break
        return out

    # ---------------------------------------------------------------- связи
    def relink(self, threshold: float = 0.42, max_links: int = 4):
        """Считает связи между нитями по близости тем. Нужно для графа в админке."""
        with self.lock:
            items = list(self.threads.values())
            for t in items:
                scored = []
                for o in items:
                    if o.id == t.id:
                        continue
                    sem = cosine(t.vector, o.vector)
                    shared = len(set(t.tags) & set(o.tags))
                    score = sem + 0.1 * shared
                    if score >= threshold:
                        scored.append((o.id, score))
                scored.sort(key=lambda x: x[1], reverse=True)
                t.links = [i for i, _ in scored[:max_links]]
            self.maybe_save()

    def graph(self, limit: int = 60) -> dict:
        with self.lock:
            items = sorted(self.threads.values(), key=lambda t: t.alive, reverse=True)[:limit]
            ids = {t.id for t in items}
            nodes = [dict(id=t.id, title=t.title, size=t.size, heat=t.alive, tier=t.tier,
                          rating=round(t.rating, 3), tags=t.tags[:4], pinned=t.pinned,
                          updated=t.updated) for t in items]
            edges = []
            seen = set()
            for t in items:
                for o in t.links:
                    if o in ids and (o, t.id) not in seen:
                        seen.add((t.id, o))
                        edges.append(dict(source=t.id, target=o,
                                          weight=round(cosine(t.vector, self.threads[o].vector), 3)))
        return dict(nodes=nodes, edges=edges)

    # ---------------------------------------------------------------- сводка
    def stats(self) -> dict:
        with self.lock:
            items = list(self.threads.values())
        if not items:
            return dict(count=0, turns=0, avg_size=0, top=[], keywords=[], fixed=0,
                        rating=0.0, active=0)
        kw = Counter()
        for t in items:
            kw.update(t.tags)
        week = now() - 7 * 86400
        return dict(
            count=len(items),
            turns=sum(t.size for t in items),
            avg_size=round(sum(t.size for t in items) / len(items), 1),
            fixed=sum(t.fixed for t in items),
            rating=round(sum(t.rating for t in items) / len(items), 3),
            active=sum(1 for t in items if t.updated > week),
            top=[t.summary() for t in sorted(items, key=lambda x: x.alive, reverse=True)[:6]],
            keywords=[dict(word=w, count=c) for w, c in kw.most_common(18)],
        )
    def smart_context(self, question: str, limit: int = 12) -> list[dict]:
        """Умный подбор контекста по смыслу — БЕЗ PyTorch и внешних библиотек."""
        from . import memory
        import math

        q_vec = memory.vector(question)
        if not q_vec:
            return []

        with memory.Store().lock:
            threads = list(memory.Store().threads.values())

        scored = []
        for t in threads:
            if not t.vector:
                continue
            # Семантическая близость (cosine)
            sem = memory.cosine(q_vec, t.vector)
            # Фактическая релевантность — насколько тред "отвечает" вопросу
            relevance = 0.0
            for turn in reversed(t.turns):
                if turn.get("role") == "user":
                    rel = memory.cosine(memory.vector(turn.get("text", "")), q_vec)
                    relevance = max(relevance, rel)

            # Общие слова = усиление связи
            shared_words = len(set(memory.keywords(question)) & set(t.tags))

            # Итоговый скор — с упором на семантику и релевантность
            score = (sem * 0.6 + relevance * 0.3 + min(1.0, shared_words * 0.1))

            if score > 0.15:  # порог вменяемой связи
                scored.append((t, score))

        # Сортируем по скору
        scored.sort(key=lambda x: x[1], reverse=True)

        # Берём N самых релевантных нитей
        result = []
        for thread, score in scored[:limit]:
            result.append(
                dict(
                    id=thread.id,
                    title=thread.title,
                    score=round(score, 3),
                    turns=thread.context()  # последние N реплик
                )
            )

        return result