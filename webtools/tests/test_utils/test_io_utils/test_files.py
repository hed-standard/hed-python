import os
import io
import shutil
import unittest
import hedweb.utils.io_utils
from hedweb.app_factory import AppFactory


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upload_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/upload')
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

    def test_file_extension_is_valid(self):
        from hedweb.utils.io_utils import file_extension_is_valid
        is_valid = file_extension_is_valid('abc.xml', ['.xml', '.txt'])
        self.assertTrue(is_valid, 'File name has a valid extension if the extension is in list of valid extensions')
        is_valid = file_extension_is_valid('abc.XML', ['.xml', '.txt'])
        self.assertTrue(is_valid, 'File name has a valid extension if capitalized version of valid extension')
        is_valid = file_extension_is_valid('abc.temp', ['.xml', '.txt'])
        self.assertFalse(is_valid, 'File name has a valid extension if the extension not in list of valid extensions')
        is_valid = file_extension_is_valid('abc')
        self.assertTrue(is_valid, 'File names with no extension are valid when no valid extensions provided')
        is_valid = file_extension_is_valid('abc', ['.xml', '.txt'])
        self.assertFalse(is_valid, 'File name has a valid extension if the extension not in list of valid extensions')
        is_valid = file_extension_is_valid('C:abc.Txt', ['.xml', '.txt'])
        self.assertTrue(is_valid, 'File name has a valid extension if the extension is in list of valid extensions')

    def test_file_to_string(self):
        from hedweb.utils.io_utils import file_to_string
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids_events_alpha.json')

        with open(json_path, 'r') as sc:
            x = sc.read()
        json_buffer = io.BytesIO(bytes(x, 'utf-8'))

        filename = 'HED8.0.0-beta.1.xml'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/HED8.0.0-beta.1.xml')
        # with open(hed_file) as f:
        #    upload_file = FileStorage(f, filename='HED.xml', content_type='text/xml',  content_length=0, stream=stream)
        #    with self.app.app_context():
        #         the_path = save_file_to_upload_folder(upload_file)
        #         self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")

        # temp_name = save_file_to_upload_folder('')

    def test_generate_filename(self):
        from hedweb.utils.io_utils import generate_filename
        filename = generate_filename(None, prefix=None, suffix=None, extension=None)
        self.assertEqual('', filename, "Return empty when all arguments are none")
        filename = generate_filename(None, prefix=None, suffix=None, extension='.txt')
        self.assertEqual('', filename, "Return empty when base_name, prefix, and suffix are None, but extension is not")
        filename = generate_filename('c:/temp.json', prefix=None, suffix=None, extension='.txt')
        self.assertEqual('c_temp.txt', filename,
                         "Returns stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename('temp.json', prefix='prefix', suffix='suffix', extension='.txt')
        self.assertEqual('prefix_temp_suffix.txt', filename,
                         "Return stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename(None, prefix='prefix', suffix='suffix', extension='.txt')
        self.assertEqual('prefix_suffix.txt', filename,
                         "Returns correct string when no base_name")
        filename = generate_filename('event-strategy-v3_task-matchingpennies_events.json',
                                     suffix='blech', extension='.txt')
        self.assertEqual('event-strategy-v3_task-matchingpennies_events_blech.txt', filename,
                         "Returns correct string when base_name with hyphens")
        filename = generate_filename('HED7.1.2.xml', suffix='blech', extension='.txt')
        self.assertEqual('HED7.1.2_blech.txt', filename, "Returns correct string when base_name has periods")

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

    def test_handle_error(self):
        self.assertTrue(True, "Testing to be done")

    def test_save_file_to_upload_folder(self):
        self.assertTrue(1, "Testing save_file_to_upload_folder")
        filename = 'HED8.0.0-beta.1.xml'
        actual_path = os.path.join(self.upload_directory, filename)
        self.assertEqual(0, os.path.isfile(actual_path), f"{actual_path} should not exist before saving")
        hed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/HED8.0.0-beta.1.xml')
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
        with self.app.app_context():
            from hedweb.utils.io_utils import save_text_to_upload_folder
            the_path = save_text_to_upload_folder(text, filename)
            self.assertEqual(1, os.path.isfile(the_path), f"{the_path} should exist after saving")


if __name__ == '__main__':
    unittest.main()
