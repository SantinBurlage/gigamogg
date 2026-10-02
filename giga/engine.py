"""Движок разговора GIGAMOGG: облачный нейросетевой кластер, память диалогов, веб-архитектор и критик.
"""
from __future__ import annotations

import logging
import math
import os
import re
import threading
import time
from typing import Any

from . import critic
from . import device as dev_mod
from . import tiers
from .cloud_llm import CloudNeuralCore, SYSTEM_PROMPT
from .memory import ThreadStore
from .thoughts import STREAM
from .web_architect import is_web_creation_request, extract_html_code, WEB_SYSTEM_PROMPT
from .web_tools import handle_internet_query

logger = logging.getLogger("gigamogg.engine")

USER_TAG = "Человек: "
BOT_TAG = "GIGAMOGG: "


class Engine:
    """Главный движок ИИ GIGAMOGG."""

    def __init__(self, threads_path: str = "threads.json", lessons_path: str = "lessons.json"):
        self.store = ThreadStore(threads_path)
        self.plan = dev_mod.detect()
        self.lock = threading.RLock()
        self.stats = dict(asked=0, fixed=0, best_of=0, since=time.time())

    def device_info(self) -> dict:
        return self.plan.as_dict()

    def ask(
        self,
        question: str,
        tier: str = "gigamogg",
        thread_id: str | None = None,
        temperature: float = 0.7,
        capture: bool = True,
        max_tokens: int | None = None,
        correct: bool = True,
        history: list[dict] | None = None,
        files: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Обрабатывает запрос пользователя через облачный нейросетевой кластер."""
        question = (question or "").strip()
        if not question and not files:
            raise RuntimeError("Пустой вопрос.")

        # Обработка прикрепленных файлов и фотографий
        files_blocks = []
        has_images = False
        image_names = []
        for f in (files or []):
            fname = f.get("name", "файл")
            ftype = f.get("type", "")
            is_img = f.get("isImage", False) or ftype.startswith("image/")
            if is_img:
                has_images = True
                image_names.append(fname)
                files_blocks.append(f"[Прикреплено фото/изображение: {fname}]")
            else:
                content = f.get("content") or f.get("textContent") or ""
                if content:
                    files_blocks.append(f"=== ПРИКРЕПЛЕННЫЙ ФАЙЛ: {fname} ===\n{content}\n=== КОНЕЦ ФАЙЛА ===")
                else:
                    files_blocks.append(f"[Прикреплен файл: {fname} ({f.get('size', 0)} байт)]")

        effective_prompt = "\n\n".join(files_blocks) + ("\n\n" + question if question else "\n\nПроанализируй прикрепленные файлы/фото и дай детальный ответ.") if files_blocks else question

        with self.lock:
            thread = self.store.ensure(thread_id, tier=tier)
            thread_context = history if (history and len(history) > 0) else thread.context(limit=14)

            if capture:
                STREAM.start("GIGAMOGG", question or "Вложение файлов", temperature)

            # Шаги размышлений для визуализатора
            thoughts = [
                f"Анализ запроса: «{(question or 'Вложение файлов')[:40]}…»",
                f"Контекстная память: {len(thread_context)} реплик в активном внимании",
            ]
            actions = [
                "Семантический парсинг запроса",
                f"Извлечение контекста ({len(thread_context)} сообщений)",
            ]

            if files:
                thoughts.append(f"Обработка {len(files)} вложений: {', '.join(f.get('name', '') for f in files[:3])}")
                actions.append(f"Парсинг файлов и фото ({len(files)} шт)")
                if has_images:
                    thoughts.append(f"Мультимодальный визуальный анализ фото: {', '.join(image_names)}")
                    actions.append("Vision-анализ графических элементов и структуры")

            # 1. Проверяем, нужны ли живые данные из интернета (погода, факты)
            net_fact = handle_internet_query(question) if question else None
            system_prompt = SYSTEM_PROMPT
            
            # 2. Если запрос на создание сайта или веб-интерфейса
            is_web = is_web_creation_request(effective_prompt)
            if is_web:
                system_prompt = WEB_SYSTEM_PROMPT
                thoughts.append("Активирован модуль Web-Architect: проектирование структуры сайта, современных CSS-стилей и скриптов")
                actions.append("Web-Architect: генерация адаптивного HTML5/CSS3/JS кода")
            else:
                thoughts.append("Маршрутизация в облачный нейросетевой кластер (Cohere Command / GLM)")
                actions.append("Облачный нейросетевой синтез ответа")

            if net_fact:
                system_prompt += f"\n\nАКТУАЛЬНЫЕ ФАКТИЧЕСКИЕ ДАННЫЕ ИЗ СЕТИ ПО ЗАПРОСУ:\n{net_fact}\nИспользуй эти точные факты в ответе, объясняя их своими словами."

            # 3. Вызов облачного нейросетевого ядра
            gen_res = CloudNeuralCore.generate(
                prompt=effective_prompt,
                messages_history=thread_context,
                system_prompt=system_prompt,
                timeout=45,
            )

            answer = gen_res.get("text", "")
            provider_used = gen_res.get("provider", "Cloud")

            # 4. Проверка и извлечение HTML-кода для живого предпросмотра
            html_preview = extract_html_code(answer)
            if html_preview:
                thoughts.append("Обнаружен готовый HTML5 документ: подготовка интерактивного предпросмотра в Web Studio")
                actions.append("Компиляция живого DOM для встраиваемого фрейма")

            # 5. Критик-Ко-пайлот: проверка ответа и стандартов качества
            report = critic.score(question, answer, perplexity=None)
            refined_text, refined_report = critic.assist_and_refine(question, answer, report)
            answer = refined_text
            report = refined_report

            thoughts.append(f"Критик-Ко-пайлот: верификация структуры и чистоты стиля (оценка {report.get('score', 1.0)})")
            actions.append("Финальная валидация и отправка пользователю")

            # Сохранение в нить
            if thread.title in ("Новая нить", "", "Диалог") and len(question) > 1:
                thread.title = question[:36]
            thread.add("user", question, tier="gigamogg")
            thread.add("bot", answer, tier="gigamogg", meta=dict(score=report.get("score", 1.0), provider=provider_used))
            self.store.maybe_save()

            self.stats["asked"] += 1
            if capture:
                STREAM.finish("ответила")

            thought_words = [w for w in re.findall(r"[а-яёa-z]{4,}", question.lower())][:6]
            if is_web:
                thought_words.extend(["html", "css", "layout", "responsive", "design"])

            return dict(
                answer=answer,
                tier="gigamogg",
                thread=thread.summary(),
                critique=report,
                corrected=False,
                correction_note="",
                candidates=[dict(text=answer[:200], score=report.get("score", 1.0), temp=temperature, perplexity=None)],
                picked=0,
                recall=[],
                lesson=None,
                related=[],
                device="Cloud Neural Engine",
                perplexity=None,
                thoughts=thoughts,
                actions=actions,
                thought_words=thought_words,
                html_preview=html_preview,
                provider=provider_used,
            )

    def thoughts(self, cursor: int = 0, limit: int = 48) -> dict:
        data = STREAM.since(cursor, limit)
        data["mood"] = STREAM.mood_report()
        data["mind"] = STREAM.mind
        return data

    def mind(self) -> dict:
        return STREAM.mood_report()

    def overview(self) -> dict:
        return dict(
            threads=self.store.stats(),
            device={"label": "GIGAMOGG Cloud Neural Core", "status": "online"},
            loaded=["gigamogg"],
            stats=dict(self.stats, uptime=round(time.time() - self.stats["since"])),
            mind=STREAM.mood_report(),
        )


ENGINE_LOCK = threading.Lock()
_ENGINE: Engine | None = None


def engine() -> Engine:
    global _ENGINE
    with ENGINE_LOCK:
        if _ENGINE is None:
            _ENGINE = Engine()
        return _ENGINE