# ---- Builder ----
# Устанавливает зависимости в изолированный venv (multi-stage, ЛР 20/21 стиль).
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Runtime ----
# Один образ для всех микросервисов. Конкретный сервис и команда запуска
# задаются через переменную окружения APP_MODULE / переопределение CMD
# в docker-compose.yml.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Копируем весь корень проекта: общий пакет shared и каталоги сервисов.
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Запуск по умолчанию — readers-service (переопределяется в compose).
CMD ["python", "-m", "app.main"]