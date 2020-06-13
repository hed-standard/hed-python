import unittest
import json
from hedemailer.app_factory import AppFactory
from hedemailer import constants


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        hed_payload_file = 'data/hed_payload.json'
        Test.create_test_app()
        Test.get_payload_from_file(hed_payload_file)

    @classmethod
    def get_payload_from_file(cls, hed_payload_file):
        with open(hed_payload_file, 'r', encoding='utf-8') as opened_hed_payload_file:
            cls.hed_payload_string = json.dumps(json.load(opened_hed_payload_file))

    @classmethod
    def create_test_app(cls):
        app = AppFactory.create_app('config.TestConfig')
        with app.app_context():
            from hedemailer.routes import route_blueprint
            app.register_blueprint(route_blueprint)
            cls.app = app.test_client()

    def test_no_hed_payload(self):
        response = self.app.post('/')
        self.assertEqual(response.status_code, 200)

    def test_good_hed_payload(self):
        self.app.application.config['EMAIL_LIST'] = 'data/emails.txt'
        response = self.app.post('/', data=self.hed_payload_string,
                                 headers={constants.HEADER_CONTENT_TYPE: constants.JSON_CONTENT_TYPE,
                                          'X-GitHub-Event': 'gollum'})
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
