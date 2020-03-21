import unittest;
import json;
from hedemailer.app_factory import AppFactory;
import hedemailer;


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Test.create_test_app();
        hed_payload_file = 'data/hed_payload.json';
        cls.file_that_exist = 'data/exist.txt';
        cls.file_that_does_not_exit = 'data/does_not_exist.txt';
        Test.get_payload_from_file(hed_payload_file);

    @classmethod
    def get_payload_from_file(cls, hed_payload_file):
        with open(hed_payload_file, 'r', encoding='utf-8') as opened_hed_payload_file:
            cls.hed_payload_string = json.dumps(json.load(opened_hed_payload_file));

    @classmethod
    def create_test_app(cls):
        app = AppFactory.create_app('config.TestConfig');
        with app.app_context():
            from hedemailer.routes import route_blueprint;
            app.register_blueprint(route_blueprint);
            cls.app = app.test_client();

    def create_file_in_data_dir(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            print(file_path + ' created');

    def test_wiki_page_is_hed_schema(self):
        github_payload_dictionary = {};
        is_hed_schema = hedemailer.utils.push_page_is_hed_schema(github_payload_dictionary)
        self.assertFalse(is_hed_schema, 'Wiki page should not be HED schema');
        github_payload_dictionary = {};
        is_hed_schema = hedemailer.utils.push_page_is_hed_schema(github_payload_dictionary)
        self.assertFalse(is_hed_schema, 'Wiki page should be HED schema');

    def test_delete_file_if_exist(self):
        self.create_file_in_data_dir(self.file_that_exist);
        file_deleted = hedemailer.utils.delete_file_if_exist(self.file_that_exist);
        self.assertTrue(file_deleted, 'File should have been deleted');
        file_deleted = hedemailer.utils.delete_file_if_exist(self.file_that_does_not_exit);
        self.assertFalse(file_deleted, 'File should not have been deleted. Does not exist');


if __name__ == "__main__":
    unittest.main()
