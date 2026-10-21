# ---- Stage 1: builder ----
# Устанавливает зависимости в изолированный venv.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: production ----
# Только запуск приложения, без инструментов сборки.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Копируем виртуальное окружение из builder (multi-stage).
COPY --from=builder /opt/venv /opt/venv

# Непривилегированный пользователь.
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Сначала код, затем права, чтобы владельцем был appuser.
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Uvicorn под gunicorn в production-режиме.
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "src.main:app"]