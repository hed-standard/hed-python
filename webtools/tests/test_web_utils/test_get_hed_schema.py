import os
import shutil
import unittest
from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hedweb.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_get_hed_schema_path_tests(self):
        from hed.schema.hed_schema import HedSchema
        from hedweb.constants import common
        from hedweb.web_utils import get_hed_schema

        # Test
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED7.1.2.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED7.1.2.xml',
                     common.COMMAND: common.COMMAND_CONVERT}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('7.1.2', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.1.xml')
        arguments = {common.SCHEMA_PATH: schema_path, 'schema_display_name': 'HED8.0.0-alpha.1.xml',
                     common.COMMAND: common.COMMAND_CONVERT}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('8.0.0-alpha.1', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

    def test_get_hed_schema_string_tests(self):
        from hed.schema.hed_schema import HedSchema
        from hedweb.constants import common
        from hedweb.web_utils import get_hed_schema

        # Test
        schema_v7 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED7.1.2.xml')
        with open(schema_v7, "r") as myfile:
            schema_string = myfile.read()
        arguments = {common.SCHEMA_STRING: schema_string}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('7.1.2', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

        schema_v7 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 '../data/HED-generation2-schema-7.2.0.mediawiki')
        with open(schema_v7, "r") as myfile:
            schema_string = myfile.read()
        arguments = {common.SCHEMA_STRING: schema_string, common.SCHEMA_FORMAT: '.mediawiki'}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, 'Issues should be empty')
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('7.2.0', schema_version, 'get_hed_schema HedSchema object should have correct version')

        schema_v8 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-alpha.1.xml')
        with open(schema_v8, "r") as myfile:
            schema_string = myfile.read()
        arguments = {common.SCHEMA_STRING: schema_string, common.COMMAND: common.COMMAND_CONVERT}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, 'get_hed_schema should return HedSchema object')
            issues = hed_schema.issues
            self.assertFalse(issues, 'Issues should be empty')
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('8.0.0-alpha.1', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

    def test_get_hed_schema_url_tests(self):
        from hed.schema.hed_schema import HedSchema
        from hedweb.constants import common
        from hedweb.web_utils import get_hed_schema

        # Test
        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED7.2.0.xml'
        arguments = {common.SCHEMA_URL: schema_url}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('7.2.0', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/' \
                     + 'hedxml/HED8.0.0-alpha.1.xml'
        arguments = {common.SCHEMA_URL: schema_url}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('8.0.0-alpha.1', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification' + \
                     '/master/HED-generation2-schema-7.2.0.mediawiki'
        arguments = {common.SCHEMA_URL: schema_url}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('7.2.0', schema_version,
                             'get_hed_schema HedSchema object should have correct version')

        schema_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/' \
                     + 'master/HED-generation3-schema-8.0.0-beta.1.mediawiki'
        arguments = {common.SCHEMA_URL: schema_url}
        with self.app.app_context():
            hed_schema = get_hed_schema(arguments)
            self.assertIsInstance(hed_schema, HedSchema, "get_hed_schema should return HedSchema object")
            issues = hed_schema.issues
            self.assertFalse(issues, "Issues should be empty")
            schema_version = hed_schema.header_attributes.get('version', 'Unknown version')
            self.assertEqual('8.0.0-beta.1', schema_version,
                             'get_hed_schema HedSchema object should have correct version')


if __name__ == '__main__':
    unittest.main()
