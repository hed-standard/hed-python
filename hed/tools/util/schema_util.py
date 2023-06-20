import pandas as pd
from hed.schema.hed_schema_constants import HedSectionKey, HedKey


def flatten_schema(hed_schema, skip_non_tag=False):
    """ turns a schema into a 3 column dataframe.
    Parameters:
        hed_schema (HedSchema): the schema to flatten
        skip_non_tag (bool): Skips all sections except tag

    """
    children, parents, descriptions = [], [], []
    for section in hed_schema._sections.values():
        if skip_non_tag and section.section_key != HedSectionKey.AllTags:
            continue
        for entry in section.all_entries:
            if entry.has_attribute(HedKey.TakesValue):
                continue
            name = ""
            parent = ""
            desc = entry.description
            if hasattr(entry, "_parent_tag"):
                name = entry.short_tag_name
                if entry._parent_tag:
                    parent = entry._parent_tag.short_tag_name
                else:
                    parent = ""
            else:
                name = entry.name
                parent = ""

            parents.append(parent)
            children.append(name)
            descriptions.append(desc)

    df = pd.DataFrame({"Child": children, "Parent": parents, "Description": descriptions})

    return df
