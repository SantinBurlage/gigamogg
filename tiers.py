"""Уровни модели: от superlow до ultra.

Уровень — это не наклейка, а реальный набор чисел: ширина, глубина, головы,
длина контекста, сколько веток ответа пробовать и сколько уроков тянуть в промпт.
Чем выше уровень, тем больше параметров и тем дольше он думает.
"""
from __future__ import annotations

import os

# name -> (width, layers, heads, kv_heads, block, drop, candidates, memory_slots, threads)
# candidates: сколько вариантов ответа сгенерировать и отобрать лучший
# memory_slots: сколько прошлых реплик подмешивать в контекст
# threads: сколько нитей показывать в админ-панели
SPECS = {
    "superlow": dict(width=192, layers=4, heads=4, kv_heads=2, block=256, drop=0.05,
                     candidates=1, memory_slots=2, threads=4, name="GIGAMOGG Nano", note="Мгновенный отклик, сверхлегкая архитектура"),
    "low": dict(width=320, layers=6, heads=5, kv_heads=5, block=384, drop=0.08,
                candidates=2, memory_slots=3, threads=6, name="GIGAMOGG Lite", note="Быстрые диалоги и базовые вычисления"),
    "mid": dict(width=448, layers=8, heads=7, kv_heads=7, block=512, drop=0.10,
                candidates=3, memory_slots=4, threads=8, name="GIGAMOGG Core", note="Оптимальный баланс глубины рассуждений"),
    "high": dict(width=640, layers=12, heads=8, kv_heads=4, block=768, drop=0.12,
                 candidates=4, memory_slots=6, threads=12, name="GIGAMOGG Pro", note="Углубленный анализ, программирование и логика"),
    "ultra": dict(width=768, layers=14, heads=8, kv_heads=4, block=768, drop=0.15,
                  candidates=6, memory_slots=8, threads=16, name="GIGAMOGG Ultra", note="Максимальная точность и комплексный синтез"),
    "brain30b": dict(width=768, layers=16, heads=12, kv_heads=4, block=1024, drop=0.10,
                     candidates=8, memory_slots=12, threads=32, name="GIGAMOGG Genesis", note="Эвристическая биоморфная сеть нового поколения"),
    "giga1b": dict(width=2048, layers=24, heads=16, kv_heads=8, block=2048, drop=0.10,
                   candidates=8, memory_slots=16, threads=48, name="GIGAMOGG", note="Флагманская автономная когнитивная архитектура"),
}

ORDER = ["superlow", "low", "mid", "high", "ultra", "brain30b", "giga1b"]
DEFAULT = "giga1b"

# грубая оценка веса модели в байтах на диске (float32 state_dict + адаптер обучения)
_BYTES_PER_PARAM = 4


def norm(name: str | None) -> str:
    """Приводит любое написание уровня к каноническому имени."""
    if not name:
        return DEFAULT
    key = str(name).strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    aliases = {
        "superlow": "superlow", "sl": "superlow", "tiny": "superlow", "micro": "superlow", "nano": "superlow",
        "low": "low", "small": "low", "s": "low", "lite": "low",
        "mid": "mid", "medium": "mid", "base": "mid", "m": "mid", "normal": "mid", "core": "mid",
        "high": "high", "large": "high", "h": "high", "pro": "high",
        "ultra": "ultra", "max": "ultra", "xl": "ultra", "u": "ultra",
        "brain30b": "brain30b", "30b": "brain30b", "brain": "brain30b", "human": "brain30b", "humanbrain": "brain30b", "genesis": "brain30b",
        "giga1b": "giga1b", "1b": "giga1b", "1000000000": "giga1b", "1g": "giga1b", "giga": "giga1b", "gigamogg1b": "giga1b", "apex": "giga1b",
    }
    return aliases.get(key, DEFAULT)


def spec(name: str | None) -> dict:
    return dict(SPECS[norm(name)])


def params(name: str | None) -> int:
    """Точное число параметров для конфигурации уровня (с учётом общих весов эмбеддинга)."""
    s = spec(name)
    v = s["width"]
    l, h, kh, b = s["layers"], s["heads"], s["kv_heads"], s["block"]
    emb = 256 * v  # словарь символов ~256
    attn = v * v + v * (kh * (v // h)) * 2 + v * v
    mlp = 3 * v * int(v * 8 / 3)
    n = emb + b * v + l * (attn + mlp + 4 * v) + v
    return int(n)


def weight_mb(name: str | None) -> float:
    return params(name) * _BYTES_PER_PARAM / 1e6


def catalog() -> list[dict]:
    """Список уровней для витрины на сайте."""
    out = []
    for i, k in enumerate(ORDER):
        s = SPECS[k]
        out.append(dict(
            id=k, index=i, name=s.get("name", k.upper()), note=s["note"],
            width=s["width"], layers=s["layers"], heads=s["heads"], kv_heads=s["kv_heads"],
            block=s["block"], candidates=s["candidates"], memory_slots=s["memory_slots"],
            threads=s["threads"],
            params=params(k), weight_mb=round(weight_mb(k), 1),
        ))
    return out


def pick_by_budget(capacity_mb: float) -> str:
    """Самый большой уровень, который влезает в память устройства."""
    best = ORDER[0]
    for k in ORDER:
        if params(k) * 3 * 4 / 1e6 < capacity_mb:  # x3 запас на активации и оптимизатор
            best = k
    return best


def device_capacity_mb() -> float:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / 2 ** 20
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return 12_000.0
    except Exception:
        pass
    try:
        total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 20
        return total * 0.5
    except Exception:
        return 8_000.0


def auto(name: str | None) -> str:
    """Если уровень не задан или назван auto — подбираем по железу."""
    if not name or str(name).strip().lower() in ("auto", "авто", ""):
        return pick_by_budget(device_capacity_mb())
    return norm(name)