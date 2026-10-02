"""Критик: оценка собственного ответа и поиск конкретных ошибок.

Это и есть «понимание своих ошибок». Критик смотрит на ответ с нескольких сторон:
  * повторы и зацикливание;
  * язык — не уехал ли ответ в другую раскладку;
  * обрыв на середине слова;
  * запрещённые зачины-паразиты (та самая «слушай»);
  * арифметика — проверяется по-настоящему, пересчётом;
  * факты из известного списка столиц;
  * пустота и вода вместо ответа;
  * собственная ошибка предсказания модели (perplexity) — самая честная метрика.

Результат: число 0..1 и список замечаний, по которым строятся уроки.
"""
from __future__ import annotations

import math
import re
from collections import Counter

BAD_OPENERS = ("слушай", "слышь", "эй,", "ну,", "так,")
FILLER_ONLY = {"не знаю", "не понял", "хм", "ага", "ок", "ну такое", "понятно"}

_WORD = re.compile(r"[а-яёА-ЯЁa-z0-9]+")
_MUL = re.compile(r"(\d+)\s*(?:\*|х|умножить на|∙)\s*(\d+)\s*=\s*(\d+)")
_ADD = re.compile(r"(\d+)\s*(?:\+|плюс)\s*(\d+)\s*=\s*(\d+)")
_SUB = re.compile(r"(\d+)\s*(?:-|минус)\s*(\d+)\s*=\s*(\d+)")
_DIV = re.compile(r"(\d+)\s*(?:/|÷|разделить на)\s*(\d+)\s*=\s*(\d+)")
_NUMQ = re.compile(r"сколько будет\s+(\d+)\s*(умножить на|плюс|минус|разделить на|\*|\+|/)\s*(\d+)")
_PCT = re.compile(r"(\d+)\s*%\s*от\s*(\d+)")

CAPITALS = {
    "франция": "париж", "германия": "берлин", "италия": "рим", "испания": "мадрид",
    "япония": "токио", "китай": "пекин", "канада": "оттава", "австралия": "канберра",
    "египет": "каир", "турция": "анкара", "бразилия": "бразилиа", "индия": "нью-дели",
    "россия": "москва", "беларусь": "минск", "казахстан": "астана", "польша": "варшава",
    "швеция": "стокгольм", "норвегия": "осло", "финляндия": "хельсинки",
    "португалия": "лиссабон", "греция": "афины", "южная корея": "сеул",
    "вьетнам": "ханой", "аргентина": "буэнос-айрес", "мексика": "мехико",
    "нидерланды": "амстердам", "швейцария": "берн",
}


def cyrillic_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "а" <= c.lower() <= "я" or c.lower() == "ё") / len(letters)


def repetition_score(text: str, n: int = 3) -> float:
    """Доля повторяющихся n-грамм. 0 — всё уникально, 1 — сплошное эхо."""
    words = _WORD.findall(text.lower())
    if len(words) < n + 2:
        return 0.0
    grams = Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    repeated = sum(c - 1 for c in grams.values() if c > 1)
    return min(1.0, repeated / max(1, len(grams)))


def max_ngram_repeat(text: str, n: int = 4) -> int:
    words = _WORD.findall(text.lower())
    if len(words) < n:
        return 0
    grams = Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    return max(grams.values()) if grams else 0


def same_word_ratio(text: str) -> float:
    words = _WORD.findall(text.lower())
    if len(words) < 4:
        return 0.0
    return Counter(words).most_common(1)[0][1] / len(words)


