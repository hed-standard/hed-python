from pandas import DataFrame, to_numeric
import numpy as np
from hed.schema.hed_schema_file import load_schema_version
from hed.models.hed_string import HedString


def extract_definitions(bids):
    print("this")


if __name__ == '__main__':
    hed_version = "8.0.0"
    hed_str = "Sensory-event, Visual-presentation, Condition-variable/Blah, ((Square, Red), (Center-of, Computer-screen))"
    hed_schema = load_schema_version(xml_version_number=hed_version)
    hobj = HedString(hed_str)
    hobj.convert_to_canonical_forms(hed_schema)
    a = hobj.get_all_groups()
    print(f"{str(a)}")

    b = hobj.get_all_tags()
    print(f"Overall: {hed_str}")
    for tag in b:
      print(f"{tag.short_tag}")
