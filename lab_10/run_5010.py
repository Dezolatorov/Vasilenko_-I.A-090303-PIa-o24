"""Запуск REST API на порту 5010 (для параллельного просмотра с ЛР №11)."""

from app import create_app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5010)