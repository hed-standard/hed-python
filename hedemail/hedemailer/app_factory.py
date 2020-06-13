from flask import Flask
import importlib

STATIC_URL_PATH_ATTRIBUTE_NAME = 'STATIC_URL_PATH'


class AppFactory:
    @staticmethod
    def create_app(config_class):
        """Send a email with the latest HED schema.

        Parameters
        ----------
        config_class: string
            The configuration class.

        Returns
        -------
        hedemailer app
            A hedemailer Flask app.
        """
        static_url_path = AppFactory.get_static_url_path(config_class)
        app = Flask(__name__, static_url_path=static_url_path)
        app.config.from_object(config_class)
        return app

    @staticmethod
    def get_static_url_path(config_class):
        """Gets the static url path of the app.

        Parameters
        ----------
        config_class: string
            The configuration class.

        Returns
        -------
        string
            The static URL path of the hedmailer Flask app.
        """
        config_module_name, config_class_name = config_class.split(".")
        config_module = importlib.import_module(config_module_name)
        config_class = getattr(config_module, config_class_name)
        return getattr(config_class, STATIC_URL_PATH_ATTRIBUTE_NAME, None)
