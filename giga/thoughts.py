"""Поток мыслей — то, что у модели «в голове», в реальном времени.

Это не картинка-украшение. Данные настоящие:
  * токены-мысли — что модель предлагает сказать прямо сейчас, с весами;
  * нейроны-узлы — по одному на канал на каждом слое, яркость из энергии активаций;
  * рёбра — реальные веса внимания: от последнего токена к токенам контекста;
  * нить-фокус — куда именно сейчас смотрит внимание в каждом слое;
  * энтропия голов — насколько модель уверена или разбросана.

Пока модель генерирует ответ, поток пишется кадр за кадром. Затем кадры
проигрываются в админ-панели как живая сеть: узлы бегут из слоя в слой,
яркость пульсирует, фокус перескакивает.
"""
from __future__ import annotations

import threading
import time

import torch

NEURONS_PER_LAYER = 28          # сколько видимых нейронов рисуем на слой
MAX_STEPS = 48                  # сколько шагов генерации записываем как кадры
MAX_CONTOUR = 8                 # сколько слов-мыслей показываем одновременно


def contour(tok, ids, limit: int = MAX_CONTOUR) -> list[dict]:
    """Слова-кандидаты с весами — «о чём модель думает прямо сейчас»."""
    out = []
    for item in ids[:limit]:
        try:
            piece = tok.decode([item["token"]]).replace("\n", "⏎").strip()
        except Exception:
            piece = ""
        if not piece:
            continue
        out.append(dict(token=item.get("token", 0), text=piece[:18], weight=item["weight"]))
    return out


def snapshot_frame(model, tok, step: int, text_so_far: str) -> dict:
    """Один кадр внутренней жизни модели."""
    snap = model.thought_snapshot()
    layers = []
    for i, L in enumerate(snap["layers"]):
        focus = L["focus"] or []
        # распределяем 28 видимых нейронов по силе внимания: активные узлы ярче
        n = NEURONS_PER_LAYER
        if focus:
            idx = sorted(range(len(focus)), key=lambda j: -focus[j])[:n]
            vals = [focus[j] for j in idx]
            peak = max(vals) or 1.0
            nodes = [dict(slot=k, gain=round(min(1.0, vals[k] / peak), 3),
                          token_pos=int(idx[k])) for k in range(len(idx))]
        else:
            nodes = [dict(slot=k, gain=0.0, token_pos=-1) for k in range(n)]
        layers.append(dict(layer=i, nodes=nodes, sharpness=L["sharpness"] or 0.0,
                           energy=L["energy"] or 0.0,
                           heads=L["heads"] or []))
    return dict(step=step, at=time.time(), layers=layers,
                contour=contour(tok, snap["proposal"]),
                sharpness=snap["sharpness"] or 0.0, text=text_so_far[-160:])


class ThoughtStream:
    """Живой поток мыслей с общей памятью кадров.

    Пишется во время генерации ответа, читается админ-панелью. Один замок на
    запись, поэтому читатель никогда не увидит половину кадра.
    """
    def __init__(self, keep: int = 600, fps: float = 30.0):
        self.lock = threading.RLock()
        self.frames: list[dict] = []
        self.keep = keep
        self.fps = fps
        self.seq = 0
        self.readers = 0
        self.last = None
        self.mind: dict = {}          # долговременное состояние: слова, темы, химия
        self._new = threading.Event()

    # ---------------------------------------------------------------- запись
    def reset(self, tier: str = ""):
        with self.lock:
            self.frames = []
            self.seq = 0
            self.mind = self._empty_mind(tier)
            self._new.set()

    @staticmethod
    def _empty_mind(tier: str) -> dict:
        return dict(tier=tier, running=False, step=0, mood="спокойна", focus_word="",
                    sharpness=0.0, temperature=0.0, thoughts=[], started=0.0)

    def start(self, tier: str, prompt: str, temperature: float):
        self.reset(tier)
        with self.lock:
            self.mind.update(running=True, started=time.time(), prompt=prompt[:160],
                             temperature=temperature, mood="думаю")
        return self.seq

    def push(self, frame: dict):
        with self.lock:
            self.frames.append(frame)
            if len(self.frames) > self.keep:
                self.frames = self.frames[-self.keep:]
            self.seq += 1
            self.last = frame
            m = self.mind
            m["step"] = frame["step"]
            m["sharpness"] = frame.get("sharpness") or 0.0
            m["thoughts"] = frame.get("contour", [])
            m["focus_word"] = (frame.get("contour") or [{}])[0].get("text", "")
            m["layers"] = len(frame.get("layers", []))
            self._new.set()
        return self.seq

    def finish(self, mood: str = "спокойна"):
        with self.lock:
            self.mind.update(running=False, mood=mood, finished=time.time())
            self._new.set()

    # ---------------------------------------------------------------- чтение
    def since(self, cursor: int = 0, limit: int = 48) -> dict:
        with self.lock:
            total = self.seq
            if cursor >= total:
                return dict(cursor=total, total=total, frames=[], mind=dict(self.mind),
                            alive=False, drift=0)
            start = max(0, len(self.frames) - (total - cursor))
            frames = self.frames[start:start + limit]
            return dict(cursor=cursor + len(frames), total=total, frames=frames,
                        mind=dict(self.mind), alive=True,
                        drift=round(len(self.frames) - (total - cursor), 2))

    def snapshot(self) -> dict:
        with self.lock:
            return dict(frames=self.frames[-MAX_STEPS:], mind=dict(self.mind), total=self.seq)

    def demo(self, model, tok, prompt_ids, n: int = 40, temperature: float = 0.8):
        """Прогнать генерацию только ради внутренностей — без выдачи текста."""
        if not model:
            return 0
        model.set_capture(True)
        try:
            idx = torch.tensor([prompt_ids[-model.block:]], device=next(model.parameters()).device)
            with torch.no_grad():
                _, past = model.forward_cache(idx, None, 0)
                offset = idx.size(1)
                for s in range(n):
                    frame = snapshot_frame(model, tok, s, "")
                    self.push(frame)
                    nxt = int(frame["contour"][0]["token"]) if frame["contour"] else 0
                    t = torch.tensor([[nxt]], device=idx.device)
                    _, past = model.forward_cache(t, past, offset)
                    offset += 1
                    if offset >= model.block:
                        break
                    time.sleep(1.0 / self.fps)
        finally:
            model.set_capture(False)
        return n

    # ---------------------------------------------------------------- сводка
    def mood_report(self) -> dict:
        """Химия модели: настроение по уверенности, разбросу и температуре."""
        with self.lock:
            m = dict(self.mind)
            frames = self.frames[-20:]
        if not frames:
            return dict(mood="спит", sharpness=0.0, drift=0.0, alive=False, note="модель ждёт запроса")
        sharp = sum(f.get("sharpness") or 0 for f in frames) / len(frames)
        spread = sum(len(set(x["text"] for x in f.get("contour", []))) for f in frames) / len(frames)
        mood = ("собрана" if sharp > 0.6 else "размышляет" if sharp > 0.35 else "колеблется")
        note = {
            "собрана": "внимание сфокусировано, ответ почти готов",
            "размышляет": "идут обычные вычисления по слоям",
            "колеблется": "много равнозначных вариантов, высокая неопределённость",
        }[mood]
        return dict(mood=mood, sharpness=round(sharp, 3), drift=round(spread, 2),
                    alive=m.get("running", False), note=note,
                    focus_word=m.get("focus_word", ""), step=m.get("step", 0))


STREAM = ThoughtStream()