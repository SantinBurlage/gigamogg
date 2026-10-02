# Руководство по развертыванию GIGAMOGG на хостинг

Данный проект полностью готов к развертыванию в облачных сервисах и на виртуальных серверах (VPS).

---

## Вариант 1. Развертывание на Render.com (Быстро и бесплатно)

1. Зарегистрируйтесь на [Render.com](https://render.com).
2. Загрузите проект в ваш GitHub / GitLab репозиторий.
3. На панели Render нажмите **New +** -> **Web Service**.
4. Подключите ваш репозиторий с проектом GIGAMOGG.
5. Настройки сервиса:
   - **Environment**: `Docker` (Render автоматически обнаружит `Dockerfile`).
   - Или выберите `Python 3`:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python run.py serve`
6. Переменные окружения (Environment Variables):
   - `PORT`: `8000` (Render подставит свой порт автоматически, проект его поддерживает).
   - `PYTHONUNBUFFERED`: `1`
7. Нажмите **Create Web Service**. Через 2 минуты сайт будет доступен по ссылке `https://ваш-проект.onrender.com`.

---

## Вариант 2. Развертывание на Railway.app

1. Перейдите на [Railway.app](https://railway.app) и авторизуйтесь через GitHub.
2. Нажмите **New Project** -> **Deploy from GitHub repo**.
3. Выберите репозиторий GIGAMOGG.
4. Railway автоматически распознает `Dockerfile` или `Procfile` и запустит сборку.
5. В разделе **Settings** -> **Networking** нажмите **Generate Domain**, чтобы получить публичный HTTPS адрес.

---

## Вариант 3. Развертывание на VPS (Ubuntu / Debian) через Docker Compose

Если у вас есть собственный VPS-сервер (Timeweb, Selectel, Hetzner, Beget и др.):

1. Подключитесь к VPS по SSH:
   ```bash
   ssh root@ВАШ_IP_СЕРВЕРА
   ```

2. Установите Docker и Docker Compose (если не установлены):
   ```bash
   apt update && apt install -y docker.io docker-compose git
   ```

3. Клонируйте проект или скопируйте файлы:
   ```bash
   git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> /opt/gigamogg
   cd /opt/gigamogg
   ```

4. Запустите контейнер в фоновом режиме:
   ```bash
   docker-compose up -d --build
   ```

5. Проверьте статус:
   ```bash
   docker ps
   ```
   Сайт сразу доступен по адресу `http://ВАШ_IP_СЕРВЕРА:8000`.

---

## Вариант 4. Настройка Nginx и SSL (Let's Encrypt) на VPS

Чтобы сайт открывался по вашему домену (например, `https://gigamogg.example.com`):

1. Установите Nginx и Certbot:
   ```bash
   apt install -y nginx certbot python3-certbot-nginx
   ```

2. Создайте конфиг `/etc/nginx/sites-available/gigamogg`:
   ```nginx
   server {
       server_name gigamogg.example.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. Активируйте конфиг и выпустите SSL-сертификат:
   ```bash
   ln -s /etc/nginx/sites-available/gigamogg /etc/nginx/sites-enabled/
   nginx -t && systemctl reload nginx
   certbot --nginx -d gigamogg.example.com
   ```

---

## Безопасность и аккаунты

- По умолчанию в базе данных `giga.db` создан администратор:
  - **Логин**: `Santin`
  - **Пароль**: `santin123`
  *(Рекомендуется сменить пароль при первом входе)*
- Обычные пользователи регистрируются прямо через модальное окно на сайте и получают чистый интерфейс диалога и Веб-Студии.
- Доступ к внутренним ML-нитям и управлению сервером имеют только администраторы (`Santin` / роль `admin`).
