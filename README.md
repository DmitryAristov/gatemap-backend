# Gatemap Backend

## 🔄 Работа с базой данных (Alembic)

Если вы изменили модели:

1. Обновите файл `models.py`.
2. Сгенерируйте миграцию:
   ```bash
   alembic revision --autogenerate -m "Описание изменений"
   ```
3. Проверьте сгенерированный файл в `alembic/versions/{...}.py`.
4. Примените миграции:
   ```bash
   alembic upgrade head
   ```

---

## 🚀 Запуск проекта локально

1. В `main.py` закомментируйте строку:
   ```python
   # app.add_middleware(HTTPSRedirectMiddleware)
   ```
   Это отключит редирект на HTTPS.

2. Для запуска с HTTPS — раскомментируйте её обратно.

---

## 📦 Установка зависимостей

Если вы добавили новую зависимость в `requirements.txt`, выполните:

```bash
pip install -r requirements.txt
```

---

## 🐍 Работа с виртуальным окружением

Создание окружения:

```bash
python3 -m venv .venv
```

Активация:

```bash
source .venv/bin/activate
```

---

## ▶️ Запуск сервиса

```bash
bash run.sh
```

---

## 📁 Структура проекта (основные файлы)

- `main.py` — точка входа, инициализация FastAPI
- `models.py` — модели SQLAlchemy
- `schemas.py` — схемы Pydantic
- `routes.py` — эндпоинты API
- `alembic/` — миграции базы данных
- `app/tasks.py` — фоновые задачи (очистка, статистика)
