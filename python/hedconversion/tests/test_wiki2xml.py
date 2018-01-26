'''
Created on Jul 25, 2017

@author: jcockfie
'''
import unittest;
from hedemailer.hedconversion.wiki2xml import *;


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        pass
    
    @classmethod
    def tearDownClass(self):
        self.github_payload_file.close();
        
    def test_send_notification_email(self):
        pass
    
    def test_create_hed_xml_file(self):
        create_hed_xml_file('');


if __name__ == "__main__":
    unittest.main()