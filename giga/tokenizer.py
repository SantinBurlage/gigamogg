"""Байтовый BPE-токенизатор с маркерами ролей.

Своя реализация, без внешних зависимостей. Работает по байтам, поэтому
корректно переживает любую кириллицу, эмодзи и опечатки, а служебные
токены <|user|> / <|bot|> понимает как единое целое.
"""
from __future__ import annotations

import heapq
import json
import os
import re
from collections import Counter, defaultdict

PAD, BOS, USER, BOT, SYS, END = range(6)
SPECIALS = ["<pad>", "<|bos|>", "<|user|>", "<|bot|>", "<|sys|>", "<|end|>"]
SPECIAL_IDS = {s: i for i, s in enumerate(SPECIALS)}
_SPECIAL_RE = re.compile("(" + "|".join(re.escape(s) for s in SPECIALS) + ")")
_SPLIT = re.compile(r"[^\s]+|\s+")
OFFSET = len(SPECIALS)          # базовые байты начинаются после служебных


class Tokenizer:
    def __init__(self, merges: list[tuple[int, int]] | None = None, meta: dict | None = None):
        self.merges: list[tuple[int, int]] = merges or []
        self.meta = meta or {}
        self.ranks = {p: i for i, p in enumerate(self.merges)}
        self.merged = {i: OFFSET + 256 + i for i in range(len(self.merges))}
        self.vocab_size = OFFSET + 256 + len(self.merges)
        # Каждое слияние ссылается на более ранние, поэтому разворачиваем их
        # по порядку один раз: декодирование становится простым и быстрым.
        self.pieces: list[bytes] = [bytes([i]) for i in range(256)]
        for a, b in self.merges:
            self.pieces.append(self.pieces[a - OFFSET] + self.pieces[b - OFFSET])

    # ---------------------------------------------------------------- словарь
    @staticmethod
    def _bytes(chunk: str) -> tuple[int, ...]:
        return tuple(b + OFFSET for b in chunk.encode("utf-8"))

    def _bpe(self, ids: tuple[int, ...]) -> list[int]:
        out = list(ids)
        while len(out) >= 2:
            best_rank, best_i = None, -1
            for i in range(len(out) - 1):
                r = self.ranks.get((out[i], out[i + 1]))
                if r is not None and (best_rank is None or r < best_rank):
                    best_rank, best_i = r, i
            if best_i < 0:
                break
            out[best_i:best_i + 2] = [self.merged[best_rank]]
        return out

    def encode(self, text: str, allow_special: bool = True) -> list[int]:
        if not text:
            return []
        ids: list[int] = []
        if allow_special:
            parts = _SPECIAL_RE.split(text)
            for i, part in enumerate(parts):
                if not part:
                    continue
                if i % 2:                      # нечётные позиции — служебные токены
                    ids.append(SPECIAL_IDS[part])
                else:
                    ids.extend(self._encode_plain(part))
        else:
            ids = self._encode_plain(text)
        return ids

    def _encode_plain(self, text: str) -> list[int]:
        out: list[int] = []
        for chunk in _SPLIT.findall(text):
            out.extend(self._bpe(self._bytes(chunk)))
        return out

    def decode(self, ids, skip_special: bool = True) -> str:
        buf = bytearray()
        for i in ids:
            i = int(i)
            if i < OFFSET:
                if not skip_special:
                    buf.extend(SPECIALS[i].encode("utf-8"))
                continue
            if i < OFFSET + 256:
                buf.append(i - OFFSET)
            elif i - OFFSET < len(self.pieces):
                buf.extend(self.pieces[i - OFFSET])
        return buf.decode("utf-8", errors="replace")

    # ---------------------------------------------------------------- файлы
    def save(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"merges": [list(m) for m in self.merges], "meta": self.meta}, f)

    @classmethod
    def load(cls, path: str) -> "Tokenizer":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return cls([tuple(m) for m in d["merges"]], d.get("meta", {}))

    @classmethod
    def exists(cls, path: str) -> bool:
        return os.path.exists(path)

    @classmethod
    def build(cls, path: str, text_path: str | None = None, vocab_size: int = 8192,
              verbose: bool = True) -> "Tokenizer":
        """Удобная обёртка: обучить словарь и сразу сохранить на диск."""
        return build(path, text_path, vocab_size=vocab_size, verbose=verbose)


# -------------------------------------------------------------------- обучение
def train(text: str, vocab_size: int = 8192, max_chunks: int = 120_000, verbose: bool = False) -> Tokenizer:
    """Учит слияния на самых частых кусках текста.

    heapq + обратный индекс: каждая итерация трогает только затронутые слова,
    иначе обучение словаря на книгах шло бы часами.
    """
    target_merges = max(0, vocab_size - OFFSET - 256)
    counts = Counter(_SPLIT.findall(text))
    if len(counts) > max_chunks:
        counts = Counter(dict(counts.most_common(max_chunks)))

    words = [tuple(b + OFFSET for b in w.encode("utf-8")) for w in counts]
    freq = list(counts.values())

    where: dict[tuple[int, int], set[int]] = defaultdict(set)
    pair_count: Counter = Counter()
    for idx, w in enumerate(words):
        f = freq[idx]
        for p in zip(w, w[1:]):
            pair_count[p] += f
            where[p].add(idx)

    heap = [(-c, p) for p, c in pair_count.items()]
    heapq.heapify(heap)
    merges: list[tuple[int, int]] = []

    while heap and len(merges) < target_merges:
        neg, pair = heapq.heappop(heap)
        cur = pair_count.get(pair, 0)
        if cur <= 0:
            continue
        if -neg != cur:                        # устаревшая запись — обновляем и возвращаем
            heapq.heappush(heap, (-cur, pair))
            continue

        a, b = pair
        new_id = OFFSET + 256 + len(merges)
        merges.append(pair)

        for idx in list(where.pop(pair, ())):
            w, f = words[idx], freq[idx]
            if len(w) < 2:
                continue
            for p in set(zip(w, w[1:])):       # снимаем старые связи
                pair_count[p] -= f
                s = where.get(p)
                if s:
                    s.discard(idx)
            out, i = [], 0
            while i < len(w):
                if i < len(w) - 1 and w[i] == a and w[i + 1] == b:
                    out.append(new_id)
                    i += 2
                else:
                    out.append(w[i])
                    i += 1
            w = tuple(out)
            words[idx] = w
            for p in set(zip(w, w[1:])):       # новые связи
                pair_count[p] += f
                where[p].add(idx)
                heapq.heappush(heap, (-pair_count[p], p))

        if verbose and len(merges) % 1000 == 0:
            print(f"  слияний: {len(merges)} / {target_merges}")

    return Tokenizer(merges, meta=dict(vocab_size=OFFSET + 256 + len(merges), chunks=len(words)))


def build(path: str, text_path: str | None = None, vocab_size: int = 8192,
          sample_chars: int = 4_000_000, verbose: bool = True) -> Tokenizer:
    if text_path is None:
        text_path = os.path.join(os.path.dirname(os.path.abspath(path)), "corpus.txt")
    with open(text_path, encoding="utf-8") as f:
        text = f.read(sample_chars)
    if verbose:
        print(f"Учу словарь на {len(text):,} символах из {text_path}...")
    tok = train(text, vocab_size=vocab_size, verbose=verbose)
    tok.save(path)
    if verbose:
        print(f"Словарь готов: {tok.vocab_size} токенов -> {path}")
    return tok