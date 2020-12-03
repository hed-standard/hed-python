import json
import copy
from hed.util.column_settings import ColumnDefinition
from hed.util.column_settings import ColumnType
from hed.util.error_types import SidecarErrors
from hed.util.error_reporter import format_sidecar_error

class ColumnDefinitionGroup:
    """This stores column definitions, generally loaded from a single file."""
    def __init__(self, json_filename=None):
        self._json_filename = json_filename
        self._column_settings = {}
        self._key_validation_issues = {}
        if json_filename:
            self.add_json_file_events(json_filename)

    def __iter__(self):
        return iter(self._column_settings.values())

    def save_as_json(self, save_filename):
        output_dict = {}
        for entry in self._column_settings.values():
            # Add type information to dict for saving.
            single_entry_dict = copy.copy(entry._hed_dict)
            single_entry_dict["type"] = entry.type.value
            output_dict[entry.name] = single_entry_dict

        with open(save_filename, "w") as fp:
            json.dump(output_dict, fp, indent=4)

    def add_json_file_events(self, event_filename):
        try:
            with open(event_filename, "r") as fp:
                loaded_events = json.load(fp)
                for event, event_dict in loaded_events.items():
                    # remove type from dictoinary and pass to structure if it exists.
                    type = ColumnType(event_dict.pop("type", None))
                    self._add_single_event_type(event, event_dict, type)

        except FileNotFoundError:
            self._key_validation_issues[event_filename] = format_sidecar_error(SidecarErrors.INVALID_FILENAME,
                                                                               filename=event_filename)
        except json.decoder.JSONDecodeError:
            self._key_validation_issues[event_filename] = format_sidecar_error(SidecarErrors.CANNOT_PARSE_JSON,
                                                                               filename=event_filename)

    def add_value_column(self, name, hed):
        new_entry = {
            "HED": hed
        }
        new_entry = ColumnDefinition._create_event_entry(new_entry, name, ColumnType.Value)
        self._add_column_settings(new_entry)

    def add_categorical_column(self, name, hed_category_dict):
        new_entry = {
            "HED": hed_category_dict
        }
        new_entry = ColumnDefinition._create_event_entry(new_entry, name, ColumnType.Categorical)
        self._add_column_settings(new_entry)

    def add_attribute_columns(self, column_names):
        self._add_multiple_columns(column_names, ColumnType.Attribute)

    def add_hedtag_columns(self, column_names):
        self._add_multiple_columns(column_names, ColumnType.HEDTags)

    def add_ignore_columns(self, column_names):
        self._add_multiple_columns(column_names, ColumnType.Ignore)

    def _add_multiple_columns(self, column_names, column_type):
        if isinstance(column_names, str):
            column_names = [column_names]
        for column_name in column_names:
            new_entry = ColumnDefinition._create_event_entry(None, column_name, column_type)
            self._add_column_settings(new_entry)

    def _add_column_settings(self, new_column_entry):
        column_name = new_column_entry.name
        self._column_settings[column_name] = new_column_entry


    def _add_single_event_type(self, column_name, dict_for_entry, column_type=None):
        column_entry = ColumnDefinition._create_event_entry(dict_for_entry, column_name, column_type)
        self._column_settings[column_name] = column_entry
        return True

    def validate_entries(self, hed_dictionary=None):
        key_validation_issues = {}
        for column_entry in self:
            event_validation_issues = column_entry._validate_event_entry(hed_dictionary)
            if event_validation_issues and self._json_filename:
                event_validation_issues = format_sidecar_error(SidecarErrors.SIDECAR_FILE_NAME,
                                                               filename=self._json_filename) \
                                          + event_validation_issues
                key_validation_issues[column_entry.name] = event_validation_issues

        return key_validation_issues