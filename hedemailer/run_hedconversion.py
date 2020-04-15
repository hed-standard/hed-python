from flask import Flask;
from shutil import copyfile


app = Flask(__name__)
with app.app_context():
    from hedconversion import wiki2xml
    from hedemailer import constants
    app.config.from_object('config.Config')

    hed_wiki_url = app.config[constants.CONFIG_HED_WIKI_URL_KEY]
    result_dict = wiki2xml.convert_hed_wiki_2_xml(hed_wiki_url)
    xml_location = result_dict[constants.HED_XML_LOCATION_KEY]
    copyfile(xml_location, "result_xml.xml")
