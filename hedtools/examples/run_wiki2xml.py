"""
Example of converting a hed schema from .mediawiki format to .xml format.

Functions Demonstrated:
wiki2xml.convert_hed_wiki_2_xml - Converts hed schema from given url or filename,
                                    returns a temporary filename for the converted file and a list of issues.
ErrorHandler.get_printable_issue_string - Static method that converts the list of issues to a human readable form.
"""
from shutil import move
from hed.schema import wiki2xml
from hed.util.error_reporter import ErrorHandler

if __name__ == '__main__':
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-generation3-schema.mediawiki'
    local_hed_file = None
    xml_location, errors = wiki2xml.convert_hed_wiki_2_xml(hed_wiki_url, local_wiki_file=local_hed_file)
    ErrorHandler.get_printable_issue_string(validation_issues=errors, title="Errors in HED-generation3-schema.mediawiki")
    if xml_location:
        move(xml_location, "output.xml")