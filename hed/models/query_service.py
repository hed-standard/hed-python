import pandas as pd

from hed.models import QueryHandler


def get_query_handlers(queries, query_names=None):
    """ Returns a list of query handlers and names

    Parameters:
        queries (list):  A list of query strings or QueryHandler objects
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
        if isinstance(query, str):
            try:
                next_query = QueryHandler(query)
            except Exception:
                raise ValueError("BadQuery", f"Query [{index}]: {query} cannot be parsed")
        else:
            raise ValueError("BadQuery", f"Query [{index}]: {query} has a bad type")
        expression_parsers.append(next_query)
    return expression_parsers, query_names


def search_strings(hed_strings, queries, query_names):
    """ Returns a DataFrame of factors based on results of queries.

    Parameters:
        hed_strings (list):  A list of HedString objects (empty entries or None entries are 0's)
        queries (list):  A list of query strings or QueryHandler objects
        query_names (list): A list of column names for results of queries.

    Returns:
        DataFrame - containing the factor vectors with results of the queries

    :raises ValueError:
        - If query names are invalid or duplicated.
    """
    df_factors = pd.DataFrame(0, index=range(len(hed_strings)), columns=query_names)
    for parse_ind, parser in enumerate(queries):
        for index, next_item in enumerate(hed_strings):
            match = parser.search(next_item)
            if match:
                df_factors.at[index, query_names[parse_ind]] = 1
    return df_factors
