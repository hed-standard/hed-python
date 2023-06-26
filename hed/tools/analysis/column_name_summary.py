""" Summarizes the unique column names in a dataset. """

import json


class ColumnNameSummary:
    def __init__(self, name=''):
        self.name = name
        self.file_dict = {}
        self.unique_headers = []

    def update(self, name, columns):
        position = self.update_headers(columns)
        if name not in self.file_dict:
            self.file_dict[name] = position
        elif name in self.file_dict and position != self.file_dict[name]:
            raise ValueError("FileHasChangedColumnNames",
                             f"{name}: Summary has conflicting column names " +
                             f"Current: {str(columns)} Previous: {str(self.unique_headers[self.file_dict[name]])}")

    def update_headers(self, column_names):
        for index, item in enumerate(self.unique_headers):
            if item == column_names:
                return index
        self.unique_headers.append(column_names)
        return len(self.unique_headers) - 1

    def get_summary(self, as_json=False):
        patterns = [list() for element in self.unique_headers]
        for key, value in self.file_dict.items():
            patterns[value].append(key)
        column_headers = []
        for index in range(len(patterns)):
            column_headers.append({'Column names': self.unique_headers[index], 'Files': patterns[index]})
        summary = {"Summary name": self.name, "Columns": column_headers, "Number files": len(self.file_dict)}
        if as_json:
            return json.dumps(summary, indent=4)
        else:
            return summary
