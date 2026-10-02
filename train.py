"""Обучение GIGAMOGG.

Особенности, которые важны на практике:
  * уровни: superlow … ultra, у каждого свой размер, батч и время;
  * продолжение с любого места — веса, оптимизатор, история шагов и прогресс;
  * гибридный режим: считает GPU, состояния оптимизатора живут в оперативной памяти;
  * защита от OOM: при нехватке памяти батч уменьшается сам, обучение не падает;
  * уроки с прошлых ошибок подмешиваются в корпус — это и есть обучение на ошибках;
  * кэш токенов на диске: повторный запуск не тратит время на разбор корпуса.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time

import numpy as np
import torch
import torch.nn as nn

from . import device as dev_mod
from . import tiers
from .corpus import build as build_corpus
from .lessons import Lessons
from .model import GigaGPT, estimate_params, oom_advice
from .tokenizer import END, Tokenizer

MODELS = "models"
CACHE = "cache"


# ------------------------------------------------------------------ пути
def paths(tier: str) -> dict:
    t = tiers.norm(tier)
    os.makedirs(MODELS, exist_ok=True)
    return dict(
        ckpt=os.path.join(MODELS, f"{t}.pt"),
        opt=os.path.join(MODELS, f"{t}.opt.pt"),
        hist=os.path.join(MODELS, f"{t}.json"),
        tok=os.path.join(MODELS, "tokenizer.json"),
        corpus="corpus.txt",
    )


def tokenizer_path() -> str:
    os.makedirs(MODELS, exist_ok=True)
    return os.path.join(MODELS, "tokenizer.json")


def have_tier(tier: str) -> bool:
    return os.path.exists(paths(tier)["ckpt"])


def available() -> list[str]:
    return [t for t in tiers.ORDER if have_tier(t)]


# ------------------------------------------------------------------ корпус и токены
def ensure_corpus(path: str = "corpus.txt", n_dialogues: int = 40000, force: bool = False,
                  verbose: bool = True) -> dict:
    lessons = Lessons()
    if force or not os.path.exists(path) or os.path.getsize(path) < 10_000:
        stats = build_corpus(path, n_dialogues=n_dialogues, verbose=verbose)
    else:
        size = os.path.getsize(path)
        stats = dict(path=path, chars=size, mb=round(size / 1e6, 2), cached=True)
    # свежие уроки всегда подмешиваются в конец корпуса
    with open(path, "a", encoding="utf-8") as f:
        text = lessons.to_text()
        if text:
            f.write("\n\n---\n\n" + text + "\n")
    return stats


def tokenize_corpus(text_path: str, tok: Tokenizer, verbose: bool = True) -> np.ndarray:
    """Токенизирует корпус в кэш, чтобы не делать это на каждом запуске."""
    os.makedirs(CACHE, exist_ok=True)
    stat = os.stat(text_path)
    key = hashlib.sha1(
        f"{os.path.abspath(text_path)}|{stat.st_size}|{int(stat.st_mtime)}|{tok.vocab_size}"
        f"|{len(tok.merges)}".encode()
    ).hexdigest()[:16]
    cache_file = os.path.join(CACHE, f"tokens_{key}.npy")
    if os.path.exists(cache_file):
        arr = np.load(cache_file, mmap_mode="r")
        if verbose:
            print(f"Токены из кэша: {len(arr):,}")
        return np.asarray(arr, dtype=np.int32)
    if verbose:
        print("Токенизирую корпус...")
    with open(text_path, encoding="utf-8") as f:
        text = f.read()
    ids = tok.encode(text)
    arr = np.asarray(ids, dtype=np.int32)
    np.save(cache_file, arr)
    if verbose:
        print(f"Токенов: {len(arr):,} (словарь {tok.vocab_size})")
    return arr


def ensure_tokenizer(text_path: str = "corpus.txt", vocab_size: int = 8192, verbose: bool = True) -> Tokenizer:
    path = tokenizer_path()
    if Tokenizer.exists(path):
        return Tokenizer.load(path)
    if not os.path.exists(text_path):
        ensure_corpus(text_path, verbose=verbose)
    tok = Tokenizer.build(path, text_path, vocab_size=vocab_size, verbose=verbose)
    return tok


# ------------------------------------------------------------------ конфиг обучения
def train_cfg(tier: str, plan) -> dict:
    t = tiers.norm(tier)
    s = tiers.spec(t)
    # Сбалансированные батчи под размер модели для мгновенного отклика и защиты от троттлинга
    batches = {
        "superlow": (16, 1),
        "low": (12, 1),
        "mid": (8, 2),
        "high": (4, 2),
        "ultra": (2, 2),
        "brain30b": (1, 2),
        "giga1b": (1, 4),
    }
    batch, acc = batches.get(t, (1, 2))
    lr = {  # крупной модели нужен меньший шаг
        "superlow": 1.2e-3, "low": 9e-4, "mid": 6e-4, "high": 4e-4, "ultra": 3.0e-4, "brain30b": 2.5e-4, "giga1b": 1.5e-4,
    }.get(t, 5e-4)
    return dict(tier=t, block=s["block"], width=s["width"], layers=s["layers"],
                heads=s["heads"], kv_heads=s["kv_heads"], drop=s["drop"],
                batch=batch, accum=acc, lr=lr, warmup=max(30, int(150 * s["layers"] / 8)),
                weight_decay=0.1, betas=(0.9, 0.95), clip=1.0,
                params=estimate_params(256, s["block"], s["layers"], s["heads"], s["kv_heads"], s["width"]))


def memory_plan(tier: str, plan) -> dict:
    """Сколько памяти нужно уровню и что делать, если её мало.

    Считаем грубо, но по делу: веса + градиенты + состояния AdamW + активации.
    Если не влезает в видеопамять, включаем чекпойнтинг (активации не хранятся)
    и переносим состояния оптимизатора в оперативную память — это и есть гибрид.
    """
    s = tiers.spec(tier)
    scale = s["width"] * s["layers"] * s["block"]
    weights = estimate_params(256, s["block"], s["layers"], s["heads"], s["kv_heads"], s["width"])
    base_mb = weights * 4 / 2 ** 20                    # сами веса в float32
    if plan.kind != "cuda":
        return dict(tier=tier, weights_mb=round(base_mb), need_mb=round(base_mb * 3),
                    hybrid=False, checkpointing=False, offload=False, fits=True)
    batch = train_cfg(tier, plan)["batch"]
    activations_mb = batch * scale * 2 / 2 ** 20       # активации под батч
    optim_mb = weights * 8 / 2 ** 20                   # два момента AdamW
    need = base_mb + weights * 4 / 2 ** 20 + optim_mb + activations_mb
    free = plan.vram_mb - 900                          # запас на фрагментацию и кэш

    hybrid = need > free
    offload = need > free
    checkpointing = need > free * 0.70 or offload
    if offload:
        need = base_mb + weights * 4 / 2 ** 20 + activations_mb * 0.3
    return dict(tier=tier, weights_mb=round(base_mb), need_mb=round(need), free_mb=round(free),
                hybrid=hybrid, checkpointing=checkpointing, offload=offload,
                fits=need <= free or offload)


def load_model(tier: str, map_location=None):
    p = paths(tier)
    if not os.path.exists(p["ckpt"]):
        raise FileNotFoundError(f"Модель уровня «{tiers.norm(tier)}» ещё не обучена.")
    ck = torch.load(p["ckpt"], map_location=map_location or "cpu", weights_only=False)
    cfg = ck["cfg"]
    model = GigaGPT(cfg["vocab"], cfg["block"], cfg["layers"], cfg["heads"],
                    cfg["kv_heads"], cfg["width"], cfg["drop"])
    model.load_state_dict(ck["model"])
    return model, cfg, ck.get("step", 0)


def read_history(tier: str) -> dict:
    p = paths(tier)["hist"]
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(train=[], val=[], step=0, samples=[], best=None)


def write_history(tier: str, hist: dict):
    with open(paths(tier)["hist"], "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False)


# ------------------------------------------------------------------ сам процесс
class Trainer:
    def __init__(self, tier: str = "mid", plan=None, corpus: str = "corpus.txt",
                 progress=None, verbose: bool = True, stop_event=None):
        self.tier = tiers.norm(tier)
        self.plan = plan or dev_mod.plan_for_tier(self.tier)
        self.plan = dev_mod.apply_backend(self.plan)
        self.corpus = corpus
        self.progress = progress or (lambda **kw: None)
        self.verbose = verbose
        self.stop = False
        self.stop_event = stop_event
        self.cfg = train_cfg(self.tier, self.plan)
        self.model = None
        self.hist = None

    def should_stop(self) -> bool:
        return bool(self.stop or (self.stop_event is not None and self.stop_event.is_set()))

    def say(self, **kw):
        self.progress(**kw)
        if self.verbose and kw.get("message"):
            print(kw["message"])

    # -------------------------------------------------------------- подготовка
    def prepare(self):
        if self.should_stop():
            return self
        plan = self.plan
        tok = ensure_tokenizer(self.corpus, verbose=self.verbose)
        if self.should_stop():
            return self
        data = tokenize_corpus(self.corpus, tok, verbose=self.verbose)
        if len(data) < self.cfg["block"] * 8:
            raise RuntimeError("Корпуса мало. Собери корпус заново (кнопка «Собрать корпус»).")

        if self.should_stop():
            return self

        cfg = dict(self.cfg)
        model = GigaGPT(tok.vocab_size, cfg["block"], cfg["layers"], cfg["heads"],
                        cfg["kv_heads"], cfg["width"], cfg["drop"],
                        grad_ckpt=plan.checkpointing).to(plan.device)
        step0 = 0
        hist = read_history(self.tier)

        p = paths(self.tier)
        if os.path.exists(p["ckpt"]):
            try:
                ck = torch.load(p["ckpt"], map_location=plan.device, weights_only=False)
                same = all(ck["cfg"].get(k) == cfg[k] for k in ("block", "layers", "heads", "width"))
                if same and ck["cfg"]["vocab"] == tok.vocab_size:
                    model.load_state_dict(ck["model"])
                    step0 = int(ck.get("step", 0))
                    self.say(message=f"Продолжаю с шага {step0:,}")
                elif same:
                    self.say(message="Словарь изменился — начинаю заново.")
            except Exception as e:
                self.say(message=f"Не удалось продолжить: {e}")

        self.model, self.hist, self.step0 = model, hist, step0
        self.tok, self.data = tok, data
        return self

    # -------------------------------------------------------------- один проход
    def fit(self, iters: int = 2000, save_every: int = 50, eval_every: int = 25):
        plan, cfg = self.plan, self.cfg
        model, data = self.model, self.data
        if model is None or data is None:
            return dict(step=0, best=None, seconds=0, tier=self.tier, steps_done=0, stopped=True)
        try:
            n = int(0.94 * len(data))
            tr = torch.from_numpy(np.asarray(data[:n], dtype=np.int64))
            va = torch.from_numpy(np.asarray(data[n:], dtype=np.int64))
            model.train()

            opt = dev_mod.make_optimizer(model, cfg["lr"], plan)
            scaler = dev_mod.make_scaler(plan)
            p = paths(self.tier)

            if os.path.exists(p["opt"]):
                try:
                    st = torch.load(p["opt"], map_location="cpu", weights_only=False)
                    if hasattr(opt, "load_state_dict"):
                        opt.load_state_dict(st)
                    elif isinstance(st, dict):
                        opt.load_state_dict(st)
                except Exception:
                    pass

            def sample_batch(src, block, batch):
                hi = max(1, len(src) - block - 1)
                starts = torch.randint(hi, (batch,))
                offs = torch.arange(block)
                idx = starts[:, None] + offs[None, :]
                x = src[idx].to(plan.device, non_blocking=True)
                y = src[idx + 1].to(plan.device, non_blocking=True)
                return x, y

            def lr_at(it: int) -> float:
                w = min(cfg["warmup"], max(5, iters // 10))
                if it < w:
                    return cfg["lr"] * (it + 1) / w
                prog = (it - w) / max(1, iters - w)
                return cfg["lr"] * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, max(0.0, prog)))))

            @torch.no_grad()
            def evaluate():
                model.eval()
                losses = []
                for _ in range(8):
                    if self.should_stop():
                        break
                    x, y = sample_batch(va, cfg["block"], min(cfg["batch"], 4))
                    with dev_mod.autocast(plan):
                        losses.append(float(model(x, y)[1]))
                model.train()
                return sum(losses) / max(1, len(losses))

            @torch.no_grad()
            def surprise(text_ids):
                """Собственная ошибка предсказания модели на её же тексте."""
                if len(text_ids) < 4:
                    return None
                x = torch.tensor([text_ids[-cfg["block"]:]], device=plan.device)
                model.eval()
                with dev_mod.autocast(plan):
                    _, loss = model(x[:, :-1], x[:, 1:])
                model.train()
                return math.exp(min(20.0, float(loss)))

            self.surprise = surprise

            # ------------------------------------------------------------------ цикл
            best = self.hist.get("best") or 9e9
            batch = cfg["batch"]
            t0 = time.time()
            done = 0
            self.say(status="training", message=f"Уровень {self.tier}: старт, батч {batch}, "
                                                f"устройство {plan.label}")

            for it in range(1, iters + 1):
                if self.should_stop():
                    break
                lr = lr_at(it)
                if hasattr(opt, "set_lr"):
                    opt.set_lr(lr)
                else:
                    for g in opt.param_groups:
                        g["lr"] = lr

                opt.zero_grad(set_to_none=True)
                total = 0.0
                ok = True
                for _ in range(cfg["accum"]):
                    if self.should_stop():
                        ok = False
                        break
                    x, y = sample_batch(tr, cfg["block"], batch)
                    try:
                        with dev_mod.autocast(plan):
                            loss = model(x, y)[1] / cfg["accum"]
                        if plan.kind == "cuda":
                            scaler.scale(loss).backward()
                        else:
                            loss.backward()
                        total += float(loss.detach())
                    except torch.cuda.OutOfMemoryError:
                        ok = False
                        dev_mod.empty_cache()
                        batch = max(1, batch // 2)
                        self.say(message=f"Не хватило видеопамяти — уменьшаю батч до {batch}")
                        break

                if self.should_stop():
                    break

                if not ok:
                    opt.zero_grad(set_to_none=True)
                    continue

                if plan.kind == "cuda":
                    scaler.unscale_(opt)
                nn.utils.clip_grad_norm_([q for q in model.parameters() if q.grad is not None], cfg["clip"])
                if plan.kind == "cuda":
                    scaler.step(opt)
                    scaler.update()
                else:
                    opt.step()

                done += 1
                step = self.step0 + it
                el = max(1e-6, time.time() - t0)
                self.say(step=step, loss=round(total, 4), lr=lr, batch=batch,
                         speed=round(it / el, 2), eta=round((iters - it) * el / it),
                         vram=round(dev_mod.vram_free_mb()))

                if it % save_every == 0 or it == iters:
                    self._save(model, opt, step)

                if it % eval_every == 0 or it == iters:
                    if self.should_stop():
                        break
                    v = evaluate()
                    self.hist["train"].append([step, round(total, 4)])
                    self.hist["val"].append([step, round(v, 4)])
                    self.hist["step"] = step
                    if v < best:
                        best = v
                        self.hist["best"] = v
                        self._save(model, opt, step, name="best")

                    text = ""
                    if not self.should_stop():
                        try:
                            ids = model.generate(torch.tensor([[1]], device=plan.device), 50,
                                                 temperature=0.85, top_k=40, top_p=0.92)[0].tolist()
                            text = self.tok.decode(ids).strip()
                        except Exception:
                            text = ""

                    self.hist.setdefault("samples", [])
                    self.hist["samples"] = (self.hist["samples"] + [dict(step=step, text=text[:800])])[-6:]
                    write_history(self.tier, self.hist)
                    self.say(val=round(v, 4), best=round(best, 4), sample=text[:300])
                    self.say(message=f"шаг {step:,} | ошибка {total:.3f} | проверка {v:.3f} | "
                                     f"{plan.label} | {round(it / el, 1)} шаг/с")

            stopped = self.should_stop()
            self.hist["step"] = self.step0 + done
            write_history(self.tier, self.hist)
            if not stopped:
                self._save(model, opt, self.hist["step"])
            return dict(step=self.hist["step"], best=best, seconds=round(time.time() - t0, 1),
                        tier=self.tier, steps_done=done, stopped=stopped)
        finally:
            if hasattr(self, "model") and self.model is not None:
                try:
                    self.model.to("cpu")
                except Exception:
                    pass
                del self.model
                self.model = None
            dev_mod.empty_cache()
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def _save(self, model, opt, step, name: str | None = None):
        p = paths(self.tier)
        target = p["ckpt"] if not name else os.path.join(MODELS, f"{self.tier}.{name}.pt")
        tmp = target + ".tmp"
        try:
            with open(tmp, "wb") as f:
                torch.save(dict(model=model.state_dict(), cfg=model.cfg, step=step,
                                tier=self.tier, saved=time.time()), f, _use_new_zipfile_serialization=False)
            if os.path.exists(target):
                try: os.remove(target)
                except Exception: pass
            os.replace(tmp, target)
        except Exception as e:
            try:
                torch.save(dict(model=model.state_dict(), cfg=model.cfg, step=step,
                                tier=self.tier, saved=time.time()), target)
            except Exception: pass
        try:
            if hasattr(opt, "state_dict"):
                opt_tmp = p["opt"] + ".tmp"
                with open(opt_tmp, "wb") as f:
                    torch.save(opt, f, _use_new_zipfile_serialization=False)
                if os.path.exists(p["opt"]):
                    try: os.remove(p["opt"])
                    except Exception: pass
                os.replace(opt_tmp, p["opt"])
        except Exception:
            pass


def train(tier: str = "mid", iters: int = 2000, progress=None, verbose: bool = True,
          plan=None, build: bool = True) -> dict:
    """Полный запуск: корпус -> словарь -> обучение. Возвращает итог."""
    if build:
        ensure_corpus(verbose=verbose)
    tr = Trainer(tier, plan=plan, progress=progress, verbose=verbose)
    if verbose:
        print(f"Уровень {tr.tier}: {tr.cfg['params'] / 1e6:.1f} млн параметров, "
              f"устройство {tr.plan.label}")
    tr.prepare()
    tr.progress(status="training", tier=tr.tier, params=tr.cfg["params"],
                device=tr.plan.as_dict())
    result = tr.fit(iters)
    tr.progress(status="done", message="Обучение завершено", **result)
    return result


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Обучение GIGAMOGG")
    ap.add_argument("tier", nargs="?", default="mid", choices=tiers.ORDER)
    ap.add_argument("--iters", type=int, default=2000)
    ap.add_argument("--device", default=None, help="cuda | hybrid | cpu | auto")
    ap.add_argument("--no-build", action="store_true", help="не пересобирать корпус")
    ap.add_argument("--vocab", type=int, default=8192)
    a = ap.parse_args()

    plan = dev_mod.detect(a.device)
    print(f"Устройство: {plan.label}")
    for w in plan.warnings:
        print("!", w)
    train(a.tier, a.iters, plan=plan, build=not a.no_build)