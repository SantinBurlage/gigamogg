"""Выбор железа и гибридный режим GPU + CPU.

Правила простые:
  1) есть CUDA — считаем на видеокарте, всегда;
  2) несколько видеокарт — раскидываем модель по ним;
  3) не хватает VRAM — включаем гибрид: считает GPU, состояния оптимизатора
     и обновление весов живут в оперативной памяти (offload), плюс
     gradient checkpointing, чтобы не держать активации;
  4) CUDA нет вообще — CPU со всеми ядрами и bf16, без падений.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import torch

# приоритет видеокарты: быстрые ядра, TF32 и «математика на максимум»
if os.name != "nt":      # expandable_segments есть только на Linux
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")


@dataclass
class Plan:
    device: torch.device = field(default_factory=lambda: torch.device("cpu"))
    name: str = "CPU"
    kind: str = "cpu"                 # cuda | mps | cpu
    vram_mb: float = 0.0
    ram_mb: float = 0.0
    gpus: int = 0
    amp: bool = False
    amp_dtype: torch.dtype = torch.float32
    tf32: bool = False
    hybrid: bool = False              # GPU + CPU одновременно
    offload_optimizer: bool = False
    checkpointing: bool = False
    channels_last: bool = False
    parallel: bool = False
    threads: int = 0
    warnings: list = field(default_factory=list)

    @property
    def label(self) -> str:
        extra = []
        if self.gpus > 1:
            extra.append(f"{self.gpus} GPU")
        if self.hybrid:
            extra.append("гибрид GPU+CPU")
        if self.checkpointing:
            extra.append("чекпойнтинг")
        tail = f" · {', '.join(extra)}" if extra else ""
        return f"{self.name}{tail}"

    def as_dict(self) -> dict:
        return dict(name=self.name, kind=self.kind, label=self.label, vram_mb=round(self.vram_mb),
                    ram_mb=round(self.ram_mb), gpus=self.gpus, amp=self.amp, tf32=self.tf32,
                    hybrid=self.hybrid, offload=self.offload_optimizer,
                    checkpointing=self.checkpointing, threads=self.threads,
                    dtype=str(self.amp_dtype).replace("torch.", ""), warnings=self.warnings)


def ram_mb() -> float:
    try:
        if hasattr(os, "sysconf"):
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 20
    except Exception:
        pass
    try:
        import ctypes

        class MemStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        m = MemStatus()
        m.dwLength = ctypes.sizeof(MemStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullTotalPhys / 2 ** 20
    except Exception:
        return 8_000.0


def verify_gpu() -> dict:
    """Проверяет GPU и выдаёт детальный отчёт. Вызывается при старте."""
    report = dict(
        available=False, name="", vram_gb=0, cuda_version=None,
        torch_version=torch.__version__, bf16=False, ok=False,
        problem="", fix=""
    )
    report["cuda_version"] = torch.version.cuda

    if torch.cuda.is_available():
        report["available"] = True
        report["ok"] = True
        try:
            props = torch.cuda.get_device_properties(0)
            report["name"] = props.name
            report["vram_gb"] = round(props.total_memory / 2 ** 30, 1)
            report["bf16"] = torch.cuda.is_bf16_supported()
            # Проверяем, что GPU реально работает (не просто доступна)
            torch.zeros(1, device="cuda")
        except Exception as e:
            report["ok"] = False
            report["problem"] = f"GPU найдена, но тест провалился: {e}"
    elif report["cuda_version"] is None:
        report["problem"] = (
            f"Установлен PyTorch {torch.__version__} только для CPU. "
            f"Видеокарта не видна — нужна CUDA-сборка PyTorch."
        )
        report["fix"] = (
            "pip uninstall -y torch torchvision torchaudio\n"
            "pip install torch --index-url https://download.pytorch.org/whl/cu128"
        )
    else:
        report["problem"] = (
            f"PyTorch {torch.__version__} с CUDA {report['cuda_version']} установлен, "
            f"но видеокарта не найдена. Обнови драйвер NVIDIA и перезагрузи ПК."
        )
        report["fix"] = "nvidia-smi"
    return report


def detect(force: str | None = None) -> Plan:
    """Собирает план работы. force: 'cuda' | 'hybrid' | 'cpu' | None (авто)."""
    force = (force or os.environ.get("GIGAMOGG_DEVICE", "auto")).strip().lower()
    plan = Plan(ram_mb=ram_mb())
    plan.threads = os.cpu_count() or 4

    if force == "cpu":
        return _finish_cpu(plan)

    if torch.cuda.is_available():
        try:
            plan.gpus = torch.cuda.device_count()
            props = torch.cuda.get_device_properties(0)
            plan.vram_mb = props.total_memory / 2 ** 20
            plan.name = props.name
            plan.device = torch.device("cuda:0")
            plan.kind = "cuda"
            # Проверяем, что GPU реально работает
            torch.zeros(1, device="cuda")
        except Exception as e:
            plan.warnings.append(f"Видеокарта найдена, но недоступна: {e}")
            return _finish_cpu(plan)

        bf16 = False
        try:
            bf16 = torch.cuda.is_bf16_supported()
        except Exception:
            pass
        plan.amp = True
        plan.amp_dtype = torch.bfloat16 if bf16 else torch.float16
        plan.tf32 = True
        plan.channels_last = True
        plan.parallel = plan.gpus > 1

        # Гибрид включаем заранее: модели уровня high/ultra почти всегда
        # упираются в VRAM, а так они просто работают, а не падают с OOM.
        small = plan.vram_mb < 8_000
        if force == "hybrid" or small:
            plan.hybrid = True
            plan.offload_optimizer = True
            plan.checkpointing = True
        if force == "hybrid":
            plan.hybrid = True
            plan.offload_optimizer = True
            plan.checkpointing = True
        return plan

    # Apple Silicon
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        plan.device = torch.device("mps")
        plan.kind = "mps"
        plan.name = "Apple GPU (MPS)"
        plan.vram_mb = min(plan.ram_mb * 0.7, 24_000)
        plan.amp = True
        plan.amp_dtype = torch.float16
        plan.hybrid = True          # у MPS нет pinned memory, часть работы уходит на CPU
        plan.offload_optimizer = True
        return plan

    plan.warnings.append(
        "CUDA не найдена. Скорее всего стоит CPU-сборка PyTorch. Ставим GPU-сборку так:\n"
        "  pip uninstall -y torch torchvision torchaudio\n"
        "  pip install torch --index-url https://download.pytorch.org/whl/cu128"
    )
    return _finish_cpu(plan)


def _finish_cpu(plan: Plan) -> Plan:
    plan.device = torch.device("cpu")
    plan.kind = "cpu"
    plan.name = f"CPU · {plan.threads} ядер"
    try:
        torch.set_num_threads(plan.threads)
    except Exception:
        pass
    try:  # на CPU bf16 быстрее fp32 и вдвое экономнее по памяти
        plan.amp_dtype = torch.bfloat16
    except Exception:
        plan.amp_dtype = torch.float32
    return plan


def plan_for_tier(name: str, force: str | None = None) -> Plan:
    """План работы с учётом уровня: крупной модели автоматически даём гибрид.

    Без этого ultra на 8 ГБ просто падал бы с OutOfMemory посреди обучения.
    """
    plan = detect(force)
    if plan.kind != "cuda" or force in ("cpu", "hybrid"):
        return plan
    try:
        from .train import memory_plan
        need = memory_plan(name, plan)
    except Exception:
        return plan
    if need.get("offload"):
        plan.offload_optimizer = True
        plan.hybrid = True
        plan.checkpointing = True
        plan.warnings.append(
            f"Уровень «{name}» просит ~{need['need_mb']} МБ видеопамяти, а свободно "
            f"~{need['free_mb']} МБ. Включаю гибридный режим: считает видеокарта, "
            f"состояния оптимизатора живут в оперативной памяти."
        )
    elif need.get("checkpointing") and not plan.checkpointing:
        plan.checkpointing = True
    return plan


def apply_backend(plan: Plan, model=None):
    """Включает быстрые пути вычислений. Вызывается один раз после выбора плана."""
    if plan.kind == "cuda":
        try:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            torch.set_float32_matmul_precision("high")
        except Exception:
            pass
    if plan.kind == "cpu":
        try:
            torch.set_num_threads(plan.threads)
        except Exception:
            pass
    if model is not None and plan.channels_last:
        try:
            model.to(memory_format=torch.channels_last)
        except Exception:
            pass
    return plan


class CpuOffloadAdamW:
    """AdamW, у которого состояния моментов живут в оперативной памяти.

    Экономит на GPU примерно 8 байт на параметр — для ultra это несколько
    гигабайт. Градиенты перегоняются на CPU маленькими копиями, веса
    обновляются на месте, поэтому видеокарта остаётся занята только счётом.
    """

    def __init__(self, params, lr=3e-4, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.1,
                 pin=False):
        self.params = [p for p in params if p.requires_grad]
        self.lr, self.betas, self.eps, self.wd = lr, betas, eps, weight_decay
        self.pin = False  # Отключаем pinned memory на Windows во избежание DefaultCPUAllocator out of memory
        self.state = {}
        self.t = 0
        for i, p in enumerate(self.params):
            self.state[i] = dict(
                exp_avg=torch.zeros_like(p, device="cpu"),
                exp_avg_sq=torch.zeros_like(p, device="cpu"),
            )

    def zero_grad(self, set_to_none: bool = True):
        for p in self.params:
            if p.grad is not None:
                if set_to_none:
                    p.grad = None
                else:
                    p.grad.detach_().zero_()

    @torch.no_grad()
    def step(self):
        self.t += 1
        b1, b2 = self.betas
        bc1 = 1 - b1 ** self.t
        bc2 = 1 - b2 ** self.t
        for i, p in enumerate(self.params):
            g = p.grad
            if g is None:
                continue
            s = self.state[i]
            gc = s["exp_avg"].copy_(g.detach().to("cpu", non_blocking=False))
            gs = s["exp_avg_sq"].copy_(g.detach().pow(2).to("cpu", non_blocking=False))
            s["exp_avg"].mul_(b1).add_(gc, alpha=1 - b1)
            s["exp_avg_sq"].mul_(b2).add_(gs, alpha=1 - b2)
            m = s["exp_avg"] / bc1
            v = s["exp_avg_sq"] / bc2
            upd = m / (v.sqrt().add_(self.eps))
            if self.wd:
                upd.add_(p.detach().to("cpu", non_blocking=False), alpha=self.wd)
            p.add_(upd.to(p.device, non_blocking=False).view_as(p), alpha=-self.lr)
            p.grad = None

    def state_dict(self):
        return dict(t=self.t, state={k: {kk: vv for kk, vv in v.items()} for k, v in self.state.items()})

    def load_state_dict(self, d):
        self.t = int(d.get("t", 0))
        for k, v in d.get("state", {}).items():
            if int(k) in self.state:
                for kk, vv in v.items():
                    self.state[int(k)][kk].copy_(vv)

    def param_groups(self):
        return [{"lr": self.lr}]

    def set_lr(self, lr: float):
        self.lr = lr


def make_optimizer(model, lr: float, plan: Plan, weight_decay: float = 0.1):
    """AdamW: fused на CUDA без гибрида, CPU-offload в гибриде (если VRAM < 3.5 ГБ), обычный на CPU."""
    decay = [p for n, p in model.named_parameters() if p.requires_grad and p.dim() >= 2]
    no_decay = [p for n, p in model.named_parameters() if p.requires_grad and p.dim() < 2]
    groups = [{"params": decay, "weight_decay": weight_decay},
              {"params": no_decay, "weight_decay": 0.0}]

    if plan.kind == "cuda" and plan.offload_optimizer and plan.vram_mb < 3500:
        return CpuOffloadAdamW(decay + no_decay, lr=lr, weight_decay=weight_decay, pin=False)
    if plan.kind == "cuda":
        try:
            return torch.optim.AdamW(groups, lr=lr, betas=(0.9, 0.95), eps=1e-8, fused=True)
        except (TypeError, RuntimeError):
            pass
    return torch.optim.AdamW(groups, lr=lr, betas=(0.9, 0.95), eps=1e-8)


def make_scaler(plan: Plan):
    on = plan.amp and plan.amp_dtype == torch.float16
    return torch.amp.GradScaler("cuda" if plan.kind == "cuda" else "cpu", enabled=on)


def autocast(plan: Plan, enabled: bool | None = None):
    use = plan.amp if enabled is None else enabled
    device = "cuda" if plan.kind == "cuda" else ("cpu" if plan.kind == "cpu" else "mps")
    return torch.autocast(device, dtype=plan.amp_dtype, enabled=use)


def autocast_dtype(plan: Plan):
    return plan.amp_dtype if plan.amp else torch.float32


def vram_free_mb() -> float:
    if not torch.cuda.is_available():
        return 0.0
    try:
        free, _total = torch.cuda.mem_get_info()
        return free / 2 ** 20
    except Exception:
        return 0.0


def empty_cache():
    import gc
    gc.collect()
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass