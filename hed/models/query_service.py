""" Functions to get and use HED queries. """
from typing import Union

import pandas as pd

from hed.models import QueryHandler


def get_query_handlers(queries, query_names=None) -> tuple[list[Union[QueryHandler, None]], list[Union[QueryHandler, None]], list]:
    """ Return a list of query handlers, query names, and issues if any.

    Parameters:
        queries (list):  A list of query strings.
        query_names (list or None): A list of column names for results of queries. If missing --- query_1, query_2, etc.

    Returns:
        tuple: A tuple containing:
            - list: QueryHandlers for successfully parsed queries or None.
            - list: str names to assign to results of the queries or None.
            - list: issues if any of the queries could not be parsed or other errors occurred.

    """
    if not queries:
        return None, None, ["EmptyQueries: The queries list must not be empty"]
    elif isinstance(queries, str):
        queries = [queries]
    expression_parsers = [None] * len(queries)
    issues = []
    if not query_names:
        query_names = [f"query_{index}" for index in range(len(queries))]

    if len(queries) != len(query_names):
        issues.append(f"QueryNamesLengthBad: The query_names length {len(query_names)} must be empty or equal " +
                      f"to the queries length {len(queries)}.")
    elif len(set(query_names)) != len(query_names):
        issues.append(f"DuplicateQueryNames: The query names {str(query_names)} list has duplicates")

    for index, query in enumerate(queries):
        try:
            expression_parsers[index] = QueryHandler(query)
        except Exception:
            issues.append(f"[BadQuery {index}]: {query} cannot be parsed")
    return expression_parsers, query_names, issues


def search_hed_objs(hed_objs, queries, query_names) -> pd.DataFrame:
    """ Return a DataFrame of factors based on results of queries.

    Parameters:
        hed_objs (list):  A list of HedString objects (empty entries or None entries are 0's
        queries (list):  A list of query strings or QueryHandler objects.
        query_names (list): A list of column names for results of queries.

    Returns:
        pd.DataFrame: Contains the factor vectors with results of the queries.

    Raises:
        ValueError: If query names are invalid or duplicated.
    """
    df_factors = pd.DataFrame(0, index=range(len(hed_objs)), columns=query_names)
    for parse_ind, parser in enumerate(queries):
        for index, next_item in enumerate(hed_objs):
            if next_item:
                match = parser.search(next_item)
                if match:
                    df_factors.at[index, query_names[parse_ind]] = 1
    return df_factors
