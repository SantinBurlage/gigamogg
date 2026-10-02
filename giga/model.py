"""Архитектура GIGAMOGG: decoder-only трансформер.

Что внутри и зачем:
  RMSNorm         — стабильнее LayerNorm и дешевле
  RoPE            — позиции через поворот векторов, длина контекста задаётся гибко
  GQA             — на несколько голов запроса меньше голов ключа/значения: KV-кэш меньше
  SwiGLU          — MLP на три матрицы, заметно лучше обычного GELU на том же бюджете
  KV-кэш          — генерация не пересчитывает весь контекст заново
  Чекпойнтинг     — активации не хранятся, память экономится ради ultra
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint


class RMSNorm(nn.Module):
    def __init__(self, d: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d))

    def forward(self, x):
        dtype = x.dtype
        x = x.float()
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return (x * self.weight.float()).to(dtype)


class RoPE(nn.Module):
    """Кэширует повороты, чтобы не считать cos/sin на каждом шаге."""

    def __init__(self, head_dim: int, max_len: int = 4096, base: float = 10_000.0):
        super().__init__()
        inv = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
        self.register_buffer("inv_freq", inv, persistent=False)
        self._len = 0
        self._cos = None
        self._sin = None
        self.max_len = max_len

    def _build(self, n: int, device, dtype):
        t = torch.arange(n, device=device, dtype=torch.float32)
        f = torch.outer(t, self.inv_freq.to(device))     # n × (head_dim/2)
        self._cos = f.cos().to(dtype)[None, None]
        self._sin = f.sin().to(dtype)[None, None]
        self._len = n

    def rotate(self, x, offset: int = 0):
        """Поворот парами: чётный и нечётный элемент каждого вектора головы."""
        n = offset + x.size(-2)
        if self._cos is None or self._len < n or self._cos.device != x.device or self._cos.dtype != x.dtype:
            self._build(max(n, 64), x.device, x.dtype)
        cos = self._cos[..., offset:n, :]
        sin = self._sin[..., offset:n, :]
        x1, x2 = x[..., ::2], x[..., 1::2]
        out = torch.stack((x1 * cos - x2 * sin, x1 * sin + x2 * cos), dim=-1)
        return out.flatten(-2)


class Attention(nn.Module):
    def __init__(self, d: int, heads: int, kv_heads: int, drop: float):
        super().__init__()
        assert d % heads == 0, "ширина должна делиться на число голов"
        assert heads % kv_heads == 0, "головы запроса должны делиться на головы ключа"
        self.heads, self.kv_heads = heads, kv_heads
        self.head_dim = d // heads
        self.drop = drop
        self.q = nn.Linear(d, heads * self.head_dim, bias=False)
        self.k = nn.Linear(d, kv_heads * self.head_dim, bias=False)
        self.v = nn.Linear(d, kv_heads * self.head_dim, bias=False)
        self.o = nn.Linear(heads * self.head_dim, d, bias=False)
        self.rope = None  # подставляется моделью
        # Режим подсмотра: когда включён, внимание считается явно и сохраняет
        # карту «куда смотрит последний токен» плюс энтропию по каждой голове.
        # Нужен только для визуализации мыслей, на обучение не влияет.
        self.capture = False
        self.last_attn = None
        self.last_entropy = None

    def _split(self, t, n_heads):
        b, s, _ = t.shape
        return t.view(b, s, n_heads, self.head_dim).transpose(1, 2)

    def forward(self, x, past=None, use_cache: bool = False, offset: int = 0):
        B, T, _ = x.shape
        q = self._split(self.q(x), self.heads)
        k = self._split(self.k(x), self.kv_heads)
        v = self._split(self.v(x), self.kv_heads)

        q = self.rope.rotate(q, offset)
        k = self.rope.rotate(k, offset)

        if past is not None:
            pk, pv = past
            k = torch.cat((pk, k), dim=2)
            v = torch.cat((pv, v), dim=2)

        rep = self.heads // self.kv_heads
        if rep > 1:  # GQA: одни и те же ключи обслуживают несколько голов запроса
            k = k.repeat_interleave(rep, dim=1)
            v = v.repeat_interleave(rep, dim=1)

        past_len = k.size(2) - T
        causal = T > 1
        if self.capture and not self.training:
            scale = 1.0 / math.sqrt(self.head_dim)
            scores = torch.matmul(q, k.transpose(-1, -2)) * scale
            if causal and T > 1:
                mask = torch.ones(T, k.size(2), dtype=torch.bool, device=q.device).tril(k.size(2) - T)
                scores = scores.masked_fill(~mask, float("-inf"))
            alpha = F.softmax(scores.float(), dim=-1)              # B × головы × T × ключи
            self.last_attn = alpha[0, :, -1, :].detach().to("cpu")  # головы × ключи
            p = alpha.clamp_min(1e-9)
            self.last_entropy = (-(p * p.log()).sum(-1))[0, :, -1].detach().to("cpu")
            y = torch.matmul(alpha.to(q.dtype), v)
        else:
            y = F.scaled_dot_product_attention(
                q, k, v, is_causal=causal, dropout_p=self.drop if self.training else 0.0,
            )
        y = y.transpose(1, 2).contiguous().view(B, T, -1)
        return self.o(y), (k[:, ::rep], v[:, ::rep]) if use_cache else None


class SwiGLU(nn.Module):
    def __init__(self, d: int, hidden: int, drop: float):
        super().__init__()
        self.w1 = nn.Linear(d, hidden, bias=False)
        self.w3 = nn.Linear(d, hidden, bias=False)
        self.w2 = nn.Linear(hidden, d, bias=False)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        return self.drop(self.w2(F.silu(self.w1(x)) * self.w3(x)))


class Block(nn.Module):
    def __init__(self, d: int, heads: int, kv_heads: int, drop: float, grad_ckpt: bool = False):
        super().__init__()
        self.n1 = RMSNorm(d)
        self.attn = Attention(d, heads, kv_heads, drop)
        self.n2 = RMSNorm(d)
        hidden = int(8 * d / 3)
        hidden = 32 * ((hidden + 31) // 32)     # кратно 32 — быстрее на тензорных ядрах
        self.mlp = SwiGLU(d, hidden, drop)
        self.grad_ckpt = grad_ckpt

    def forward(self, x, past=None, use_cache: bool = False, offset: int = 0):
        if self.grad_ckpt and self.training:
            a, _ = checkpoint(lambda h: self.attn(self.n1(h), None, False, offset),
                              x, use_reentrant=False)
            x = x + a
            return x + checkpoint(lambda h: self.mlp(self.n2(h)), x, use_reentrant=False), None
        a, cache = self.attn(self.n1(x), past, use_cache, offset)
        x = x + a
        x = x + self.mlp(self.n2(x))
        return x, cache


class GigaGPT(nn.Module):
    def __init__(self, vocab: int, block: int, layers: int, heads: int, kv_heads: int,
                 width: int, drop: float = 0.1, grad_ckpt: bool = False, tie: bool = True):
        super().__init__()
        self.cfg = dict(vocab=vocab, block=block, layers=layers, heads=heads,
                        kv_heads=kv_heads, width=width, drop=drop, tie=tie)
        self.block, self.grad_ckpt = block, grad_ckpt
        self.capture = False
        self.last_energy = []
        self.last_logits = None
        self.tok = nn.Embedding(vocab, width)
        self.blocks = nn.ModuleList(Block(width, heads, kv_heads, drop, grad_ckpt) for _ in range(layers))
        self.norm = RMSNorm(width)
        self.head = nn.Linear(width, vocab, bias=False)
        self.rope = RoPE(width // heads, max_len=max(block, 4096) * 2)
        for blk in self.blocks:
            blk.attn.rope = self.rope
        if tie:
            self.head.weight = self.tok.weight
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0.0, 0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, 0.0, 0.02)

    def num_params(self, non_embedding: bool = False) -> int:
        n = sum(p.numel() for p in self.parameters())
        if non_embedding and not self.cfg["tie"]:
            n -= self.head.weight.numel()
        return n

    def forward(self, idx, targets=None):
        x = self.tok(idx)
        for blk in self.blocks:
            x, _ = blk(x)
        logits = self.head(self.norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.shape[-1]),
                                   targets.reshape(-1), ignore_index=-100)
        return logits, loss

    def forward_cache(self, idx, past=None, offset: int = 0, caches=None):
        """Шаг генерации: считает только новые токены, опираясь на KV-кэш."""
        x = self.tok(idx)
        new = []
        energy = []
        for i, blk in enumerate(self.blocks):
            p = past[i] if past is not None else None
            x, c = blk(x, p, True, offset)
            new.append(c)
            if self.capture:
                try:
                    energy.append(round(float(x.float().norm() / math.sqrt(x.shape[-1])), 3))
                except Exception:
                    energy.append(0.0)
        self.last_energy = energy
        logits = self.head(self.norm(x))
        self.last_logits = logits[:, -1].detach()
        return logits, new

    def set_capture(self, value: bool):
        """Включает подсмотр за внутренностями: внимание, энергия слоёв, энтропия."""
        self.capture = bool(value)
        for b in self.blocks:
            b.attn.capture = bool(value)
        return self

    def thought_snapshot(self, top_k: int = 6) -> dict:
        """Снимок того, что сейчас происходит внутри головы модели."""
        proposal = []
        if getattr(self, "last_logits", None) is not None:
            try:
                p = F.softmax(self.last_logits.float(), dim=-1)[0]
                v, i = torch.topk(p, top_k)
                proposal = [dict(token=int(t), weight=round(float(w), 4))
                            for w, t in zip(v.tolist(), i.tolist())]
            except Exception:
                proposal = []
        layers = []
        for i, b in enumerate(self.blocks):
            ent = b.attn.last_entropy
            a = b.attn.last_attn
            layers.append(dict(
                layer=i,
                focus=[round(float(x), 4) for x in (a.mean(0).tolist() if a is not None else [])][-64:],
                heads=([round(float(x), 3) for x in ent.tolist()] if ent is not None else []),
                sharpness=(round(float(1.0 / (1.0 + ent.mean())), 4) if ent is not None else None),
                energy=(self.last_energy[i] if i < len(getattr(self, "last_energy", [])) else None),
            ))
        return dict(layers=layers, proposal=proposal,
                    sharpness=round(float(sum(l["sharpness"] for l in layers if l["sharpness"]) /
                                          max(1, sum(1 for l in layers if l["sharpness"]))), 4)
                    if any(l["sharpness"] for l in layers) else None)

    @torch.no_grad()
    def generate(self, idx, n: int, temperature: float = 0.85, top_k: int = 40, top_p: float = 0.95,
                 repetition_penalty: float = 1.0, stop_ids=None, seed: int | None = None,
                 use_cache: bool = True, on_step=None):
        """Потокобезопасно для одного вызова: свой генератор случайных чисел.

        on_step(k, ids) вызывается на каждом новом токене — через него пишется
        поток мыслей: к этому моменту внимание и энергия слоёв уже посчитаны.
        """
        gen = None
        if seed is not None:
            gen = torch.Generator(device=idx.device)
            gen.manual_seed(int(seed) & 0x7FFFFFFF)
        was_training = self.training
        self.eval()
        prompt_len = idx.size(1)
        out = idx
        past = None
        offset = 0

        if use_cache:
            ctx = idx[:, -self.block:]
            logits, past = self.forward_cache(ctx, None, 0)
            offset = ctx.size(1)
            logits = logits[:, -1]
        else:
            logits = self(idx[:, -self.block:])[0][:, -1]

        if on_step:
            try:
                on_step(0, [int(t) for t in out[0].tolist()])
            except Exception:
                pass

        produced = []
        for _ in range(n):
            step = logits.float() / max(temperature, 1e-4)

            if repetition_penalty and repetition_penalty != 1.0 and produced:
                for t in set(produced[-64:]):
                    step[0, t] /= repetition_penalty

            if top_k:
                k = min(top_k, step.size(-1))
                v, _ = torch.topk(step, k)
                step[step < v[:, [-1]]] = -float("inf")

            if top_p and top_p < 1.0:
                srt, order = torch.sort(step, descending=True)
                probs = F.softmax(srt, dim=-1).cumsum(-1)
                cut = probs > top_p
                cut[..., 1:] = cut[..., :-1].clone()
                cut[..., 0] = False
                srt[cut] = -float("inf")
                step = torch.empty_like(step).scatter_(1, order, srt)

            probs = F.softmax(step, dim=-1)
            if gen is None:
                nxt = torch.multinomial(probs, 1)
            else:
                nxt = torch.multinomial(probs, 1, generator=gen)

            produced.append(int(nxt))
            if stop_ids and int(nxt) in stop_ids:
                break

            out = torch.cat((out, nxt), dim=1)
            if use_cache:
                if offset >= self.block:      # контекст переполнен — начинаем окно заново
                    ctx = out[:, -self.block:]
                    logits, past = self.forward_cache(ctx, None, 0)
                    offset = ctx.size(1)
                else:
                    logits, past = self.forward_cache(nxt, past, offset)
                    offset += 1
                logits = logits[:, -1]
            else:
                logits = self(out[:, -self.block:])[0][:, -1]

            if on_step:
                try:
                    on_step(len(produced), [int(t) for t in out[0].tolist()])
                except Exception:
                    pass

        if was_training:
            self.train()
        if prompt_len and out.size(1) > prompt_len:
            return out[:, prompt_len:]
        return out

    def loss_on(self, idx, targets):
        """Считает ошибку на одном примере — нужно для проверки и для уроков."""
        _, loss = self(idx, targets)
        return loss

    @property
    def kv_heads(self):
        return self.cfg["kv_heads"]


def estimate_params(vocab: int, block: int, layers: int, heads: int, kv_heads: int, width: int) -> int:
    hidden = 32 * ((int(8 * width / 3) + 31) // 32)
    emb = vocab * width + block * width
    attn = width * (heads * (width // heads)) + 2 * width * (kv_heads * (width // heads)) + width * width
    mlp = 3 * width * hidden
    return emb + layers * (attn + mlp + 4 * width) + width


def oom_advice(name: str, plan) -> str:
    return (f"Не хватило памяти для уровня «{name}» на {plan.label}. "
            "Возьми уровень ниже или запусти с GIGAMOGG_DEVICE=hybrid " 
            "(оптимизатор уедет в оперативную память, обучение пойдёт заметно медленнее, но не упадёт).")


def grad_norm_(params):
    return nn.utils.clip_grad_norm_([p for p in params if p.grad is not None], 1.0)