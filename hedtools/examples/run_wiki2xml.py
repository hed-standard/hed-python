"""
Example of converting a hed schema from .mediawiki format to .xml format.

Functions Demonstrated:
schema.convert_schema_to_format - Converts hed schema from given url or filename,
                                    returns a temporary filename for the converted file and a list of issues.
hed.get_printable_issue_string - method that converts the list of issues to a human readable form.
"""
from shutil import move
import hed
from hed.schema.hed_schema_file import convert_schema_to_format

if __name__ == '__main__':
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-generation2-schema-7.3.0.mediawiki'
    local_hed_file = None
    xml_location, errors = convert_schema_to_format(hed_wiki_url, local_hed_file=local_hed_file)
    hed.get_printable_issue_string(validation_issues=errors, title="Errors in HED-generation3-schema.mediawiki")
    if xml_location:
        move(xml_location, "outputGen2.xml")

    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-generation3-schema-8.0.0-alpha.2.mediawiki'
    local_hed_file = None
    xml_location, errors = convert_schema_to_format(hed_wiki_url, local_hed_file=local_hed_file)
    hed.get_printable_issue_string(validation_issues=errors, title="Errors in HED-generation3-schema.mediawiki")
    if xml_location:
        move(xml_location, "outputGen3.xml")