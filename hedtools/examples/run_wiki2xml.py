"""
Example of converting a hed schema from .mediawiki format to .xml format.

Functions Demonstrated:
schema.convert_schema_to_format - Converts hed schema from given url or filename,
                                    returns a temporary filename for the converted file and a list of issues.
hed.get_printable_issue_string - method that converts the list of issues to a human readable form.
"""
from shutil import move
import hed
from hed import schema
from hed.util.file_util import write_strings_to_file


if __name__ == '__main__':
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-generation2-schema-7.3.0.mediawiki'
    local_hed_file = None
    hed_schema = schema.load_schema(hed_file_path=local_hed_file, hed_url_path=hed_wiki_url)
    file_strings, errors = schema.convert_schema_to_format(hed_schema)
    hed.get_printable_issue_string(validation_issues=errors, title="Errors in HED-generation3-schema.mediawiki")
    if file_strings:
        xml_location = write_strings_to_file(file_strings)
        move(xml_location, "outputGen2.xml")

    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/HED-generation3-schema-8.0.0-alpha.2.mediawiki'
    local_hed_file = None
    hed_schema = schema.load_schema(hed_file_path=local_hed_file, hed_url_path=hed_wiki_url)
    file_strings, errors = schema.convert_schema_to_format(hed_schema)
    hed.get_printable_issue_string(validation_issues=errors, title="Errors in HED-generation3-schema.mediawiki")
    if file_strings:
        xml_location = write_strings_to_file(file_strings)
        move(xml_location, "outputGen3.xml")