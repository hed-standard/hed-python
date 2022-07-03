from hed.models import HedString, TagExpressionParser
from hed.schema import load_schema_version
import pandas as pd


class Query:
    def __init__(self, query):
        self.name = query['name']
        self.query_type = query['query_type']
        self.query_str = query['query_str']
        self.expression = TagExpressionParser(self.query_str)

    def evaluate(self, hed_string_obj):
        return self.expression.search_hed_string(hed_string_obj)


class QueryParser:

    def __init__(self, query_list):
        self.query_list = query_list

    def get_column_names(self):
        columns = ['cond']*len(self.query_list)
        for index, query in enumerate(self.query_list):
            columns[index] = query.name
        return columns

    def parse(self, hed_string_obj):
        matches = [0] * len(self.query_list)
        for index, query in enumerate(self.query_list):
            if query.evaluate(hed_string_obj):
                matches[index] = 1
        return matches



# def get_design(hed_list, definitions, hed_schema, query_parser):
#     """ Return a dataframe with results of query.
#
#     Args:
#         data_input (TabularInput): The tabular input file (e.g., events) to be searched.
#         hed_schema (HedSchema or HedSchemaGroup):  The schema(s) under which to make the query.
#         query (str):     The str query to make.
#         columns_included (list or None):  List of names of columns to include
#
#     Returns:
#         DataFrame or None: A DataFrame with the results of the query or None if no events satisfied the query.
#
#     """
#
#     df_0 = pd.DataFrame(0, index=range(len(hed_list)), columns=range(2))
#     for index, next_item in enumerate(hed_list):
#         match = query_parser.search_hed_string(next_item)
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

if __name__ == '__main__':
    qlist = [Query({'name': 'cond_1', 'query_type': 'condition', 'query_str': 'Condition-variable'}),
             Query({'name': 'tag_1', 'query_type': 'get_tag', 'query_str': 'Sensory-presentation'})]

    schema = load_schema_version(xml_version="8.0.0")
    test_strings = [HedString('Condition-variable/Test-cond', hed_schema=schema),
                    HedString('Visual-presentation', hed_schema=schema),
                    HedString('Agent-action, (Move, Hand)', hed_schema=schema)]
    q_parser = QueryParser(qlist)
    col_names = q_parser.get_column_names()
    print(f"Column names:{str(col_names)}")

    result = [None]*len(test_strings)
    for index, obj in enumerate(test_strings):
        result[index] = q_parser.parse(obj)

    df = pd.DataFrame(result, columns=col_names)
    print("toHere")
