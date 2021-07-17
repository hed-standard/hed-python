import os
import io
import shutil
import unittest
import hedweb.utils.io_utils
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


    def test_file_to_string(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_events_alpha.json')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))

        filename = 'HED8.0.0-beta.1.xml'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-beta.1.xml')
        # with open(hed_file) as f:
        #    upload_file = FileStorage(f, filename='HED.xml', content_type='text/xml',  content_length=0, stream=stream)
        #    with self.app.app_context():
        #         the_path = save_file_to_upload_folder(upload_file)
        #         self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")

        # temp_name = save_file_to_upload_folder('')



    def test_get_optional_form_field(self):
        self.assertTrue(1, "Testing get_optional_form_field")

    def test_get_uploaded_file_path_from_form(self):
        pass
        # with self.app.test as client:
        #     # send data as POST form to endpoint
        #     sent = {'return_url': 'my_test_url'}
        #     result = client.post(
        #         '/',
        #         data=sent
        #     )
        # mock_form = mock.Mock()
        # mock_dict = {'upload': 'me', 'download:': 'them'}
        #     mock_form.values = mock_dict
        # text = 'save me now'
        # filename = 'test_save.txt'
        # actual_path = os.path.join(self.upload_directory, filename)
        # self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        # with self.app.app_context():
        # the_path = save_text_to_upload_folder(text, filename)
        # self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")

    # def test_handle_http_error(self):
    #     error_code = "CODE"
    #     error_message = "Test"
    #
    #     self.assertTrue(1, "Testing handle_http_error")+


    def test_save_file_to_upload_folder(self):
        self.assertTrue(1, "Testing save_file_to_upload_folder")
        filename = 'HED8.0.0-beta.1.xml'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/HED8.0.0-beta.1.xml')
        # with open(hed_file) as f:
        #    upload_file = FileStorage(f, filename='HED.xml', content_type='text/xml',  content_length=0, stream=stream)
        #    with self.app.app_context():
        #         the_path = save_file_to_upload_folder(upload_file)
        #         self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")

        # temp_name = save_file_to_upload_folder('')
        # self.assertEqual(temp_name, '', "A file with empty name cnnot be copied copied")
        # some_file = '3k32j23kj1.txt'
        # temp_name = save_file_to_upload_folder(some_file)
        # self.assertEqual(temp_name, '', "A file that does not exist cannot be copied")
        # hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        #
        # self.assertTrue(os.path.exists(hed_file), "The HED.xml file should exist in the data directory")
        # actual_path = os.path.join(self.upload_directory, filename)
        # self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        # with self.app.app_context():
        #     the_path = save_text_to_upload_folder(text, filename)
        #     self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")
        # mock_file = mock.Mock()
        # mock_file.filename = hed_file
        # TODO: Context not working this is not tested
        # with Test.app_context():
        #     temp_name = save_file_to_upload_folder(mock_file)
        # self.assertNotEqual(mock_file, '', "It should create an actual file in the upload directory")
        # self.assertTrue(os.path.isfile(temp_name), "File should exist after it is uploaded")

    def test_save_file_to_upload_folder_no_exception(self):
        self.assertTrue(True, "Testing to be done")

    def test_save_text_to_upload_folder(self):
        text = 'save me now'
        filename = 'test_save.txt'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")



if __name__ == '__main__':
    unittest.main()
