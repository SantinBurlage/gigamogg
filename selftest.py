"""Самопроверка: прогоняет весь путь целиком на настоящем железе.

Что проверяется:
  железо -> корпус -> словарь -> обучение -> ответ -> критик -> нити -> мысли -> уроки.

Запуск:  python run.py selftest
Работает в отдельной папке _selftest, твои модели и нити не трогает.
"""
from __future__ import annotations

import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ok(name: str, extra: str = ""):
    print(f"  [ок] {name}{(' — ' + extra) if extra else ''}")


def fail(name: str, extra: str = ""):
    print(f"  [!!] {name}{(' — ' + extra) if extra else ''}")
    return 1


def run() -> int:
    work = os.path.join(BASE, "_selftest")
    if os.path.exists(work):
        shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    os.chdir(work)          # все пути внутри giga считаются от рабочей папки

    problems = 0
    from giga import device as dev_mod
    from giga import tiers
    from giga import train as train_mod
    from giga import critic, corpus
    from giga.tokenizer import Tokenizer
    from giga.thoughts import STREAM
    from giga.engine import Engine

    print("GIGAMOGG · самопроверка\n")

    # 1. железо
    print("1) Железо")
    plan = dev_mod.detect()
    print(f"   {plan.label} · VRAM {plan.vram_mb:.0f} МБ · точность "
          f"{str(plan.amp_dtype).replace('torch.', '')} · гибрид {plan.hybrid}")
    if plan.kind != "cuda":
        print("   ! Работаем без видеокарты — это медленнее, но проверка продолжится.")
    ok("устройство выбрано", plan.label)

    # 2. корпус
    print("\n2) Корпус")
    t0 = time.time()
    stats = corpus.build("corpus.txt", n_dialogues=800, books=False, verbose=False)
    with open("corpus.txt", encoding="utf-8") as f:
        text = f.read()
    ok("корпус собран", f"{stats['mb']} МБ, {stats['blocks']} блоков, {time.time() - t0:.1f} с")
    if "слушай" in text.lower():
        problems += fail("в корпусе осталось слово-паразит «слушай»")
    else:
        ok("без паразитных зачинов")
    for need in ("Человек:", "GIGAMOGG:", "<|sys|>"):
        if need not in text:
            problems += fail(f"в корпусе нет {need}")
    else:
        ok("формат диалогов и самокоррекции на месте")

    # 3. словарь
    print("\n3) Словарь")
    t0 = time.time()
    tok = Tokenizer.build("models/tokenizer.json", "corpus.txt", vocab_size=1200, verbose=False)
    back = tok.decode(tok.encode("Привет! Как дела — проверка ёлки ⏎"))
    ok("BPE обучен", f"{tok.vocab_size} токенов за {time.time() - t0:.1f} с")
    if "ёлки" not in back or "Привет" not in back:
        problems += fail("кодирование/декодирование теряет текст", back[:60])
    else:
        ok("кириллица переживает round-trip")

    # 4. обучение
    print("\n4) Обучение (уровень superlow)")
    t0 = time.time()
    tr = train_mod.Trainer("superlow", plan=plan, verbose=False)
    tr.prepare()
    params = sum(p.numel() for p in tr.model.parameters())
    result = tr.fit(iters=60, save_every=30, eval_every=30)
    ok("модель обучена", f"{params / 1e6:.2f} млн параметров, 60 шагов за {time.time() - t0:.1f} с")
    if os.path.exists(train_mod.paths("superlow")["ckpt"]):
        ok("чекпойнт сохранён")
    else:
        problems += fail("чекпойнт не сохранён")

    # 5. ответ + критик
    print("\n5) Разговор")
    Engine.threads_path = "threads.json"
    eng = Engine("threads.json", "lessons.json")
    res = eng.ask("привет, как тебя зовут?", tier="superlow", capture=True)
    answer = res["answer"]
    ok("получен ответ", repr(answer[:70]))
    print(f"   оценка критика: {res['critique']['score']} · вердикт: {res['critique']['verdict']} · "
          f"веток: {len(res.get('candidates', []))}")
    if not answer.strip():
        problems += fail("пустой ответ")
    if res["critique"]["score"] > 0:
        ok("критик оценил ответ")

    res2 = eng.ask("сколько будет 6 умножить на 7", tier="superlow", capture=False)
    ok("арифметический вопрос задан", repr(res2["answer"][:60]))
    report = critic.score("сколько будет 6 умножить на 7", "6 * 7 = 48. Ответ: 48.")
    if report["issues"] and "арифметика" in report["issues"][0]:
        ok("критик ловит неверную арифметику")
    else:
        problems += fail("критик не поймал 6*7=48", str(report))
    if critic.correct_answer("сколько будет 6 умножить на 7", "48") == "6 * 7 = 42. Ответ: 42.":
        ok("критик знает правильный ответ")

    # 6. нити
    print("\n6) Нити")
    stats_threads = eng.store.stats()
    ok("нити создаются", f"{stats_threads['count']} нитей, {stats_threads['turns']} реплик")
    if stats_threads["turns"] < 4:
        problems += fail("в нитях слишком мало реплик", str(stats_threads))
    path = "threads.json"
    eng.store.save(force=True)
    again = eng.store.__class__(path)
    if again.stats()["count"] == stats_threads["count"]:
        ok("нити переживают перезапуск", "файл читается заново")
    else:
        problems += fail("нити не сохранились на диск")
    eng.store.relink()
    graph = eng.store.graph()
    ok("карта связей строится", f"{len(graph['nodes'])} узлов, {len(graph['edges'])} связей")

    # 7. мысли
    print("\n7) Поток мыслей")
    frames = STREAM.snapshot()["frames"]
    if frames:
        f = frames[-1]
        ok("кадры внутренностей пишутся", f"{len(frames)} кадров, слоёв {len(f['layers'])}, "
                                          f"слов-мыслей {len(f['contour'])}")
        has_attn = any(any(n["gain"] > 0 for n in L["nodes"]) for L in f["layers"])
        if has_attn:
            ok("веса внимания читаются с живой модели")
        else:
            problems += fail("внимание пустое — визуализация была бы декоративной")
    else:
        problems += fail("поток мыслей пуст")
    print(f"   настроение: {STREAM.mood_report()['mood']} · "
          f"{STREAM.mood_report()['note']}")

    # 8. уроки
    print("\n8) Уроки из ошибок")
    lesson = eng.lessons.record("сколько будет 6 умножить на 7", "6 * 7 = 48. Ответ: 48.",
                                critic.score("сколько будет 6 умножить на 7", "6 * 7 = 48. Ответ: 48."))
    if lesson:
        ok("промах записан в урок", f"{lesson['id']}: {lesson['issues'][:2]}")
    else:
        problems += fail("урок не записался")
    text = eng.lessons.to_text()
    if "<|sys|>замечание" in text and "42" in text:
        ok("урок превратился в обучающий пример с исправлением")
    else:
        problems += fail("обучающий текст урока неправильный", text[:120])
    check = eng.self_check("superlow", limit=4)
    ok("проверка себя работает", f"спрошено {check['checked']}, выучено {check['fixed']}, "
                                 f"осталось {check['left']}")

    # 9. уровни
    print("\n9) Уровни")
    for t in tiers.catalog():
        ready = os.path.exists(train_mod.paths(t["id"])["ckpt"])
        print(f"   {t['id']:9s} {t['params'] / 1e6:7.1f} млн  ~{t['weight_mb']:6.1f} МБ  "
              f"контекст {t['block']:5d}  веток {t['candidates']}  "
              f"{'обучен' if ready else 'не обучен'}")
    ok("каталог уровней строится", f"авто-выбор для этого железа: {tiers.auto(None)}")

    print("\n" + ("Проблемы найдены: " + str(problems) if problems else "Всё работает."))
    print(f"Рабочая папка проверки: {work}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(run())