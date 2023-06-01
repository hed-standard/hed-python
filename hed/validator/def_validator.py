from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.definition_dict import DefinitionDict
from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler


class DefValidator(DefinitionDict):
    """ Handles validating Def/ and Def-expand/.

    """
    def __init__(self, def_dicts=None, hed_schema=None):
        """ Initialize for definitions in hed strings.

        Parameters:
            def_dicts (list or DefinitionDict or str): DefinitionDicts containing the definitions to pass to baseclass

        """
        super().__init__(def_dicts, hed_schema=hed_schema)

    def validate_def_tags(self, hed_string_obj, tag_validator=None):
        """ Validate Def/Def-Expand tags.

        Parameters:
            hed_string_obj (HedString): The hed string to process.
            tag_validator (TagValidator): Used to validate the placeholder replacement.
        Returns:
            list: Issues found related to validating defs. Each issue is a dictionary.
        """
        hed_string_lower = hed_string_obj.lower()
        if self._label_tag_name not in hed_string_lower:
            return []

        def_issues = []
        # We need to check for labels to expand in ALL groups
        for def_tag, def_expand_group, def_group in hed_string_obj.find_def_tags(recursive=True):
            def_issues += self._validate_def_contents(def_tag, def_expand_group, tag_validator)

        return def_issues

    def _validate_def_contents(self, def_tag, def_expand_group, tag_validator):
        """ Check for issues with expanding a tag from Def to a Def-expand tag group

        Parameters:
            def_tag (HedTag): Source hed tag that may be a Def or Def-expand tag.
            def_expand_group (HedGroup or HedTag):
            Source group for this def-expand tag.  Same as def_tag if this is not a def-expand tag.
            tag_validator (TagValidator): Used to validate the placeholder replacement.
        Returns:
            issues
        """
        def_issues = []
        is_def_expand_tag = def_expand_group != def_tag
        is_label_tag = def_tag.extension
        placeholder = None
        found_slash = is_label_tag.find("/")
        if found_slash != -1:
            placeholder = is_label_tag[found_slash + 1:]
            is_label_tag = is_label_tag[:found_slash]

        label_tag_lower = is_label_tag.lower()
        def_entry = self.defs.get(label_tag_lower)
        if def_entry is None:
            error_code = ValidationErrors.HED_DEF_UNMATCHED
            if is_def_expand_tag:
                error_code = ValidationErrors.HED_DEF_EXPAND_UNMATCHED
            def_issues += ErrorHandler.format_error(error_code, tag=def_tag)
        else:
            def_tag_name, def_contents = def_entry.get_definition(def_tag, placeholder_value=placeholder,
                                                                  return_copy_of_tag=True)
            if def_tag_name:
                if is_def_expand_tag and def_expand_group != def_contents:
                    def_issues += ErrorHandler.format_error(ValidationErrors.HED_DEF_EXPAND_INVALID,
                                                            tag=def_tag, actual_def=def_contents,
                                                            found_def=def_expand_group)
                if def_entry.takes_value and tag_validator:
                    placeholder_tag = def_contents.get_first_group().find_placeholder_tag()
                    error_code = ValidationErrors.DEF_INVALID
                    if is_def_expand_tag:
                        error_code = ValidationErrors.DEF_EXPAND_INVALID
                    if placeholder_tag.is_unit_class_tag():
                        def_issues += tag_validator.check_tag_unit_class_units_are_valid(placeholder_tag,
                                                                                         report_as=def_tag,
                                                                                         error_code=error_code)
                    elif placeholder_tag.is_value_class_tag():
                        def_issues += tag_validator.check_tag_value_class_valid(placeholder_tag,
                                                                                report_as=def_tag,
                                                                                error_code=error_code)

            elif def_entry.takes_value:
                error_code = ValidationErrors.HED_DEF_VALUE_MISSING
                if is_def_expand_tag:
                    error_code = ValidationErrors.HED_DEF_EXPAND_VALUE_MISSING
                def_issues += ErrorHandler.format_error(error_code, tag=def_tag)
            else:
                error_code = ValidationErrors.HED_DEF_VALUE_EXTRA
                if is_def_expand_tag:
                    error_code = ValidationErrors.HED_DEF_EXPAND_VALUE_EXTRA
                def_issues += ErrorHandler.format_error(error_code, tag=def_tag)

        return def_issues