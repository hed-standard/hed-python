import os
import shutil
import unittest
from hedweb.app_factory import AppFactory
import sys
sys.path.append('hedtools')


class TestWebBase(unittest.TestCase):
    enable_csrf = False
    cache_schemas = False

    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed import schema as hedschema
            hedschema.set_cache_directory(app.config['HED_CACHE_FOLDER'])
            if cls.cache_schemas:
                hedschema.cache_all_hed_xml_versions()
            from hedweb.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            app.config['WTF_CSRF_ENABLED'] = cls.enable_csrf
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)
