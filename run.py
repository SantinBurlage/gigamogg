"""GIGAMOGG — точка входа.

  python run.py                   запустить сайт
  python run.py train mid         обучить уровень
  python run.py train ultra --iters 4000
  python run.py check             проверить установку и железо
  python run.py devices           показать, что найдено: GPU, VRAM, гибрид
"""
import os
import sys

# Русский текст в консоли Windows: без этого печать падает с UnicodeEncodeError.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

from giga import tiers  # noqa: E402


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "serve"

    if cmd in ("app", "desktop", "окно"):
        from desktop_app import main as run_desktop
        run_desktop()
        return 0

    if cmd in ("build", "exe"):
        import build_exe
        return 0

    if cmd in ("serve", "сайт", ""):
        from giga import device as dev_mod
        # ──── гарантия GPU: проверяем и печатаем статус ────
        gpu = dev_mod.verify_gpu()
        if gpu["ok"]:
            print(f"✓ GPU: {gpu['name']} · {gpu['vram_gb']} ГБ VRAM · bf16={gpu['bf16']}")
            print(f"  CUDA {gpu['cuda_version']} · PyTorch {gpu['torch_version']}")
            print(f"  TF32: вкл · cudnn.benchmark: вкл · fused AdamW: вкл")
        elif gpu["problem"]:
            print(f"✗ GPU: {gpu['problem']}")
            if gpu["fix"]:
                print(f"  Исправление:\n  {gpu['fix']}")
        from giga.server import serve
        port = int(os.environ.get("PORT", os.environ.get("GIGAMOGG_PORT", 8000)))
        host = os.environ.get("HOST", os.environ.get("GIGAMOGG_HOST", "0.0.0.0"))
        serve(port=port, host=host)
        return 0

    if cmd in ("train", "обучение"):
        from giga import device as dev_mod
        from giga import train as train_mod
        tier = tiers.auto(argv[2] if len(argv) > 2 else None)
        iters = 2000
        dv = None
        if "--iters" in argv:
            iters = int(argv[argv.index("--iters") + 1])
        if "--device" in argv:
            dv = argv[argv.index("--device") + 1]
        plan = dev_mod.detect(dv)
        print(f"Устройство: {plan.label}")
        for w in plan.warnings:
            print("!", w)
        train_mod.train(tier, iters, plan=plan)
        return 0

    if cmd in ("check", "проверка"):
        from giga import device as dev_mod
        from giga import train as train_mod
        plan = dev_mod.detect()
        print(f"Устройство: {plan.label}")
        print(f"Видеопамять: {plan.vram_mb:.0f} МБ · оперативная: {plan.ram_mb:.0f} МБ")
        print(f"Точность: {str(plan.amp_dtype).replace('torch.', '')} · TF32: {plan.tf32} · "
              f"гибрид: {plan.hybrid}")
        for w in plan.warnings:
            print("!", w)
        print(f"Авто-уровень: {tiers.auto(None)}")
        for t in tiers.catalog():
            mark = "готов" if os.path.exists(train_mod.paths(t["id"])["ckpt"]) else "не обучен"
            print(f"  {t['id']:9s} {t['params'] / 1e6:7.1f} млн  ~{t['weight_mb']:6.1f} МБ  {mark}")
        return 0

    if cmd in ("devices", "gpu"):
        import torch
        print(f"torch {torch.__version__} · CUDA доступна: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                p = torch.cuda.get_device_properties(i)
                print(f"  [{i}] {p.name} · {p.total_memory / 2 ** 30:.1f} ГБ · "
                      f"compute {p.major}.{p.minor}")
            print(f"  bf16: {torch.cuda.is_bf16_supported()}")
        else:
            print("  Видеокарта не видна PyTorch. Поставь CUDA-сборку:")
            print("  pip uninstall -y torch torchvision torchaudio")
            print("  pip install torch --index-url https://download.pytorch.org/whl/cu128")
        return 0

    if cmd in ("corpus", "данные"):
        from giga.corpus import build
        n = int(argv[2]) if len(argv) > 2 else 40000
        build("corpus.txt", n)
        return 0

    if cmd in ("selftest", "тест"):
        from giga.selftest import run
        return run()

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))