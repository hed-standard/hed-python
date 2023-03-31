import pandas as pd
from hed.schema.hed_schema_constants import HedSectionKey


def flatten_schema(hed_schema, skip_non_tag=False):
    """ turns a schema into a 3 column dataframe.
    Parameters:
        hed_schema (HedSchema): the schema to flatten
        skip_non_tag (bool): Skips all sections except tag

    """
    child, parent, desc = [], [], []
    for section in hed_schema._sections.values():
        if skip_non_tag and section.section_key != HedSectionKey.AllTags:
            continue
        for entry in section.all_entries:
            if hasattr(entry, "_parent_tag"):
                child.append(entry.short_tag_name)
                if entry._parent_tag:
                    parent.append(entry._parent_tag.short_tag_name)
                else:
                    parent.append("")
            else:
                child.append(entry.name)
                parent.append("")

            desc.append(entry.description)

    df = pd.DataFrame({"Child": child, "Parent": parent, "Description": desc})

    return df
