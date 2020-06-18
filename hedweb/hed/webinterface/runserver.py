import os
from hed.webinterface.app_factory import AppFactory
from logging.handlers import RotatingFileHandler
from logging import ERROR

CONFIG_ENVIRON_NAME = 'HEDTOOLS_CONFIG_CLASS'


def setup_logging():
    """Sets up the current_application logging. If the log directory does not exist then there will be no logging.

    """
    if not app.debug and os.path.exists(app.config['LOG_DIRECTORY']):
        file_handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setLevel(ERROR)
        app.logger.addHandler(file_handler)


def configure_app():
    """Configures the current application. Checks to see if a environment variable exist and if it doesn't then it
       defaults to another configuration.

    """
    if CONFIG_ENVIRON_NAME in os.environ:
        return AppFactory.create_app(os.environ.get(CONFIG_ENVIRON_NAME))
    else:
        return AppFactory.create_app('config.DevelopmentConfig')


app = configure_app()
with app.app_context():
    from hed.webinterface import utils
    from hed.webinterface.routes import route_blueprint

    app.register_blueprint(route_blueprint, url_prefix=app.config['URL_PREFIX'])
    utils.create_upload_directory(app.config['UPLOAD_FOLDER'])
    setup_logging()

if __name__ == '__main__':
    app.run()
