import os
import pandas as pd
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
    hed_schema = schema.load_schema(schema_path)
    temp_path, issues = schema.convert_schema_to_format(local_hed_file=schema_path, save_as_legacy_xml=True)
    schema_save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.3a.xml')
    print(temp_path)
    if issues:
        print('Had issues')
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0-alpha.1.xml')