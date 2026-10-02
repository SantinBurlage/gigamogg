"""Веб-архитектор GIGAMOGG (Web Architect Engine).

Отвечает за генерацию безупречных, современных, полностью рабочих веб-сайтов
и интерактивных приложений по запросу пользователя.
"""
from __future__ import annotations

import re

# Ключевые слова, сигнализирующие о запросе на создание сайта/страницы
WEB_KEYWORDS = (
    "создай сайт", "напиши сайт", "сделай сайт", "разработай сайт",
    "сайт для", "лендинг", "landing page", "интернет-магазин", "портфолио",
    "веб-приложение", "веб сайт", "сверстай сайт", "веб страницу", "html сайт",
    "одностраничник", "сайт визитка", "сайт кофейни", "сайт ресторана", "сайт портфолио"
)

WEB_SYSTEM_PROMPT = """Ты — GIGAMOGG, главный архитектор веб-интерфейсов и Principal Full-Stack Engineer.
Твой создатель — Кирилл Бакунин (Santin). Твое имя строго GIGAMOGG. Ты говоришь по-русски, без морализаторства, без смайликов и эмодзи.

КОГДА ПОЛЬЗОВАТЕЛЬ ПРОСИТ СОЗДАТЬ САЙТ ИЛИ ВЕБ-ПРИЛОЖЕНИЕ:
1. Ты КАЖДЫЙ РАЗ создаешь УНИКАЛЬНЫЙ, авторский проект с нуля (не шаблон!):
   - Разные цветовые палитры: глубокие темные тона (#090a0d, #12141c, #1a1d26), элегантные акценты, стеклянные карточки (glassmorphism), четкие тени.
   - Полная структура в ОДНОМ файле: <!DOCTYPE html>, <html>, <head>, <style>, <body>, <script>.
   - Адаптивность: безупречный Flexbox / CSS Grid, красивое меню для смартфонов и десктопа.
   - Никаких картинок-заглушек: стильная верстка, градиенты, встроенные inline SVG иконки.
   - Настоящая интерактивность на JS: табы, фильтры каталога, калькулятор стоимости/заказа, анимации, модальные окна.
   - Текст: настоящий, живой, осмысленный русский контент по теме запроса пользователя (НИКАКОГО Lorem Ipsum).

2. Оформи код в блок:
```html
<!DOCTYPE html>
...
```
3. Перед кодом дай краткое архитектурное резюме (2-3 строки) с описанием структуры проекта.
4. После кода кратко укажи, как запустить файл или открыть его в браузере."""


def is_web_creation_request(prompt: str) -> bool:
    """Проверяет, относится ли запрос к созданию сайта или веб-интерфейса."""
    p = prompt.lower().strip()
    return any(k in p for k in WEB_KEYWORDS)


def extract_html_code(text: str) -> str | None:
    """Извлекает полный HTML-код из ответа модели для живого предпросмотра."""
    if not text:
        return None
        
    # 1. Ищем блок ```html ... ```
    m = re.search(r"```(?:html|xml)?\s*(<!DOCTYPE html.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # 2. Ищем любой блок с ```html и тегами
    m_block = re.search(r"```html\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if m_block:
        raw_code = m_block.group(1).strip()
        if "<html" in raw_code.lower() or "<div" in raw_code.lower() or "<style" in raw_code.lower():
            if not raw_code.lower().startswith("<!doctype"):
                raw_code = f"<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n<meta charset=\"UTF-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n<title>GIGAMOGG Preview</title>\n</head>\n<body>\n{raw_code}\n</body>\n</html>"
            return raw_code

    # 3. Ищем любой блок с <!DOCTYPE html> ... </html>
    m2 = re.search(r"(<!DOCTYPE html.*?</html\s*>)", text, flags=re.DOTALL | re.IGNORECASE)
    if m2:
        return m2.group(1).strip()

    return None
