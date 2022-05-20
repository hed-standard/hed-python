import pandas as pd
from hed.models import TabularInput, HedStringFrozen, TagExpressionParser


def assemble_hed(events, additional_columns=None, expand_defs=False):
    """ Return a dataframe representing the assembled HED annotations for an events file.

    Args:
        events (TabularInput): The input events file to be searched.
        additional_columns (list or None):  A list of additional column names to include. If None, only onset is used.
        expand_defs (bool): If True, definitions are expanded when the events are assembled.

    Returns:
        DataFrame or None: A DataFrame with the assembled events.

    """

    eligible_columns = list(events.dataframe.columns)
    frame_dict = {}
    if additional_columns:
        for column in additional_columns:
            if column in eligible_columns:
                frame_dict[column] = []

    hed_tags = []
    onsets = []
    for row_number, row_dict in events.iter_dataframe(return_row_dict=True, expand_defs=expand_defs,
                                                      remove_definitions=True):
        hed_tags.append(str(row_dict.get("HED", "")))
        onsets.append(row_dict.get("onset", "n/a"))
        for column in frame_dict:
            frame_dict[column].append(events.dataframe.loc[row_number - 2, column])
    df = pd.DataFrame({'onset': onsets})
    for column, values in frame_dict.items():
        df[column] = values
    df['HED'] = hed_tags
    return df


def search_events(events, query, hed_schema):
    """ Return a dataframe with results of query.

    Args:
        events (TabularInput): The input events file to be searched.
        query (str):     The str query to make.
        hed_schema (HedSchema or HedSchemaGroup):  The schema(s) under which to make the query.

    Returns:
        DataFrame or None: A DataFrame with the results of the query or None if no events satisfied the query.

    """
    matched_tags = []
    hed_tags = []
    row_numbers = []
    expression = TagExpressionParser(query)
    for row_number, row_dict in events.iter_dataframe(return_row_dict=True, expand_defs=True, remove_definitions=True):
        expanded_string = str(row_dict.get("HED", ""))
        hed_string = HedStringFrozen(expanded_string, hed_schema=hed_schema)
        match = expression.search_hed_string(hed_string)
        if not match:
            continue
        match_str = ""
        for m in match:
            match_str = match_str + f" [{str(m)}] "

        hed_tags.append(expanded_string)
        matched_tags.append(match_str)
        row_numbers.append(row_number)

    if row_numbers:
        return pd.DataFrame({'row_number': row_numbers, 'matched_tags': matched_tags, 'HED': hed_tags})
    else:
        return None


def filter_events(events, filter, hed_schema):
    """ Return a dataframe with results of query.

    Args:
        events (TabularInput): The input events file to be searched.
        query (str):     The str query to make.
        hed_schema (HedSchema or HedSchemaGroup):  The schema(s) under which to make the query.

    Returns:
        DataFrame or None: A DataFrame with the results of the query or None if no events satisfied the query.

    """
    matched_tags = []
    hed_tags = []
    row_numbers = []
    expression = TagExpressionParser(query)
    for row_number, row_dict in events.iter_dataframe(return_row_dict=True, expand_defs=True, remove_definitions=True):
        expanded_string = str(row_dict.get("HED", ""))
        hed_string = HedStringFrozen(expanded_string, hed_schema=hed_schema)
        match = expression.search_hed_string(hed_string)
        if not match:
            continue
        match_str = ""
        for m in match:
            match_str = match_str + f" [{str(m)}] "

        hed_tags.append(expanded_string)
        matched_tags.append(match_str)
        row_numbers.append(row_number - 2)

    if row_numbers:
        return pd.DataFrame({'row_number': row_numbers, 'matched_tags': matched_tags, 'HED': hed_tags})
    else:
        return None

