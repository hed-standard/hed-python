import json
from hed.util.column_definition import ColumnDefinition
from hed.util.error_types import SidecarErrors
from hed.util.error_reporter import format_sidecar_error

class ColumnDefinitionGroup:
    """This stores column definitions, generally loaded from a single file."""
    def __init__(self, json_filename=None):
        self._json_filename = json_filename
        self._column_settings = {}
        self._validation_issues = {}
        if json_filename:
            self.add_json_file_defs(json_filename)

    def __iter__(self):
        return iter(self._column_settings.values())

    def save_as_json(self, save_filename):
        output_dict = {}
        for entry in self._column_settings.values():
            output_dict[entry.column_name] = entry._hed_dict
        with open(save_filename, "w") as fp:
            json.dump(output_dict, fp, indent=4)

    def add_json_file_defs(self, col_def_filename):
        try:
            with open(col_def_filename, "r") as fp:
                loaded_defs = json.load(fp)
                for col_def, col_dict in loaded_defs.items():
                    self._add_single_col_type(col_def, col_dict)
            self.save_as_json(col_def_filename + "test_json_out.json")

        except FileNotFoundError:
            self._validation_issues[col_def_filename] = format_sidecar_error(SidecarErrors.INVALID_FILENAME,
                                                                             filename=col_def_filename)
        except json.decoder.JSONDecodeError:
            self._validation_issues[col_def_filename] = format_sidecar_error(SidecarErrors.CANNOT_PARSE_JSON,
                                                                             filename=col_def_filename)

    @staticmethod
    def load_multiple_json_files(json_file_input_list):
        """This takes a list of filenames or ColumnDefinitionGroups and returns a list of ColumnDefinitionGroups."""
        if not isinstance(json_file_input_list, list):
            json_file_input_list = [json_file_input_list]

        loaded_files = []
        for json_file in json_file_input_list:
            if isinstance(json_file, str):
                json_file = ColumnDefinitionGroup(json_file)
            loaded_files.append(json_file)

        return loaded_files

    def hed_string_iter(self, include_position=False):
        """Returns all hed strings in the columns one by one.

           Returns a tuple of (string, position) if include_position is true.
           Pass position to set_hed_string to change one.
           """
        for key, entry in self._column_settings.items():
            for hed_string in entry.hed_string_iter(include_position):
                if include_position:
                    yield hed_string[0], (key, hed_string[1])
                else:
                    yield hed_string

    def set_hed_string(self, new_hed_string, position):
        """Position is the value returned from hed_string_iter.  Generally (column_name, category key)."""
        column_name, position = position
        entry = self._column_settings[column_name]
        entry.set_hed_string(new_hed_string, position)

    # Figure out later if we want support like this...
    # def add_value_column(self, column_name, hed):
    #     new_entry = {
    #         "HED": hed
    #     }
    #     new_entry = ColumnDefinition(new_entry, column_name, ColumnType.Value)
    #     self._column_settings[column_name] = column_entry
    #
    # def add_categorical_column(self, column_name, hed_category_dict):
    #     new_entry = {
    #         "HED": hed_category_dict
    #     }
    #     new_entry = ColumnDefinition(new_entry, column_name, ColumnType.Categorical)
    #     self._column_settings[column_name] = column_entry
    #
    # def add_attribute_columns(self, column_names):
    #     self._add_multiple_columns(column_names, ColumnType.Attribute)

    # def add_hedtag_columns(self, column_names):
    #     self._add_multiple_columns(column_names, ColumnType.HEDTags)
    #
    # def add_ignore_columns(self, column_names):
    #     self._add_multiple_columns(column_names, ColumnType.Ignore)

    def _add_multiple_columns(self, column_names, column_type):
        if isinstance(column_names, str):
            column_names = [column_names]
        for column_name in column_names:
            self._add_single_col_type(column_name, None, column_type)

    def _add_single_col_type(self, column_name, dict_for_entry, column_type=None):
        column_entry = ColumnDefinition(column_type, column_name, dict_for_entry)
        self._column_settings[column_name] = column_entry

    def get_validation_issues(self):
        return self._validation_issues

    def validate_entries(self, hed_dictionary=None):
        # If we already have an issue we either already validated, or have a file io error
        if not self._validation_issues:
            key_validation_issues = {}
            for column_entry in self:
                col_validation_issues = column_entry._validate_column_entry(hed_dictionary)
                if col_validation_issues:
                    if self._json_filename:
                        col_validation_issues = format_sidecar_error(SidecarErrors.SIDECAR_FILE_NAME,
                                                                     filename=self._json_filename) \
                                                + col_validation_issues
                    key_validation_issues[column_entry.column_name] = col_validation_issues

            self._validation_issues = key_validation_issues
        return self._validation_issues


if __name__ == '__main__':
    from hed.util.hed_dictionary import HedDictionary

    local_hed_xml = "examples/data/HED7.1.1.xml"
    hed_dictionary = HedDictionary(local_hed_xml)
    json_filename = "examples/data/both_types_events_errors.json"
    json_file = ColumnDefinitionGroup(json_filename)
    for column_def in json_file:
        for hed_string, position in column_def.hed_string_iter(include_position=True):
            new_hed_string = hed_string + "extra"
            column_def.set_hed_string(new_hed_string, position)
            print(hed_string)

    errors = json_file.validate_entries(hed_dictionary)
    for error in errors.values():
        for sub_error in error:
            print(sub_error["message"])

    # Alt syntax
    for hed_string, position in json_file.hed_string_iter(include_position=True):
        new_hed_string = hed_string + "extra2"
        json_file.set_hed_string(new_hed_string, position)
        print(hed_string)

    for hed_string in json_file.hed_string_iter():
        print(hed_string)
