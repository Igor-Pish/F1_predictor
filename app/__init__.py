from __future__ import annotations

from flask import Flask
from flask_cors import CORS
import fastf1

from .db import create_db
from .api import api


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # FastF1 cache для процесса Flask (воркер отдельно включает кэш сам)
    fastf1.Cache.enable_cache("f1_cache")

    create_db()
    app.register_blueprint(api)

    return app