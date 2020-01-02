from flask import Flask;
from shutil import copyfile

app = Flask(__name__)
with app.app_context():
    from hedconversion import wiki2xml
    from hedemailer import constants
    #result_dict = wiki2xml.convert_hed_wiki_2_xml("HED-schema_dung.mediawiki")
    result_dict = wiki2xml.convert_hed_wiki_2_xml()
    xml_location = result_dict[constants.HED_XML_LOCATION_KEY]
    copyfile(xml_location, "result_xml.xml")
