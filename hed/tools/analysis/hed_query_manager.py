# from hed.models.expression_parser import TagExpressionParser
#
#
# class HedQuery:
#     def __init__(self, query):
#         self.name = query['name']
#         self.query_type = query['query_type']
#         self.query_str = query['query_str']
#         self.expression = TagExpressionParser(self.query_str)
#
#     def evaluate(self, hed_string_obj):
#         return self.expression.search_hed_string(hed_string_obj)
#
#
# class HedQueryManager:
#
#     def __init__(self, query_list):
#         self.query_list = query_list
#
#     def get_column_names(self):
#         columns = ['cond']*len(self.query_list)
#         for index, query in enumerate(self.query_list):
#             columns[index] = query.name
#         return columns
#
#     def parse(self, hed_string_obj):
#         matches = [0] * len(self.query_list)
#         for index, query in enumerate(self.query_list):
#             if query.evaluate(hed_string_obj):
#                 matches[index] = 1
#         return matches
#
#
# # if __name__ == '__main__':
# #     qlist = [HedQuery({'name': 'cond_1', 'query_type': 'condition', 'query_str': 'Condition-variable'}),
# #              HedQuery({'name': 'tag_1', 'query_type': 'get_tag', 'query_str': 'Sensory-presentation'})]
# #
# #     schema = load_schema_version(xml_version="8.0.0")
# #     test_strings = [HedString('Condition-variable/Test-cond', hed_schema=schema),
# #                     HedString('Visual-presentation', hed_schema=schema),
# #                     HedString('Agent-action, (Move, Hand)', hed_schema=schema)]
# #     q_parser = HedQueryManager(qlist)
# #     col_names = q_parser.get_column_names()
# #     print(f"Column names:{str(col_names)}")
# #
# #     result = [None]*len(test_strings)
# #     for index, obj in enumerate(test_strings):
# #         result[index] = q_parser.parse(obj)
# #
# #     df = pd.DataFrame(result, columns=col_names)
