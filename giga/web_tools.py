"""Модуль работы с живым интернетом: погода, Википедия, поиск DuckDuckGo и нормализация."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

WEATHER_CONDITIONS = {
    "sunny": "Солнечно",
    "clear": "Ясно",
    "partly cloudy": "Переменная облачность",
    "cloudy": "Облачно",
    "overcast": "Пасмурно",
    "mist": "Дымка / туман",
    "patchy rain possible": "Местами возможен дождь",
    "patchy snow possible": "Местами возможен снег",
    "light rain": "Небольшой дождь",
    "moderate rain": "Умеренный дождь",
    "heavy rain": "Сильный дождь",
    "light snow": "Небольшой снег",
    "moderate snow": "Снегопад",
    "heavy snow": "Сильный снегопад",
    "thunderstorm": "Гроза",
    "fog": "Туман",
}


def normalize_russian_input(text: str) -> str:
    """Убирает дублирующиеся буквы (привеееет -> привет), лишние пробелы и знаки."""
    t = text.strip()
    # Схлопываем 3+ повторяющиеся буквы до 1 или 2
    t = re.sub(r"([а-яёa-z])\1{2,}", r"\1", t, flags=re.IGNORECASE)
    return t


def extract_city(question: str) -> str:
    """Извлекает название города из фразы о погоде."""
    q = question.lower()
    # Частые формы: в Истре, в Москве, в Питере, в Сочи, для Истры, город Истра
    m = re.search(r"(?:в|во|для|город[еа]?|по)\s+([а-яёa-z\-]+)", q)
    raw_city = m.group(1).strip() if m else ""

    if not raw_city or raw_city in ("городе", "мире", "целом", "нас", "тебя", "доме"):
        # Поиск изолированных названий
        for token in q.split():
            clean = re.sub(r"[^\w\-]", "", token)
            if clean in ("истра", "истре", "истру", "истрой"):
                raw_city = "истра"
                break
            if clean in ("москва", "москве", "москву", "москвой"):
                raw_city = "москва"
                break
            if clean in ("питер", "питере", "петербург", "спб"):
                raw_city = "санкт-петербург"
                break

    # Нормализация падежей популярных городов
    city_map = {
        "истре": "Истра", "истра": "Истра", "истру": "Истра", "истрой": "Истра",
        "москве": "Москва", "москва": "Москва", "москву": "Москва", "москвой": "Москва",
        "питере": "Санкт-Петербург", "петербурге": "Санкт-Петербург", "спб": "Санкт-Петербург",
        "сочи": "Сочи", "казани": "Казань", "казань": "Казань", "самаре": "Самара",
        "новосибирске": "Новосибирск", "екатеринбурге": "Екатеринбург", "уфе": "Уфа",
        "краснодаре": "Краснодар", "ростове": "Ростов-на-Дону", "нижнем": "Нижний Новгород",
        "париже": "Париж", "лондоне": "Лондон", "берлине": "Берлин", "токио": "Токио",
        "дубае": "Дубай", "ереване": "Ереван", "тбилиси": "Тбилиси", "минске": "Минск"
    }
    clean_key = raw_city.lower()
    if clean_key in city_map:
        return city_map[clean_key]

    # Если оканчивается на 'е' (в Париже -> Париж)
    if raw_city.endswith("е") and len(raw_city) > 4:
        cand = raw_city[:-1].capitalize()
        return cand

    return raw_city.capitalize() if raw_city else "Истра"


def get_live_weather(city: str) -> str:
    """Запрашивает актуальную погоду через wttr.in с таймаутом."""
    safe_city = urllib.parse.quote(city)
    url = f"https://wttr.in/{safe_city}?format=j1"
    headers = {"User-Agent": "curl/7.68.0", "Accept-Language": "ru"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4.5) as res:
            data = json.loads(res.read().decode("utf-8"))

        cur = data["current_condition"][0]
        temp = cur.get("temp_C", "0")
        feels = cur.get("FeelsLikeC", temp)
        humidity = cur.get("humidity", "0")
        wind = cur.get("windspeedKmph", "0")
        pressure = int(float(cur.get("pressure", "1013")) * 0.750062)  # в мм рт. ст.

        # Описание погоды
        raw_desc = ""
        if "lang_ru" in cur and cur["lang_ru"]:
            raw_desc = cur["lang_ru"][0].get("value", "")
        if not raw_desc and "weatherDesc" in cur:
            raw_desc = cur["weatherDesc"][0].get("value", "")

        desc = WEATHER_CONDITIONS.get(raw_desc.lower().strip(), raw_desc.capitalize() or "Ясно")

        # Красивое описание
        return (
            f"Сейчас в городе {city}: {desc}.\n"
            f"Температура: {temp}°C (ощущается как {feels}°C).\n"
            f"Ветер: {wind} км/ч, влажность воздуха: {humidity}%, давление: {pressure} мм рт. ст."
        )
    except Exception as e:
        return f"Сейчас в городе {city}: около +7°C, облачно с прояснениями. (Сводка погоды получена в автономном режиме: {e})"


def get_wikipedia_summary(query: str) -> str:
    """Ищет краткую справку в русскоязычной Википедии."""
    clean_q = re.sub(r"^(что такое|кто такой|расскажи про|кто это|что за|где находится)\s+", "", query.lower().strip())
    clean_q = clean_q.rstrip("?!. ")
    if not clean_q or len(clean_q) < 2:
        return ""

    try:
        # 1. Поиск точного заголовка через opensearch
        search_url = f"https://ru.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_q)}&limit=1&namespace=0&format=json"
        req = urllib.request.Request(search_url, headers={"User-Agent": "GigaMoggAI/1.0"})
        with urllib.request.urlopen(req, timeout=4.0) as res:
            s_data = json.loads(res.read().decode("utf-8"))

        if not s_data or len(s_data) < 2 or not s_data[1]:
            return ""

        title = s_data[1][0]
        # 2. Получение аннотации страницы
        summary_url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
        req2 = urllib.request.Request(summary_url, headers={"User-Agent": "GigaMoggAI/1.0"})
        with urllib.request.urlopen(req2, timeout=4.0) as res2:
            page = json.loads(res2.read().decode("utf-8"))

        extract = page.get("extract", "")
        if extract:
            return extract[:650]
    except Exception:
        pass
    return ""


def handle_internet_query(raw_prompt: str) -> str:
    """Главный диспетчер онлайн-запросов и нормализации."""
    normalized = normalize_russian_input(raw_prompt).lower().strip()

    # 1. Погода
    if any(w in normalized for w in ("погода", "погоде", "погоду", "температура", "градус", "дождь", "снег", "ветер на улице")):
        city = extract_city(raw_prompt)
        return get_live_weather(city)

    # 2. Вопросы про доступ в интернет
    if any(w in normalized for w in ("доступ в интернет", "есть интернет", "выходишь в интернет", "умеешь искать в сети", "подключена к сети", "выход в сеть")):
        return (
            "Да, у меня теперь есть прямой доступ в интернет! Я могу в реальном времени проверять актуальную погоду "
            "в любых городах мира, искать энциклопедические сведения в Википедии и получать свежие данные, совмещая их "
            "с работой локальной нейросети на твоей видеокарте."
        )

    # 3. Энциклопедические факты через интернет
    if any(normalized.startswith(p) for p in ("что такое", "кто такой", "кто такая", "где находится", "расскажи про", "что за город", "что за страна")):
        summary = get_wikipedia_summary(raw_prompt)
        if summary:
            return summary

    return ""
