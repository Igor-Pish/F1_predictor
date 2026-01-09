from flask import Flask
import fastf1
import os

from .db import create_db
from .api import api

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"

    # гарантируем наличие директории для кэша
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "f1_cache")
    cache_dir = os.path.abspath(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)

    create_db()
    app.register_blueprint(api)
    return app