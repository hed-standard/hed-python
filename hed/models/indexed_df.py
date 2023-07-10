from functools import partial
import pandas as pd

from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.models.hed_string import HedString
from hed.models.definition_dict import DefinitionDict
from hed.models import df_util


class IndexedDF:
    def __init__(self, tabular_input, sidecar, hed_schema):
        self._hed_strings = df_util.get_assembled(tabular_input, sidecar, hed_schema, expand_defs=True)
    #     self._df = df
    #     self._index = self._create_index(df)
    #     self._hed_strings = df_util.get_assembled()
    #
    # def create_index_from_hed_strings(self):
    #
    #
    #
    # @staticmethod
    # def find_rows_for_strings(self, df, search_strings):
    #     cache = {}
    #     for string in search_strings:
    #         if string not in cache:
    #             print("Hi")
    #             parts = string.split('/')
    #             for i in range(1, len(parts) + 1):
    #                 part = '/'.join(parts[:i])
    #                 if part not in cache:
    #                     if i == 1:
    #                         searchable_rows = df
    #                     else:
    #                         searchable_rows = df[cache['/'.join(parts[:i - 1])]]
    #                     cache[part] = searchable_rows[searchable_rows.str.contains(part)].index.to_list()
    #         # cache[string] = cache[part]  # Assign the cache result to the complete string
    #
    #     return cache
