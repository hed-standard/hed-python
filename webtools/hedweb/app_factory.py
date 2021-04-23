from flask import Flask
from flask_wtf.csrf import CSRFProtect
import importlib
from config import Config


class AppFactory:
    @staticmethod
    def create_app(config_class):
        static_url_path = AppFactory.get_static_url_path(config_class)
        app = Flask(__name__, static_url_path=static_url_path)
        app.config.from_object(config_class)
        CSRFProtect(app)
        return app

    @staticmethod
    def get_static_url_path(config_class):
        config_module_name, config_class_name = config_class.split(".")
        config_module = importlib.import_module(config_module_name)
        config_class = getattr(config_module, config_class_name)
        return getattr(config_class, Config.STATIC_URL_PATH_ATTRIBUTE_NAME, None)
