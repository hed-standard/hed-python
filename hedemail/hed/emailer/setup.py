import os
from flask.app import Flask
from hed.emailer.app_factory import AppFactory

CONFIG_ENVIRON_NAME = 'HEDEMAILER_CONFIG_CLASS'


def configure_app():
    if CONFIG_ENVIRON_NAME in os.environ:
        return AppFactory.create_app(os.environ.get(CONFIG_ENVIRON_NAME))
    else:
        return AppFactory.create_app('config.DevelopmentConfig')


app = Flask(__name__)
app.config.from_object('config.Config')
