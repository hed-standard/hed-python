import unittest
from tests.test_web_base import TestWebBase


class Test(TestWebBase):

    def test_render_events_form(self):
        response = self.app.test.get('/events')
        self.assertEqual(response.status_code, 200, "The events content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_schema_form(self):
        response = self.app.test.get('/schema')
        self.assertEqual(response.status_code, 200, "The schema page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_services_form(self):
        response = self.app.test.get('/services')
        self.assertEqual(response.status_code, 200, "The hed-services content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_sidecar_form(self):
        response = self.app.test.get('/sidecar')
        self.assertEqual(response.status_code, 200, "The sidecar content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_spreadsheet_form(self):
        response = self.app.test.get('/spreadsheet')
        self.assertEqual(response.status_code, 200, "The spreadsheet page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_string_form(self):
        response = self.app.test.get('/string')
        self.assertEqual(response.status_code, 200, "The hedstring content page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

    def test_render_home_page(self):
        response = self.app.test.get('/')
        self.assertEqual(response.status_code, 200, "The root hed home page should exist")
        self.assertTrue(response.data, "The returned page should not be empty")

if __name__ == '__main__':
    unittest.main()
