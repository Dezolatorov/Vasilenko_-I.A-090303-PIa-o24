# LibraryAPI - production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# По умолчанию SQLite-файл в /data (volume); в compose переопределяется на PostgreSQL
ENV DATABASE_URL=sqlite:////data/library.db

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=5).status==200 else 1)"

CMD ["uvicorn", "src.library.main:app", "--host", "0.0.0.0", "--port", "8000"]