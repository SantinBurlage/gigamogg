FROM python:3.11-slim

# Установка системных утилит
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода проекта
COPY . .

# Переменные окружения для хостинга
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8000 \
    HOST=0.0.0.0

EXPOSE 8000

# Запуск сервера GIGAMOGG
CMD ["python", "run.py", "serve"]
