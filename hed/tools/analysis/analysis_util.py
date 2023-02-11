""" Utilities for assembly, analysis, and searching. """

import pandas as pd
from hed.models.tabular_input import TabularInput
from hed.models.expression_parser import QueryParser
from hed.tools.util.data_util import separate_values
from hed.models.hed_tag import HedTag
from hed.models.hed_group import HedGroup


def assemble_hed(data_input, columns_included=None, expand_defs=False):
    """ Return assembled HED annotations in a dataframe.

    Parameters:
        data_input (TabularInput): The tabular input file whose HED annotations are to be assembled.
        columns_included (list or None):  A list of additional column names to include.
            If None, only the list of assembled tags is included.
        expand_defs (bool): If True, definitions are expanded when the events are assembled.

    Returns:
        DataFrame or None: A DataFrame with the assembled events.
        dict: A dictionary with definition names as keys and definition content strings as values.
    """

    eligible_columns, missing_columns = separate_values(list(data_input.dataframe.columns), columns_included)
    hed_obj_list = get_assembled_strings(data_input, expand_defs=expand_defs)
    hed_string_list = [str(hed) for hed in hed_obj_list]
    if not eligible_columns:
        df = pd.DataFrame({"HED_assembled": hed_string_list})
    else:
        df = data_input.dataframe[eligible_columns].copy(deep=True)
        df['HED_assembled'] = hed_string_list
    definitions = data_input.get_definitions().gathered_defs
    return df, definitions


def get_assembled_strings(table, hed_schema=None, expand_defs=False):
    """ Return HED string objects for a tabular file.

    Parameters:
        table (TabularInput): The input file to be searched.
        hed_schema (HedSchema or HedschemaGroup): If provided the HedStrings are converted to canonical form.
        expand_defs (bool): If True, definitions are expanded when the events are assembled.

    Returns:
        list: A list of HedString or HedStringGroup objects.

    """
    hed_list = list(table.iter_dataframe(hed_ops=[hed_schema], return_string_only=True,
                                         expand_defs=expand_defs, remove_definitions=True))
    return hed_list


def search_tabular(data_input, hed_schema, query, columns_included=None):
    """ Return a dataframe with results of query.

    Parameters:
        data_input (TabularInput): The tabular input file (e.g., events) to be searched.
        hed_schema (HedSchema or HedSchemaGroup):  The schema(s) under which to make the query.
        query (str or list):     The str query or list of string queries to make.
        columns_included (list or None):  List of names of columns to include

    Returns:
        DataFrame or None: A DataFrame with the results of the query or None if no events satisfied the query.

    """

    eligible_columns, missing_columns = separate_values(list(data_input.dataframe.columns), columns_included)
    hed_list = get_assembled_strings(data_input, hed_schema=hed_schema, expand_defs=True)
    expression = QueryParser(query)
    hed_tags = []
    row_numbers = []
    for index, next_item in enumerate(hed_list):
        match = expression.search(next_item)
        if not match:
            continue
        hed_tags.append(next_item)
        row_numbers.append(index)

    if not row_numbers:
        df = None
    elif not eligible_columns:
        df = pd.DataFrame({'row_number': row_numbers, 'HED_assembled': hed_tags})
    else:
        df = data_input.dataframe.iloc[row_numbers][eligible_columns].reset_index()
        df.rename(columns={'index': 'row_number'})
    return df


# def remove_defs(hed_strings):
#     """ This removes any def or Def-expand from a list of HedStrings.
#
#     Parameters:
#         hed_strings (list):  A list of HedStrings
#
#     Returns:
#         list: A list of the removed Defs.
#
#     """
#     def_groups = [[] for i in range(len(hed_strings))]
#     for index, hed in enumerate(hed_strings):
#         def_groups[index] = extract_defs(hed)
#     return def_groups
#
#
# def extract_defs(hed_string_obj):
#     """ This removes any def or Def-expand from a list of HedStrings.
#
#     Parameters:
#         hed_string_obj (HedString):  A HedString
#
#     Returns:
#         list: A list of the removed Defs.
#
#     Notes:
#         - the hed_string_obj passed in no longer has definitions.
#
#     """
#     to_remove = []
#     to_append = []
#     tuples = hed_string_obj.find_def_tags(recursive=True, include_groups=3)
#     for tup in tuples:
#         if len(tup[2].children) == 1:
#             to_append.append(tup[0])
#         else:
#             to_append.append(tup[2])
#         to_remove.append(tup[2])
#     hed_string_obj.remove(to_remove)
#     return to_append


def hed_to_str(contents, remove_parentheses=False):

    if contents is None:
        return ''
    if isinstance(contents, str):
        return contents
    if isinstance(contents, HedTag):
        return str(contents)
    if isinstance(contents, list):
        converted = [hed_to_str(element, remove_parentheses) for element in contents if element]
        return ",".join(converted)
    if not isinstance(contents, HedGroup):
        raise TypeError("ContentsWrongClass", "OnsetGroup excepts contents that can be converted to string.")
    if not remove_parentheses or len(contents.children) != 1:
        return str(contents)
    return _handle_remove(contents)


def _handle_remove(contents):
    if contents.is_group or isinstance(contents.children[0], HedTag):
        return str(contents.children[0])
    child = contents.children[0]
    if child.is_group and len(child.children) == 1:
        return str(child.children[0])
    return str(child)
