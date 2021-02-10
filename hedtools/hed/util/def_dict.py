from hed.util.hed_string_delimiter import HedStringDelimiter
from hed.util.error_types import DefinitionErrors
from hed.util import error_reporter


class DefDict:
    """Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids style file might have many of these(one for each json dict, and another for the actual file)
    """
    DLABEL_ORG_KEY = 'Label-def'
    ELABEL_ORG_KEY = 'Label-exp'
    DLABEL_KEY = DLABEL_ORG_KEY.lower()
    ELABEL_KEY = ELABEL_ORG_KEY.lower()

    DEF_KEY = "definition"
    ORG_KEY = "organizational"

    def __init__(self, hed_schema=None):
        """
        Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids style file might have many of these(one for each json dict, and another for the actual file)
        Parameters
        ----------
        hed_schema : HedSchema, optional
            Used to determine where definition tags are in the schema.  This is technically optional, but
            only short form definition tags will work if this is absent.  This is also used to verify definitions
            are not already used as terms.
        """
        self._defs = {}

        if hed_schema:
            self._def_tag_versions = hed_schema.get_all_forms_of_tag(self.DEF_KEY)
            self._org_tag_versions = hed_schema.get_all_forms_of_tag(self.ORG_KEY)
            self._label_tag_versions = hed_schema.get_all_forms_of_tag(self.DLABEL_KEY)
            if not self._label_tag_versions:
                self._label_tag_versions = [self.DLABEL_KEY + "/"]
            self._short_tag_mapping = hed_schema.short_tag_mapping
        else:
            self._def_tag_versions = [self.DEF_KEY + "/"]
            self._org_tag_versions = [self.ORG_KEY + "/"]
            self._label_tag_versions = [self.DLABEL_KEY + "/"]
            self._short_tag_mapping = None

    def __iter__(self):
        return iter(self._defs.items())

    def check_for_definitions(self, hed_string, check_for_issues=True, error_handler=None):
        """
        Check a given hed string for definition tags, and add them to the dictionary if so.

        Parameters
        ----------
        hed_string : str
            A single hed string to gather definitions from
        check_for_issues: bool
            If we should return validation issues found.(note most issues will be checked for either way,
            they just won't be returned.)
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        ----------
        issues_list: None or [{}]
            A list of error objects containing warnings and errors related to definitions.
        """
        if self.DEF_KEY not in hed_string.lower():
            return []
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()

        validation_issues = []
        def_tag_versions = self._def_tag_versions
        org_tag_versions = self._org_tag_versions

        # This could eventually be replaced with another method as we only care about portions of the tags
        string_split = HedStringDelimiter(hed_string)
        for tag_group in string_split.tag_groups:
            org_tags = []
            def_tags = []
            group_tags = []
            for tag in tag_group:
                new_def_tag = self._check_tag_starts_with(tag, def_tag_versions)
                if new_def_tag:
                    def_tags.append(new_def_tag)
                    continue

                new_org_tag = self._check_tag_starts_with(tag, org_tag_versions)
                if new_org_tag:
                    org_tags.append(tag)
                    continue

                group_tags.append(tag)

            # Now validate to see if we have a definition.  We want 1 definition, and the other parts are optional.
            if not def_tags:
                # If we don't have at least one valid definition tag, just move on.  This is probably a tag with
                # the word definition somewhere else in the text.
                continue

            if len(def_tags) > 1:
                validation_issues += error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_DEF_TAGS,
                                                                           def_name=def_tags[0], tag_list=def_tags[1:])
                continue
            def_tag = def_tags[0]
            if len(org_tags) > 1:
                validation_issues += error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_ORG_TAGS,
                                                                           def_name=def_tag, tag_list=org_tags)
                continue
            if len(group_tags) > 1:
                validation_issues += error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                                           def_name=def_tag, tag_list=group_tags)
                continue

            org_tag = org_tags[0] if org_tags else None
            group_tag = group_tags[0] if group_tags else None

            if def_tag in self._defs:
                validation_issues += error_handler.format_definition_error(DefinitionErrors.DUPLICATE_DEFINITION,
                                                                           def_name=def_tag)
            if self._short_tag_mapping and def_tag.lower() in self._short_tag_mapping:
                validation_issues += error_handler.format_definition_error(DefinitionErrors.TAG_IN_SCHEMA,
                                                                           def_name=def_tag)

            self._defs[def_tag.lower()] = f"({self.ELABEL_ORG_KEY}/{def_tag}, {org_tag}, {group_tag})"

        if check_for_issues:
            return validation_issues

    @staticmethod
    def _check_tag_starts_with(hed_tag, possible_starts_with_list):
        """ Check if a given tag starts with a given string, and returns the tag with the prefix removed if it does.

        Parameters
        ----------
        hed_tag : str
            A single input tag
        possible_starts_with_list : list
            A list of strings to check as the prefix.
            Generally this will be all short/intermediate/long forms of a specific tag
            eg. ['definitional', 'informational/definitional', 'attribute/informational/definitional']
        Returns
        -------
            str: the tag without the removed prefix, or None
        """
        hed_tag_lower = hed_tag.lower()
        for start_with_version in possible_starts_with_list:
            if hed_tag_lower.startswith(start_with_version):
                found_tag = hed_tag[len(start_with_version):]
                return found_tag
        return None
