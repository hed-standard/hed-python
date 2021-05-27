from hed.util.hed_string import HedString, HedTag, HedGroup
from hed.util.error_types import DefinitionErrors
from hed.util import error_reporter


class DefTagNames:
    """The source names for definitions, def labels, and expanded labels"""
    DLABEL_ORG_KEY = 'Def/'
    ELABEL_ORG_KEY = 'Def-expand/'
    DEF_ORG_KEY = "Definition/"
    DLABEL_KEY = DLABEL_ORG_KEY.lower()
    ELABEL_KEY = ELABEL_ORG_KEY.lower()
    DEF_KEY = DEF_ORG_KEY.lower()


class DefEntry:
    def __init__(self, name, contents_string, takes_value):
        """Contains info for a single definition tag

        Parameters
        ----------
        name : str
            The label portion of this name(not including definition/)
        contents_string: str
            The contents of this definition
        takes_value : bool
            If True, expects ONE tag to have a single # sign in it.
        """
        self.name = name
        self.contents = contents_string
        self.takes_value = takes_value

    def get_definition(self, placeholder_value=None):
        if self.takes_value == (placeholder_value is None):
            return None

        output_contents = None
        name = self.name
        if self.contents:
            hed_string = self.contents
            if placeholder_value:
                hed_string = hed_string.replace("#", placeholder_value)
                name = f"{name}/{placeholder_value}"

            output_contents = HedString.split_hed_string_into_groups(hed_string)

        # Possibly update this to properly point to the original def tag
        def_tag = HedTag(f"{DefTagNames.ELABEL_ORG_KEY}{name}", span=(0, len(f"{DefTagNames.ELABEL_ORG_KEY}{name}")))
        if output_contents:
            return [def_tag, output_contents]
        else:
            return [def_tag]


class DefDict:
    """Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids style file might have many of these(one for each json dict, and another for the actual file)
    """
    def __init__(self):
        """
        Class responsible for gathering and storing a group of definitions to be considered a single source.

        A bids style file might have many of these(one for each json dict, and another for the actual file)
        Parameters
        ----------
        """
        self._defs = {}

        # if hed_schema:
        #     self._def_tag_versions = hed_schema.get_all_forms_of_tag(DefTagNames.DEF_KEY)
        #     self._label_tag_versions = hed_schema.get_all_forms_of_tag(DefTagNames.DLABEL_KEY)
        #     if not self._label_tag_versions:
        #         self._label_tag_versions = [DefTagNames.DLABEL_KEY + "/"]
        #     self._short_tag_mapping = hed_schema.short_tag_mapping
        # else:
        #     self._def_tag_versions = [DefTagNames.DEF_KEY + "/"]
        #     self._label_tag_versions = [DefTagNames.DLABEL_KEY + "/"]
        #     self._short_tag_mapping = None

    def __iter__(self):
        return iter(self._defs.items())

    def check_for_definitions(self, hed_string_obj, check_for_issues=True, error_handler=None):
        """
        Check a given hed string for definition tags, and add them to the dictionary if so.

        Parameters
        ----------
        hed_string_obj : HedString
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
        if DefTagNames.DEF_KEY not in hed_string_obj.lower():
            return []
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()

        validation_issues = []
        for tag_group in hed_string_obj.get_all_groups():
            def_tags = []
            group_tags = []
            other_tags = []
            for tag_or_group in tag_group.get_direct_children():
                if isinstance(tag_or_group, HedGroup):
                    group_tags.append(tag_or_group)
                    continue
                else:
                    new_def_tag = self._check_tag_starts_with(str(tag_or_group), DefTagNames.DEF_KEY)
                    if new_def_tag:
                        def_tags.append((tag_or_group, new_def_tag))
                        continue

                other_tags.append(tag_or_group)

            # Now validate to see if we have a definition.  We want 1 definition, and the other parts are optional.
            if not def_tags:
                # If we don't have at least one valid definition tag, just move on.  This is probably a tag with
                # the word definition somewhere else in the text.
                continue

            if len(def_tags) > 1:
                validation_issues += error_handler.format_error(DefinitionErrors.WRONG_NUMBER_DEF_TAGS,
                                                                def_name=def_tags[0][1],
                                                                tag_list=[tag[0] for tag in def_tags[1:]])
                continue
            def_tag, def_tag_name = def_tags[0]
            if len(group_tags) > 1:
                validation_issues += error_handler.format_error(DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                                def_name=def_tag_name, tag_list=group_tags + other_tags)
                continue
            if len(other_tags) > 0:
                validation_issues += error_handler.format_error(DefinitionErrors.WRONG_NUMBER_GROUP_TAGS,
                                                                def_name=def_tag_name, tag_list=other_tags + group_tags)
                continue

            group_tag = group_tags[0] if group_tags else None

            def_takes_value = def_tag_name.lower().endswith("/#")
            if def_takes_value:
                def_tag_name = def_tag_name[:-len("/#")]

            def_tag_lower = def_tag_name.lower()
            if "/" in def_tag_lower or "#" in def_tag_lower:
                validation_issues += error_handler.format_error(DefinitionErrors.INVALID_DEF_EXTENSION,
                                                                def_name=def_tag_name)
                continue

            if def_tag_lower in self._defs:
                validation_issues += error_handler.format_error(DefinitionErrors.DUPLICATE_DEFINITION,
                                                                def_name=def_tag_name)
                continue

            # Todo: restore this functionality or add it elsewhere
            # if self._short_tag_mapping and def_tag_lower in self._short_tag_mapping:
            #     validation_issues += error_handler.format_error(DefinitionErrors.TAG_IN_SCHEMA,
            #                                                                def_name=def_tag_name)

            # Verify placeholders here.
            placeholder_tags = []
            if group_tag:
                for tag in group_tag.get_all_tags():
                    if "#" in str(tag):
                        placeholder_tags.append(tag)

            if (len(placeholder_tags) == 1) != def_takes_value:
                validation_issues += \
                    error_handler.format_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                               def_name=def_tag_name, tag_list=placeholder_tags,
                                               expected_count=1 if def_takes_value else 0)
                continue

            self._defs[def_tag_lower] = DefEntry(name=def_tag_name, contents_string=str(group_tag),
                                                 takes_value=def_takes_value)

        if check_for_issues:
            return validation_issues

    @staticmethod
    def _check_tag_starts_with(hed_tag, target_tag_short_name):
        """ Check if a given tag starts with a given string, and returns the tag with the prefix removed if it does.

        Parameters
        ----------
        hed_tag : str
            A single input tag
        target_tag_short_name : str
            The string to match eg find target_tag_short_name in hed_tag
        Returns
        -------
            str: the tag without the removed prefix, or None
        """
        hed_tag_lower = hed_tag.lower()
        found_index = hed_tag_lower.find(target_tag_short_name)

        if found_index == -1:
            return None

        if found_index == 0 or hed_tag_lower[found_index - 1] == "/":
            return hed_tag[found_index + len(target_tag_short_name):]
        return None
