
import os
import shutil
import unittest

from hed.web.app_factory import AppFactory


def test_input():
    base_path = os.path.dirname(os.path.abspath(__file__))
    test_inputs = {'hed-xml-file': os.path.join(base_path, 'data/HED8.0.0-alpha.1.xml'),
                   'hed-display-name': 'HED8.0.0-alpha.1.xml', 'hedstring': 'White'}

    return test_inputs


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/upload')
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hed.web.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            if not os.path.exists(cls.upload_directory):
                os.mkdir(cls.upload_directory)
            app.config['UPLOAD_FOLDER'] = cls.upload_directory
            cls.app = app
            cls.app.test = app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.upload_directory)

    def test_generate_input_from_hedstring_form(self):
        from hed.web import hedstring
        self.assertRaises(TypeError, hedstring.generate_input_from_hedstring_form, {},
                          "An exception should be raised if an empty request is passed")

    def test_hedstring_process(self):
        self.assertTrue(1, "process_hedstring")

    def test_hedstring_convert(self):
        from hed.web import hedstring
        input_arguments = {'hed-xml-file': 'data/'}
        self.assertTrue(1, "process_hedstring")

    def test_hedstring_validate(self):
        from hed.web.hedstring import hedstring_validate
        input = test_input()
        result = hedstring_validate(input)
        self.assertIsInstance(result, dict, "hedstring_validate should return a dictionary")
        self.assertEqual("No validation errors found...", result['hedstring-result'], "This is a valid hedstring for 8.0.0")
        # hed8_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        #
        # hed7_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        # hed7 = hed_schema_file.load_schema(hed7_path)
        # response = dictionary_validate(inputs, hed_schema=hed7)
        # inputs["hed-xml-file"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        # hed7 = hed_schema_file.load_schema(inputs["hed-xml_file"])
        # self.assertEqual("", dictionary_validate(arguments, hed_schema=schema8),
        #                  "This dictionary should have no errors for directly created 8.0.0")
        # schema7 = HedSchema(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml'))
        # x = dictionary_validate(arguments, hed_schema=schema7, return_response=False)
        # self.assertEqual("", dictionary_validate(arguments, hed_schema=schema7,return_response=False),
        #                  "This dictionary should have no errors for directly created 8.0.0")


if __name__ == '__main__':
    unittest.main()
