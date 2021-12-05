"""
TODO:  Update to current version of the schema

Example of converting a hed schema from .mediawiki format to .xml format.

Functions Demonstrated:
schema.convert_schema_to_format - Converts hed schema from given url or filename,
                                    returns a temporary filename for the converted file and a list of issues.
hed.get_printable_issue_string - method that converts the list of issues to a human readable form.
"""
from shutil import move
from hed.util.file_util import write_strings_to_file
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema, convert_schema_to_format

if __name__ == '__main__':

    # Convert an HED-2G schema from mediawiki to XML.
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master' + \
                   '/hedwiki/HED7.3.0.mediawiki'
    print("Converting HED7.3.0.mediawiki with compliance check (it is not compliant):")
    hed_schema = load_schema(hed_url_path=hed_wiki_url)
    file_strings, errors = convert_schema_to_format(hed_schema, save_as_legacy_xml=True)
    if errors:
        issue_str = get_printable_issue_string(issues=errors, title="HED7.3.0.mediawiki is not HED-3G compliant")
        print(issue_str)
    if file_strings:
        xml_location = write_strings_to_file(file_strings)
        move(xml_location, "outputGen2.xml")

    print("Converting HED7.3.0.mediawiki with no compliance check:")
    file_strings, errors = convert_schema_to_format(hed_schema, check_for_issues=False, save_as_legacy_xml=True)
    if errors:
        issue_str = get_printable_issue_string(issues=errors,
                                               title="HED7.3.0.mediawiki should not have errors if no compliance check")
        print(issue_str)
    if file_strings:
        xml_location = write_strings_to_file(file_strings)
        move(xml_location, "outputGen2_no_compliance.xml")

    # Convert an HED-3G schema from mediawiki to XML.
    print("Converting HED8.0.0.mediawiki with compliance check:")
    hed_wiki_url = 'https://raw.githubusercontent.com/hed-standard/hed-specification/master' + \
                   '/hedwiki/HED8.0.0.mediawiki'
    hed_schema = load_schema(hed_url_path=hed_wiki_url)
    file_strings, errors = convert_schema_to_format(hed_schema)
    if errors:
        issue_str = get_printable_issue_string(issues=errors, title="Errors in HED8.0.0.mediawiki")
        print(issue_str)
    if file_strings:
        xml_location = write_strings_to_file(file_strings)
        move(xml_location, "outputGen3.xml")
