import pandas as pd
from hed.models import TabularInput, HedStringFrozen, TagExpressionParser


def assemble_hed(data_input, columns_included=None, expand_defs=False):
    """ Return a dataframe representing the assembled HED annotations for an events file.

    Args:
        data_input (TabularInput): The input events file to be searched.
        columns_included (list or None):  A list of additional column names to include. If None, only onset is used.
        expand_defs (bool): If True, definitions are expanded when the events are assembled.

    Returns:
        DataFrame or None: A DataFrame with the assembled events.

    """

    if columns_included:
        columns = frozenset(list(data_input.dataframe.columns))
        eligible_columns = [x for x in columns_included if x in columns]
    else:
        eligible_columns = None

    hed_obj_list = get_assembled_strings(data_input, expand_defs=expand_defs)
    hed_string_list = [str(hed) for hed in hed_obj_list]
    if not eligible_columns:
        return pd.DataFrame({"HED_assembled": hed_string_list})
    df = data_input.dataframe[eligible_columns].copy(deep=True)
    df['HED_assembled'] = hed_string_list
    return df


def get_assembled_strings(events, hed_schema=None, expand_defs=False):
    """ Return a list of the HED string objects corresponding to the rows of events.

    Args:
        events (TabularInput): The input events file to be searched.
        hed_schema (HedSchema or HedschemaGroup): If provided the HedStrings are converted to canonical form.
        expand_defs (bool): If True, definitions are expanded when the events are assembled.

    Returns:
        List: A list ov HedString or HedStringComb objects.

    """

    hed_list = []
    for row, row_dict in events.iter_dataframe(return_row_dict=True, expand_defs=expand_defs, remove_definitions=True):
        this_group = row_dict.get("HED", None)
        if hed_schema and this_group:
            this_group.convert_to_canonical_forms(hed_schema)
            hed_list.append(this_group)
        else:
            hed_list.append(row_dict.get("HED", None))
    return hed_list


def search_tabular(data_input, hed_schema, query, columns_included=None):
    """ Return a dataframe with results of query.

    Args:
        data_input (TabularInput): The tabular input file (e.g., events) to be searched.
        hed_schema (HedSchema or HedSchemaGroup):  The schema(s) under which to make the query.
        query (str):     The str query to make.
        columns_included (list):  List of names of columns to include

    Returns:
        DataFrame or None: A DataFrame with the results of the query or None if no events satisfied the query.

    """
    if columns_included:
        columns = frozenset(list(data_input.dataframe.columns))
        eligible_columns = [x for x in columns_included if x in columns]
    else:
        eligible_columns = None

    hed_list = get_assembled_strings(data_input, hed_schema=hed_schema, expand_defs=True)
    expression = TagExpressionParser(query)
    hed_tags = []
    row_numbers = []
    for index, next_item in enumerate(hed_list):
        match = expression.search_hed_string(next_item)
        if not match:
            continue
        hed_tags.append(next_item)
        row_numbers.append(index)

    if not row_numbers:
        df = None
    elif not eligible_columns:
        df = pd.DataFrame({'row_number': row_numbers, 'HED_assembled': hed_tags})
    else:
        df = data_input.dataframe.iloc[row_numbers][eligible_columns].reset_index()  #df[eligible_columns] = data_input.dataframe.iloc[row_numbers][eligible_columns]
        df['HED_assembled'] = hed_tags
        df.rename(columns={'index': 'row_number'})
    return df


def filter_events(events, hed_schema, filter_hed):
    """ Return a dataframe with results of query. """
    return None


if __name__ == '__main__':
    import os
    from hed.models import Sidecar
    from hed.schema import load_schema_version
    root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../tests/data/bids/eeg_ds003654s_hed')
    events_path = os.path.realpath(os.path.join(root_path, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
    json_path = os.path.realpath(os.path.join(root_path, 'task-FacePerception_events.json'))
    sidecar = Sidecar(json_path, name='face_sub1_json')
    input_data = TabularInput(events_path, sidecar=sidecar, name="face_sub1_events")
    hed_schema = load_schema_version(xml_version="8.0.0")
    print("to here")

    # df = assemble_hed(input_data, columns_included=["onset", "duration", "event_type"], expand_defs=False)
    # df1 = assemble_hed(input_data, columns_included=["onset", "duration", "event_type"], expand_defs=True)
    # df2 = assemble_hed(input_data, columns_included=["onset", "baloney", "duration", "event_type"], expand_defs=False)
    # print("to there")

    query = "Sensory-event"
    df3 = search_tabular(input_data, hed_schema, query, columns_included=['onset', 'event_type'])

    print(f"{len(df3)} events match")