import os
import shutil
import unittest
from flask import Response
from hed.web.app_factory import AppFactory


def test_dictionaries():
    base_path = os.path.dirname(os.path.abspath(__file__))
    test_dict = {'hed-xml-file': os.path.join(base_path, 'data/HED8.0.0-alpha.1.xml'),
                 'hed-display-name': 'HED8.0.0-alpha.1.xml',
                 'json-path': os.path.join(base_path, 'data/short_form_valid.json'),
                 'json-file': 'short_form_valid.json',
                 'check-for-warnings': True}
    return test_dict


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

    def test_generate_input_from_dictionary_form(self):
        from hed.web import dictionary
        self.assertRaises(TypeError, dictionary.generate_input_from_dictionary_form, {},
                          "An exception should be raised if an empty request is passed")

    def test_validate_dictionary_success(self):
        from hed.web.dictionary import dictionary_validate
        from hed.schema import hed_schema_file
        inputs = test_dictionaries()
        response = dictionary_validate(inputs)
        print(type(response) is Response)
        self.assertTrue(type(response) is Response, "dictionary_validate should return a response if no error")

        hed8_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')

        hed7_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        hed7 = hed_schema_file.load_schema(hed7_path)
        # response = dictionary_validate(inputs, hed_schema=hed7)
        # inputs["hed-xml-file"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
        # hed7 = hed_schema_file.load_schema(inputs["hed-xml_file"])
        # self.assertEqual("", dictionary_validate(arguments, hed_schema=schema8),
        #                  "This dictionary should have no errors for directly created 8.0.0")
        # schema7 = HedSchema(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml'))
        # x = dictionary_validate(arguments, hed_schema=schema7, return_response=False)
        # self.assertEqual("", dictionary_validate(arguments, hed_schema=schema7,return_response=False),
        #                  "This dictionary should have no errors for directly created 8.0.0")

        # from hed.web import dictionary
        # print("First test.....")
        # r = Response("download_text", mimetype='text/plain charset=utf-8',
        #              headers={'Category': "success", 'Message': "This is a test of the response"})
        # the_list = r.headers.getlist('Content-Length')
        # print("HERE", int(the_list[0]))
        # for prop, value in vars(r).items():
        #     print(prop, ":", value)
        #
        # print("\nSecond test.....")
        # r = Response("", mimetype='text/plain charset=utf-8',
        #              headers={'Category': "success", 'Message': "This is empty"})
        # for prop, value in vars(r).items():
        #     print(prop, ":", value)
        # headers = r.headers
        # print(r.__dict__)
        # print(dir(r))
        # print('Headers....', r.headers)
        # print("headers field", headers.__dict__)
        # print("headers field", dir(headers))
        # print("headers_item", headers.__getitem__('Content-Length'))
        # the_list = headers.getlist('Content-Length')
        # print("CL", the_list)
        # the_len = int(the_list[0])
        # print('len:', the_len)
        # keys = headers.keys()
        # print("Keys", keys)
        # if r.response:
        #     print(r.response)
        # else:
        #     print("Second response is empty")


    # def test_generate_input_arguments_from_validation_form(self):
    #     from hed.web import dictionary
    #     self.assertRaises(TypeError, dictionary.generate_input_from_dictionary_form, {},
    #                       "An exception should be raised if an empty request is passed")
    #
    # def test_report_dictionary_validation_status(self):
    #     self.assertTrue(1, "Testing report_dictionary_validation_status")
    #
    # def test_validate_dictionary(self):
    #     from hed.web.dictionary import dictionary_validate
    #     from hed.schema import hed_schema_file
    #     inputs = test_dictionaries()
    #     self.assertEqual("", dictionary_validate(inputs), "This dictionary should have no errors for 8.0.0")
    #     hed8_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    #
    #     hed7_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    #     hed7 = hed_schema_file.load_schema(hed7_path)
    #     # response = dictionary_validate(inputs, hed_schema=hed7)
    #     # inputs["hed-xml-file"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    #     # hed7 = hed_schema_file.load_schema(inputs["hed-xml_file"])
    #     # self.assertEqual("", dictionary_validate(arguments, hed_schema=schema8),
    #     #                  "This dictionary should have no errors for directly created 8.0.0")
    #     # schema7 = HedSchema(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml'))
    #     # x = dictionary_validate(arguments, hed_schema=schema7, return_response=False)
    #     # self.assertEqual("", dictionary_validate(arguments, hed_schema=schema7,return_response=False),
    #     #                  "This dictionary should have no errors for directly created 8.0.0")

if __name__ == '__main__':
    unittest.main()
