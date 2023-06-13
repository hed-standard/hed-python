""" Utilities for assembly, analysis, and searching. """

import pandas as pd
from hed.models.tabular_input import TabularInput
from hed.tools.util.data_util import separate_values
from hed.models.hed_tag import HedTag
from hed.models.hed_group import HedGroup
from hed.models import df_util
from hed.models import QueryParser


def assemble_hed(data_input, sidecar, schema, columns_included=None, expand_defs=False):
    """ Return assembled HED annotations in a dataframe.

    Parameters:
        data_input (TabularInput): The tabular input file whose HED annotations are to be assembled.
        sidecar (Sidecar):  Sidecar with definitions.
        schema (HedSchema):  Hed schema
        columns_included (list or None):  A list of additional column names to include.
            If None, only the list of assembled tags is included.
        expand_defs (bool): If True, definitions are expanded when the events are assembled.

    Returns:
        DataFrame or None: A DataFrame with the assembled events.
        dict: A dictionary with definition names as keys and definition content strings as values.
    """

    eligible_columns, missing_columns = separate_values(list(data_input.dataframe.columns), columns_included)
    hed_string_list = data_input.series_a
    definitions = sidecar.get_def_dict(hed_schema=schema)
    if expand_defs:
        df_util.expand_defs(hed_string_list, schema, definitions)
    # Keep in mind hed_string_list is now a Series.  The rest of the function should probably
    # also be modified

    # hed_obj_list, defs = get_assembled(data_input, sidecar, schema, extra_def_dicts=None, join_columns=True,
    #                                    shrink_defs=False, expand_defs=True)
    # hed_string_list = [str(hed) for hed in hed_obj_list]
    if not eligible_columns:
        df = pd.DataFrame({"HED_assembled": hed_string_list})
    else:
        df = data_input.dataframe[eligible_columns].copy(deep=True)
        df['HED_assembled'] = hed_string_list
    # definitions = data_input.get_definitions().gathered_defs
    return df, definitions


def get_expression_parsers(queries, query_names=None):
    """ Returns a list of expression parsers and query_names.

        Parameters:
            queries (list):  A list of query strings or QueryParser objects
            query_names (list): A list of column names for results of queries. If missing --- query_1, query_2, etc.

        Returns:
            DataFrame - containing the search strings

        :raises ValueError:
            - If query names are invalid or duplicated.

        """
    expression_parsers = []
    if not query_names:
        query_names = [f"query_{index}" for index in range(len(queries))]
    elif len(queries) != len(query_names):
        raise ValueError("QueryNamesLengthBad",
                         f"The query_names length {len(query_names)} must be empty or equal" +
                         f"to the queries length {len(queries)}.")
    elif len(set(query_names)) != len(query_names):
        raise ValueError("DuplicateQueryNames", f"The query names {str(query_names)} list has duplicates")
    for index, query in enumerate(queries):
        if not query:
            raise ValueError("BadQuery", f"Query [{index}]: {query} cannot be empty")
        elif isinstance(query, str):
            try:
                next_query = QueryParser(query)
            except Exception:
                raise ValueError("BadQuery", f"Query [{index}]: {query} cannot be parsed")
        else:
            next_query = query
        expression_parsers.append(next_query)
    return expression_parsers, query_names


def search_strings(hed_strings, queries, query_names=None):
    """ Returns a DataFrame of factors based on results of queries.

    Parameters:
        hed_strings (list):  A list of HedString objects (empty entries or None entries are 0's)
        queries (list):  A list of query strings or QueryParser objects
        query_names (list): A list of column names for results of queries. If missing --- query_1, query_2, etc.

    Returns:
        DataFrame - containing the factor vectors with results of the queries

    :raises ValueError:
        - If query names are invalid or duplicated.
            
    """

    expression_parsers, query_names = get_expression_parsers(queries, query_names=query_names)
    df_factors = pd.DataFrame(0, index=range(len(hed_strings)), columns=query_names)
    for parse_ind, parser in enumerate(expression_parsers):
        for index, next_item in enumerate(hed_strings):
            match = parser.search(next_item)
            if match:
                df_factors.at[index, query_names[parse_ind]] = 1
    return df_factors

# def get_assembled_strings(table, hed_schema=None, expand_defs=False):
#     """ Return HED string objects for a tabular file.
# 
#     Parameters:
#         table (TabularInput): The input file to be searched.
#         hed_schema (HedSchema or HedschemaGroup): If provided the HedStrings are converted to canonical form.
#         expand_defs (bool): If True, definitions are expanded when the events are assembled.
# 
#     Returns:
#         list: A list of HedString or HedStringGroup objects.
# 
#     """
#     hed_list = list(table.iter_dataframe(hed_ops=[hed_schema], return_string_only=True,
#                                          expand_defs=expand_defs, remove_definitions=True))
#     return hed_list
# 

# def search_tabular(data_input, sidecar, hed_schema, query, extra_def_dicts=None, columns_included=None):
#     """ Return a dataframe with results of query.
# 
#     Parameters:
#         data_input (TabularInput): The tabular input file (e.g., events) to be searched.
#         hed_schema (HedSchema or HedSchemaGroup):  The schema(s) under which to make the query.
#         query (str or list):     The str query or list of string queries to make.
#         columns_included (list or None):  List of names of columns to include
# 
#     Returns:
#         DataFrame or None: A DataFrame with the results of the query or None if no events satisfied the query.
# 
#     """
# 
#     eligible_columns, missing_columns = separate_values(list(data_input.dataframe.columns), columns_included)
#     hed_list, definitions = df_util.get_assembled(data_input, sidecar, hed_schema, extra_def_dicts=None, join_columns=True,
#                                                   shrink_defs=False, expand_defs=True)
#     expression = QueryParser(query)
#     hed_tags = []
#     row_numbers = []
#     for index, next_item in enumerate(hed_list):
#         match = expression.search(next_item)
#         if not match:
#             continue
#         hed_tags.append(next_item)
#         row_numbers.append(index)
# 
#     if not row_numbers:
#         df = None
#     elif not eligible_columns:
#         df = pd.DataFrame({'row_number': row_numbers, 'HED_assembled': hed_tags})
#     else:
#         df = data_input.dataframe.iloc[row_numbers][eligible_columns].reset_index()
#         df.rename(columns={'index': 'row_number'})
#     return df


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
