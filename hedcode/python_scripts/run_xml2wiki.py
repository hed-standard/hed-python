"""
TODO: Update to current version of the schema

Example of converting a hed schema from .xml format to .mediawiki format.

Functions Demonstrated:
wiki2xml.convert_schema_to_format - Converts hed schema from given url or filename,
                                    returns a temporary filename for the converted file and a list of issues.
hed.get_printable_issue_string - method that converts the list of issues to a human readable form.
"""

from shutil import move
from hed.util.file_util import write_strings_to_file
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema, convert_schema_to_format


if __name__ == '__main__':
    hed_xml_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml'
    local_hed_file = None
    hed_schema = load_schema(hed_file_path=local_hed_file, hed_url_path=hed_xml_url)
    file_strings, errors = convert_schema_to_format(hed_schema, save_as_mediawiki=True)
    issue_str = get_printable_issue_string(issues=errors, title="Errors in HED8.0.xml:")
    if issue_str:
        print(issue_str)
    if file_strings:
        mediawiki_location = write_strings_to_file(file_strings)
        move(mediawiki_location, "HED8.0.0.mediawiki")
