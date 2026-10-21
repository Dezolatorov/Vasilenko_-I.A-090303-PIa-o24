from __future__ import annotations

import logging
import time

from flask import Flask, g, jsonify, render_template, request

from app.config import settings
from app.database import SessionLocal, create_tables, get_session
from app.routes.api import api
from app.routes.web import web
from app.seed import seed_database
from app.services.services import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger("library.web")


def create_app(config: dict | None = None, with_seed: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.secret_key)
    if config:
        app.config.update(config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger.info(
        "Запуск приложения: env=%s, database=%s",
        settings.flask_env,
        settings.database_url,
    )

    app.register_blueprint(web)
    app.register_blueprint(api)

    @app.teardown_appcontext
    def _remove_session(exception=None):
        SessionLocal.remove()

    @app.before_request
    def _start_timer():
        g.started = time.perf_counter()

    @app.after_request
    def _log_request(response):
        elapsed = (time.perf_counter() - getattr(g, "started", time.perf_counter())) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            elapsed,
        )
        return response

    def is_api() -> bool:
        return request.path.startswith("/api")

    @app.errorhandler(ValidationError)
    def _validation(error):
        if is_api():
            return jsonify({"detail": str(error), "code": error.code}), 400
        return render_template("error.html", message=str(error), code=400), 400

    @app.errorhandler(NotFoundError)
    def _not_found(error):
        if is_api():
            return jsonify({"detail": str(error), "code": error.code}), 404
        return render_template("404.html", message=str(error)), 404

    @app.errorhandler(ConflictError)
    def _conflict(error):
        if is_api():
            return jsonify({"detail": str(error), "code": error.code}), 409
        return render_template("error.html", message=str(error), code=409), 409

    @app.errorhandler(404)
    def _page_not_found(error):
        if is_api():
            return jsonify({"detail": "Ресурс не найден", "code": "NOT_FOUND"}), 404
        return render_template("404.html", message="Страница не найдена"), 404

    @app.errorhandler(500)
    def _server_error(error):
        logger.exception("Внутренняя ошибка сервера")
        if is_api():
            return jsonify({"detail": "Внутренняя ошибка сервера", "code": "INTERNAL_ERROR"}), 500
        return render_template("error.html", message="Внутренняя ошибка сервера", code=500), 500

    if with_seed:
        create_tables()
        session = get_session()
        seed_database(session)
        session.close()

    return app