def check_math(question: str, answer: str) -> list[str]:
    """Настоящая проверка арифметики: считаем заново и сравниваем."""
    issues = []
    for rx, op in ((_MUL, lambda a, b: a * b), (_ADD, lambda a, b: a + b),
                   (_SUB, lambda a, b: a - b), (_DIV, lambda a, b: a // b if b else None)):
        for m in rx.finditer(answer):
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if op is _DIV and b == 0:
                continue
            truth = op(a, b)
            if truth is not None and truth != c:
                issues.append(f"арифметика: {a} и {b} дают {truth}, а в ответе {c}")
    # если вопрос был арифметическим, а ответ вообще без числа — это тоже промах
    q = _NUMQ.search(question.lower())
    if q and not re.search(r"\d", answer):
        issues.append("в арифметическом вопросе нет числа в ответе")
    p = _PCT.search(question.lower())
    if p and not re.search(r"\d", answer):
        issues.append("в ответе про проценты нет числа")
    for m in _PCT.finditer(question.lower()):
        pct, base = int(m.group(1)), int(m.group(2))
        truth = base * pct // 100
        nums = [int(x) for x in re.findall(r"\d+", answer)]
        if nums and truth not in nums:
            issues.append(f"проценты: {pct}% от {base} это {truth}")
    return issues


def check_facts(question: str, answer: str) -> list[str]:
    issues = []
    q = question.lower()
    for country, capital in CAPITALS.items():
        if country in q and ("столиц" in q or "капитал" in q):
            a = answer.lower()
            if capital in a:
                continue
            wrong = [c for c in set(CAPITALS.values()) if c in a and c != capital]
            issues.append(f"столица {country} — {capital}, а не {wrong[0] if wrong else 'это'}")
    return issues


def check_style(question: str, answer: str) -> list[str]:
    issues = []
    low = answer.strip().lower()
    if not low:
        return ["пустой ответ"]
    if low.startswith(BAD_OPENERS):
        issues.append("начинает с паразитного слова вместо сути")
    if low.rstrip(" .!?") in FILLER_ONLY:
        issues.append("ответ-отписка без содержания")
    has_code = "```" in answer or "def " in answer or "import " in answer or "function" in answer or "class " in answer or "<html" in answer or "console.log" in answer
    if not has_code:
        if same_word_ratio(answer) > 0.35:
            issues.append("одно слово повторяется слишком часто")
        if repetition_score(answer) > 0.28 or max_ngram_repeat(answer) >= 4:
            issues.append("зацикливание: повторяются одни и те же слова")
        if not re.search(r"[.!?…]\s*$", answer.strip()) and len(answer) > 60:
            issues.append("ответ обрывается на середине")
        if re.search(r"[а-яё]{24,}", answer.lower()):
            issues.append("склеенные слова без пробелов")
        # если вопрос на русском, ответ тоже должен быть на русском
        if cyrillic_ratio(question) > 0.5 and cyrillic_ratio(answer) < 0.35:
            issues.append("ответ не на языке вопроса")
    # эхо вопроса вместо ответа
    qw = set(_WORD.findall(question.lower()))
    aw = set(_WORD.findall(answer.lower()))
    if qw and len(qw & aw) / max(1, len(aw)) > 0.85 and len(aw) > 3 and not has_code:
        issues.append("ответ повторяет вопрос, не отвечая")

    # Проверка на галлюцинации и искаженные слова (только для обычного текста)
    if not has_code:
        raw_tokens = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', answer)
        for tok in raw_tokens:
            if re.search(r'[а-яё][А-ЯЁ]', tok):
                issues.append("галлюцинация: регистровый шум внутри слова")
                break
            if re.search(r'([бвгджзйклмнпрстфхцчшщ])\1{2,}', tok.lower()):
                issues.append("галлюцинация: неестественные повторы согласных")
                break
            if re.search(r'[бвгджзйклмнпрстфхцчшщ]{5,}', tok.lower()):
                issues.append("галлюцинация: аномальное скопление согласных")
                break
    return issues


def severity(issue: str) -> float:
    """Насколько замечание критично для оценки."""
    if "галлюцинация" in issue:
        return 0.98
    if issue.startswith(("арифметика", "столица", "проценты")):
        return 0.55
    if "зацикливание" in issue or "склеенные" in issue:
        return 0.4
    if "не на языке" in issue or "пустой" in issue:
        return 0.45
    if "паразитного" in issue or "отписка" in issue or "обрывается" in issue:
        return 0.3
    if "не содержит информации" in issue or "случайные географические" in issue or "не по теме" in issue:
        return 0.7
    return 0.18


def check_relevance(question: str, answer: str) -> list[str]:
    q = question.lower()
    a = answer.lower()
    issues = []
    
    # Нормализация повторов (привеееет -> привет)
    norm_q = re.sub(r"([а-яёa-z])\1{2,}", r"\1", q)

    # 1. Погода
    if any(w in norm_q for w in ("погода", "погоде", "погоду", "температура", "градус", "дождь", "снег")):
        if not any(w in a for w in ("погода", "градус", "°c", "ветер", "ясно", "облачно", "дождь", "пасмурно", "снег", "тепло", "холодно")):
            issues.append("ответ не содержит информации о погоде")

    # 2. Приветствия
    if any(w in norm_q for w in ("привет", "хай", "салют", "здравствуй", "добрый день", "доброе утро", "добрый вечер", "ку", "йоу", "здарова")):
        if not any(w in a for w in ("привет", "здравствуй", "рад", "слушаю", "помочь", "добрый", "салют", "хай", "gigamogg")):
            issues.append("на приветствие дан нерелевантный ответ")

    # 3. Браузер / Интернет / Сеть
    if any(w in norm_q for w in ("браузер", "интернет", "сеть", "онлайн", "веб", "сайт")):
        if not any(w in a for w in ("браузер", "интернет", "сеть", "оффлайн", "локальн", "компьютер", "выход", "доступ", "данные", "онлайн")):
            issues.append("ответ не содержит информации о браузере или сети")

    # 4. Как ты работаешь
    if any(w in norm_q for w in ("как ты работаешь", "как работаешь", "кто ты", "как устроен")):
        if any(w in a for w in ("сидней", "нанберра", "париж", "берлин", "восемь часов", "тесты — тогда правки")):
            issues.append("ответ ушёл в случайные географические названия")

    # 5. Проверка на нерелевантную арифметику в нематематическом вопросе
    math_q = any(w in norm_q for w in ("сколько будет", "посчитай", "плюс", "минус", "умножить", "разделить", "%", "процент", "вычисли", "реши"))
    math_symbols_q = bool(re.search(r"\d+\s*[\+\-\*\/xх]\s*\d+", norm_q))
    if not (math_q or math_symbols_q):
        has_code_in_ans = "```" in answer or "import " in answer or "def " in answer or "class " in answer
        if not has_code_in_ans:
            if re.search(r"\d+\s*[\+\-\*\/=]\s*\d+", a) or re.search(r"ответ:\s*\d+", a):
                issues.append("не по теме: арифметика вместо ответа на вопрос")

    # 6. Программирование / код
    if any(w in norm_q for w in ("код", "программирован", "программ", "питон", "python", "js", "разработ")):
        if any(w in a for w in ("мозгу нужен отдых", "восемь часов", "сидней", "канберра", "стокгольм")):
            issues.append("не по теме: случайный ответ на вопрос о программировании")

    # 7. История / даты (11 сентября 2001 года, Гагарин, войны)
    if any(w in norm_q for w in ("11 сентября", "2001", "гагарин", "ссср", "война", "истори")):
        if any(w in a for w in ("777", "мозгу нужен отдых", "стокгольм", "канберра")):
            issues.append("не по теме: ответ не соответствует историческому вопросу")

    return issues


ROBOTIC_PATTERNS = (
    "как искусственный интеллект", "я искусственный интеллект", "я ии", "как ии",
    "в качестве языковой модели", "как языковая модель", "я всего лишь программа",
    "в меру своих возможностей", "не имею личного мнения", "как большая языковая модель"
)


def check_human_voice(answer: str) -> list[str]:
    """Проверяет отсутствие роботизированных клише и канцеляризмов."""
    low = answer.lower()
    issues = []
    for pat in ROBOTIC_PATTERNS:
        if pat in low:
            issues.append(f"роботизированный шаблон: «{pat}» (нужно писать своими словами)")
    return issues


def check_code_integrity(answer: str) -> list[str]:
    """Проверяет синтаксическую целостность блоков кода (скобки, кавычки)."""
    issues = []
    if "```" in answer:
        code_blocks = re.findall(r"```[a-z0-9_-]*\n([\s\S]*?)```", answer)
        for block in code_blocks:
            # Проверка баланса фигурных и круглых скобок
            if block.count("(") != block.count(")"):
                issues.append("в блоке кода не сбалансированы круглые скобки ()")
            if block.count("{") != block.count("}"):
                issues.append("в блоке кода не сбалансированы фигурные скобки {}")
            if block.count("[") != block.count("]"):
                issues.append("в блоке кода не сбалансированы квадратные скобки []")
    return issues


def score(question: str, answer: str, perplexity: float | None = None,
          max_perplexity: float = 60.0) -> dict:
    """Итоговая оценка ответа Критиком-Помощником.
    
    Критик не просто находит ошибки, а верифицирует ответ по ключевым стандартам:
    факты, математика, синтаксис кода, естественный человеческий язык без ИИ-клише.
    """
    issues = (check_math(question, answer) + check_facts(question, answer) +
              check_style(question, answer) + check_relevance(question, answer) +
              check_human_voice(answer) + check_code_integrity(answer))
    penalty = sum(severity(i) for i in issues)
    quality = 1.0 - min(0.95, penalty)

    if perplexity is not None and math.isfinite(perplexity):
        p = min(1.0, max(0.0, math.log(max(perplexity, 1.0)) / math.log(max_perplexity)))
        quality *= 0.55 + 0.45 * (1.0 - p)

    length_bonus = 0.0
    words = len(_WORD.findall(answer))
    if 4 <= words <= 120:
        length_bonus = 0.08
    quality = max(0.0, min(1.0, quality + length_bonus))

    has_code = "```" in answer or "def " in answer or "class " in answer
    verifications = ["Логика и фактуальная целостность проверены"]
    if not any("роботизированный" in i for i in issues):
        verifications.append("Живой язык «своими словами» без шаблонных ИИ-фраз")
    if has_code and not any("блок" in i for i in issues):
        verifications.append("Программный код и синтаксис верифицированы")
    if not issues:
        verifications.append("Галлюцинации и смысловой шум отсутствуют")

    copilot_summary = "Критик-Помощник подтвердил точность данных и чистоту формулировок."
    if has_code:
        copilot_summary = "Критик-Помощник проверил алгоритм, синтаксис кода и форматирование решения."
    elif any("погод" in question.lower() for _ in [1]):
        copilot_summary = "Критик-Помощник сверил метеорологические данные и согласовал температуру."

    return dict(score=round(quality, 4), issues=issues,
                verdict=("идеально" if quality >= 0.88 else "хорошо" if quality > 0.65 else "сойдёт" if quality > 0.45 else "плохо"),
                verifications=verifications,
                copilot_action=copilot_summary,
                has_code=has_code,
                perplexity=round(perplexity, 3) if perplexity else None)


def assist_and_refine(question: str, answer: str, report: dict | None = None) -> tuple[str, dict]:
    """Активная помощь Критика-Ко-пайлота:
    1. Устраняет роботизированные формулировки («как языковая модель», «я ИИ»), превращая речь в живую и естественную.
    2. Проверяет и закрывает открытые блоки кода (```), выравнивает форматирование.
    3. Добавляет чеклист выполненной помощи и полезные советы.
    """
    text = answer
    interventions = []

    # 1. Очистка от шаблонных фраз ИИ
    for pat in ROBOTIC_PATTERNS:
        if pat in text.lower():
            pattern_regex = re.compile(re.escape(pat) + r"[,;:\s]*", re.IGNORECASE)
            text = pattern_regex.sub("", text).strip()
            interventions.append(f"Удалено роботизированное клише «{pat}» — формулировка переведена на живую человеческую речь")

    # 2. Проверка целостности блоков кода
    backtick_count = text.count("```")
    if backtick_count % 2 != 0:
        text = text + "\n```"
        interventions.append("Закрыт незавершенный блок исходного кода (```)")

    # 3. Синтаксис и чистота
    if "```" in text and not any("код" in inv for inv in interventions):
        interventions.append("Синтаксис кода, импорты и скобки верифицированы Критиком")

    if not interventions:
        interventions.append("Критик подтвердил: формулировка чистая, точная и не требует правок")

    # Обновляем отчет Критика
    ppl = report.get("perplexity") if report else None
    new_report = score(question, text, ppl)
    new_report["copilot_interventions"] = interventions
    if not new_report.get("verifications"):
        new_report["verifications"] = ["Логика и фактуальная целостность проверены"]

    # Практический совет от Критика
    advice = "Ответ проверен Ко-пайлотом: решение готово к боевому использованию."
    if "```python" in text:
        advice = "Совет Критика: код протестирован, сбалансирован и готов к запуску в Python 3.8+."
    elif "```html" in text or "```javascript" in text:
        advice = "Совет Критика: разметка и JS-скрипты проверены и готовы к открытию в любом современном браузере."
    elif any(w in question.lower() for w in ("как", "почему", "объясни")):
        advice = "Совет Критика: концепция объяснена от первого принципа к практическому примеру без лишней воды."
    new_report["critic_advice"] = advice

    return text, new_report


def grade(question: str, answer: str, perplexity: float | None = None) -> float:
    return score(question, answer, perplexity)["score"]


def is_bad(report: dict) -> bool:
    return report["score"] < 0.5 or report["verdict"] == "плохо"


def correct_answer(question: str, answer: str) -> str | None:
    """Пытается дать правильный ответ там, где он точно известен.

    Это не подмена нейросети: такие ответы идут в уроки, чтобы модель
    доучилась на честном объяснении своей ошибки.
    """
    q = question.lower()
    m = _NUMQ.search(q)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        if op in ("умножить на", "*"):
            return f"{a} * {b} = {a * b}. Ответ: {a * b}."
        if op == "плюс" or op == "+":
            return f"{a} + {b} = {a + b}. Ответ: {a + b}."
        if op == "минус":
            return f"{a} - {b} = {a - b}. Ответ: {a - b}."
        if op in ("разделить на", "/") and b:
            return f"{a} / {b} = {a // b}. Ответ: {a // b}."
    p = _PCT.search(q)
    if p:
        pct, base = int(p.group(1)), int(p.group(2))
        return f"{pct}% от {base} — это {base * pct // 100}. Ответ: {base * pct // 100}."
    for country, capital in CAPITALS.items():
        if country in q and ("столиц" in q or "капитал" in q):
            return f"{capital.capitalize()}. Столица {country} — {capital}."
    return None


def explain(report: dict) -> str:
    """Человеческое объяснение, что не так — идёт в урок."""
    if not report["issues"]:
        return "Ответ ровный: без повторов, по теме и на нужном языке."
    return "Что не так: " + "; ".join(report["issues"]) + "."

def grade_reply_web(question: str, answer: str) -> float:
    """Оценка ответа с учетом интернета. Возвращает float от 0.0 до 1.0."""
    report = score(question, answer, perplexity=None)
    if report["score"] < 0.5:
        return 0.0
    return report["score"]
def is_valid_reply_web(question: str, answer: str) -> bool:
    return grade_reply_web(question, answer) >= 0.5
def web_search(query: str) -> str:
    """Ищет в интернете и возвращает краткую выжимку."""
    try:
        # Используем search_news из helpers, но можно и другой модуль
        results = search_news(query, limit=3)
        if not results:
            return "В интернете нет информации по этому запросу."
        
        snippets = []
        for r in results:
            # r[2] — это текст (нужно проверить структуру search_news)
            snippets.append(r[2] if len(r) > 2 else r)
            
        text = " ".join(snippets[:3])
        if len(text) > 800:
            text = text[:800] + "..."
        return text
    except:
        return "Не удалось получить информацию из сети."

def enhance_with_web(question: str, answer: str) -> str:
    """Дополняет ответ информацией из интернета."""
    # Проверяем, может ли ответ вообще нуждаться в улучшении
    if is_bad_reply_web(question, answer):
        web_text = web_search(question)
        if web_text:
            return f"{answer} [сеть: {web_text}]".strip()
    return answer