import os
# from hed.schema.hed_schema_file import from_string
from hed import schema


if __name__ == '__main__':
    # schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')
    # schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED7.1.2.xml')
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'data/HED-generation3-schema-8.0.0-alpha.3.mediawiki')
    # # Testing conversion from string
    # with open(schema_path, "r") as myfile:
    #     schema_string = myfile.read()
    # hed_schema = schema.from_string(schema_string)

    # Load schema and save as legacy XML
    hed_schema = schema.load_schema(hed_file_path=schema_path)
    temp_path, issues = schema.convert_schema_to_format(hed_schema, save_as_legacy_xml=True)
    schema_save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.3.xml')
    schema_version = schema.get_hed_xml_version(temp_path)
    print(schema_version)
    if issues:
        print('Had issues')
