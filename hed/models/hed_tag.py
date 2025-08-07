""" A single HED tag. """
from __future__ import annotations
from typing import Union
from hed.schema.hed_schema_constants import HedKey
import copy
from hed.models.model_constants import DefTagNames


class HedTag:
    """ A single HED tag.

    Notes:
        - HedTag is a smart class in that it keeps track of its original value and positioning
          as well as pointers to the relevant HED schema information, if relevant.

    """

    def __init__(self, hed_string, hed_schema, span=None, def_dict=None):
        """ Creates a HedTag.

        Parameters:
            hed_string (str): Source HED string for this tag.
            hed_schema (HedSchema): A parameter for calculating canonical forms on creation.
            span  (int, int): The start and end indexes of the tag in the hed_string.
            def_dict (DefinitionDict or None): The def dict to use to identify def/def expand tags.
        """
        self._hed_string = hed_string
        if span is None:
            span = (0, len(hed_string))
        # This is the span into the original HED string for this tag
        self.span = span

        # If this is present, use this as the org tag for most purposes.
        # This is not generally used anymore, but you can use it to replace a tag in place.
        self._tag = None

        self._namespace = self._get_schema_namespace(self.org_tag)

        # This is the schema this tag was converted to.
        self._schema = None
        self._schema_entry = None

        self._extension_value = ""
        self._parent = None

        self._expandable = None
        self._expanded = False

        self.tag_terms = None  # tuple of all the terms in this tag Lowercase.
        self._calculate_to_canonical_forms(hed_schema)

        self._def_entry = None
        if def_dict:
            if self.short_base_tag in {DefTagNames.DEF_KEY, DefTagNames.DEF_EXPAND_KEY}:
                self._def_entry = def_dict.get_definition_entry(self)

    def copy(self) -> "HedTag":
        """ Return a deep copy of this tag.

        Returns:
            HedTag: The copied group.

        """
        save_parent = self._parent
        self._parent = None
        return_copy = copy.deepcopy(self)
        self._parent = save_parent
        return return_copy

    @property
    def schema_namespace(self) -> str:
        """ Library namespace for this tag if one exists.

        Returns:
            str: The library namespace, including the colon.

        """
        return self._namespace

    @property
    def short_tag(self) -> str:
        """ Short form including value or extension.

        Returns:
            str: The short form of the tag, including value or extension.

        """
        if self._schema_entry:
            return f"{self._namespace}{self._schema_entry.short_tag_name}{self._extension_value}"

        return str(self)

    @property
    def base_tag(self) -> str:
        """ Long form without value or extension.

        Returns:
            str: The long form of the tag, without value or extension.
        """
        if self._schema_entry:
            return self._schema_entry.long_tag_name
        return str(self)

    @property
    def short_base_tag(self) -> str:
        """ Short form without value or extension.

        Returns:
            str: The short non-extension port of a tag.

        Notes:
            - ParentNodes/Def/DefName would return just "Def".

        """
        if self._schema_entry:
            return self._schema_entry.short_tag_name
        return str(self)

    @short_base_tag.setter
    def short_base_tag(self, new_tag_val):
        """ Change base tag, leaving extension or value.

        Parameters:
            new_tag_val (str): The new short_base_tag for this tag.

        Raises:
            ValueError: If the tag wasn't already identified.

        Note:
            - Generally this is used to swap def to def-expand.
        """
        if self._schema_entry:
            tag_entry = None
            if self._schema:
                if self.is_takes_value_tag():
                    new_tag_val = new_tag_val + "/#"
                tag_entry = self._schema.get_tag_entry(new_tag_val, schema_namespace=self.schema_namespace)

            self._schema_entry = tag_entry
        else:
            raise ValueError("Cannot set unidentified tags")

    @property
    def org_base_tag(self) -> str:
        """ Original form without value or extension.

        Returns:
            str: The original form of the tag, without value or extension.

        Notes:
            - Warning: This could be empty if the original tag had a name_prefix prepended.
              e.g. a column where "Label/" is prepended, thus the column value has zero base portion.
        """
        if self._schema_entry:
            extension_len = len(self._extension_value)
            if not extension_len:
                return self.tag

            org_len = len(self.tag)
            if org_len == extension_len:
                return ""

            return self.tag[:org_len - extension_len]
        return str(self)

    def tag_modified(self) -> bool:
        """ Return True if tag has been modified from original.

        Returns:
            bool: Return True if the tag is modified.

        Notes:
            - Modifications can include adding a column name_prefix.

        """
        return bool(self._tag)

    @property
    def tag(self) -> str:
        """ Returns the tag or the original tag if no user form set.

        Returns:
            str: The custom set user form of the tag.

        """
        if self._tag:
            return self._tag

        return self.org_tag

    @tag.setter
    def tag(self, new_tag_val):
        """ Allow you to overwrite the tag output text.

        Parameters:
            new_tag_val (str): New (implicitly long form) of tag to set.

        Notes:
            - You probably don't actually want to call this.
        """
        self._tag = new_tag_val
        self._schema_entry = None
        self._calculate_to_canonical_forms(self._schema)

    @property
    def extension(self) -> str:
        """ Get the extension or value of tag.

            Generally this is just the portion after the last slash.
            Returns an empty string if no extension or value.

        Returns:
            str: The tag name.

        Notes:
            - This tag must have been computed first.

        """
        if self._extension_value:
            return self._extension_value[1:]

        return ""

    @extension.setter
    def extension(self, x):
        self._extension_value = f"/{x}"

    @property
    def long_tag(self) -> str:
        """ Long form including value or extension.

        Returns:
            str: The long form of this tag.

        """
        if self._schema_entry:
            return f"{self._namespace}{self._schema_entry.long_tag_name}{self._extension_value}"
        return str(self)

    @property
    def org_tag(self) -> str:
        """ Return the original unmodified tag.

        Returns:
            str: The original unmodified tag.

        """
        return self._hed_string[self.span[0]:self.span[1]]

    @property
    def expanded(self) -> bool:
        """Return if this is currently expanded or not.

           Will always be False unless expandable is set.  This is primarily used for Def/Def-expand tags at present.

        Returns:
            bool: True if this is currently expanded.
        """
        return self._expanded

    @property
    def expandable(self) -> Union["HedGroup", "HedTag", None]:
        """Return what this expands to.

           This is primarily used for Def/Def-expand tags at present.

           Lazily set the first time it's called.

        Returns:
            Union[HedGroup,HedTag,None]: Returns the expanded form of this tag.
        """
        if self._expandable is None and self._def_entry:
            save_parent = self._parent
            tag_label, _, placeholder = self.extension.partition('/')

            def_contents = self._def_entry.get_definition(self, placeholder_value=placeholder)
            self._parent = save_parent
            if def_contents is not None:
                self._expandable = def_contents
                self._expanded = self.short_base_tag == DefTagNames.DEF_EXPAND_KEY
        return self._expandable

    def is_column_ref(self) -> bool:
        """ Return if this tag is a column reference from a sidecar.

            You should only see these if you are directly accessing sidecar strings, tools should remove them otherwise.

        Returns:
            bool: True if this is a column ref.
        """
        return self.org_tag.startswith('{') and self.org_tag.endswith('}')

    def __str__(self) -> str:
        """ Convert this HedTag to a string.

        Returns:
            str: The original tag if we haven't set a new tag.(e.g. short to long).

        """
        if self._schema_entry:
            return self.short_tag

        if self._tag:
            return self._tag

        return self._hed_string[self.span[0]:self.span[1]]

    def lower(self) -> str:
        """ Convenience function, equivalent to str(self).lower(). """
        return str(self).lower()

    def casefold(self) -> str:
        """ Convenience function, equivalent to str(self).casefold(). """
        return str(self).casefold()

    def _calculate_to_canonical_forms(self, hed_schema) -> list:
        """ Update internal state based on schema.

        Parameters:
            hed_schema (HedSchema or HedSchemaGroup): The schema to use to validate this tag.

        Returns:
            list[dict]:  A list of issues found during conversion. Each element is a dictionary.

        """
        tag_entry, remainder, tag_issues = hed_schema.find_tag_entry(self, self.schema_namespace)
        self._schema_entry = tag_entry
        self._schema = hed_schema
        if self._schema_entry:
            self.tag_terms = self._schema_entry.tag_terms
            if remainder:
                self._extension_value = remainder
        else:
            self.tag_terms = tuple()

        return tag_issues

    def get_stripped_unit_value(self, extension_text) -> tuple[Union[str, None], Union[str, None]]:
        """ Return the extension divided into value and units, if the units are valid.

        Parameters:
            extension_text (str): The text to split, in case it's a portion of a tag.

        Returns:
            Union[str, None]: The extension portion with the units removed or None if invalid units.
            Union[str, None]: The units or None if no units of the right unit class are found.

        Examples:
            'Duration/3 ms' will return ('3', 'ms')

        """
        tag_unit_classes = self.unit_classes
        stripped_value, units, match = HedTag._get_tag_units_portion(extension_text, tag_unit_classes)
        if stripped_value and match:
            return stripped_value, units
        elif units and not match:
            return None, units
        return extension_text, None

    def value_as_default_unit(self) -> Union[float, None]:
        """ Return the value converted to default units if possible or None if invalid.

        Returns:
            Union[float, None]: The extension value in default units. If no default units it assumes that the extension value is in default units.

        Examples:
            'Duration/300 ms' will return .3

        """
        tag_unit_classes = self.unit_classes
        stripped_value, unit, unit_entry = HedTag._get_tag_units_portion(self.extension, tag_unit_classes)
        if not stripped_value:
            return None
        if unit and not unit_entry:
            return None
        if unit and unit_entry and unit_entry.get_conversion_factor(unit) is not None:
            return float(stripped_value) * unit_entry.get_conversion_factor(unit)
        return float(stripped_value)

    @property
    def unit_classes(self) -> dict:
        """ Return a dict of all the unit classes this tag accepts.

        Returns:
            dict:  A dict of unit classes this tag accepts.

        Notes:
            - Returns empty dict if this is not a unit class tag.
            - The dictionary has unit name as the key and HedSchemaEntry as value.

        """
        if self._schema_entry:
            return self._schema_entry.unit_classes
        return {}

    @property
    def value_classes(self) -> dict:
        """ Return a dict of all the value classes this tag accepts.

        Returns:
            dict: A dictionary of HedSchemaEntry value classes this tag accepts.

        Notes:
            - Returns empty dict if this is not a value class.
            - The dictionary has unit name as the key and HedSchemaEntry as value.

        """
        if self._schema_entry:
            return self._schema_entry.value_classes
        return {}

    @property
    def attributes(self) -> dict:
        """ Return a dict of all the attributes this tag has or empty dict if this is not a value tag.

        Returns:
            dict: A dict of attributes this tag has.

        Notes:
            - Returns empty dict if this is not a unit class tag.
            - The dictionary has unit name as the key and HedSchemaEntry as value.

        """
        if self._schema_entry:
            return self._schema_entry.attributes
        return {}

    def tag_exists_in_schema(self) -> bool:
        """ Return whether the schema entry for this tag exists.

        Returns:
            bool: True if this tag exists.

        Notes:
            - This does NOT assure this is a valid tag.
        """
        return bool(self._schema_entry)

    def is_takes_value_tag(self) -> bool:
        """ Return True if this is a takes value tag.

        Returns:
            bool: True if this is a takes value tag.

        """
        if self._schema_entry:
            return self._schema_entry.has_attribute(HedKey.TakesValue)
        return False

    def is_unit_class_tag(self) -> bool:
        """ Return True if this is a unit class tag.

        Returns:
            bool: True if this is a unit class tag.

        """
        if self._schema_entry:
            return bool(self._schema_entry.unit_classes)
        return False

    def is_value_class_tag(self) -> bool:
        """ Return True if this is a value class tag.

        Returns:
            bool:  True if this is a tag with a value class.

        """
        if self._schema_entry:
            return bool(self._schema_entry.value_classes)
        return False

    def is_basic_tag(self) -> bool:
        """  Return True if a known tag with no extension or value.

        Returns:
            bool:  True if this is a known tag without extension or value.

        """
        return bool(self._schema_entry and not self.extension)

    def has_attribute(self, attribute) -> bool:
        """ Return True if this is an attribute this tag has.

        Parameters:
            attribute (str): Name of the attribute.

        Returns:
            bool: True if this tag has the attribute.

        """
        if self._schema_entry:
            return self._schema_entry.has_attribute(attribute)
        return False

    def get_tag_unit_class_units(self) -> list:
        """ Get the unit class units associated with a particular tag.

        Returns:
            list: A list containing the unit class units associated with a particular tag or an empty list.

        """
        units = []
        unit_classes = self.unit_classes
        for unit_class_entry in unit_classes.values():
            units += unit_class_entry.units.keys()

        return units

    @property
    def default_unit(self):
        """ Get the default unit class unit for this tag.

            Only a tag with a single unit class can have default units.

        Returns:
            unit(UnitEntry or None): the default unit entry for this tag, or None
        """
        # todo: Make this cached
        unit_classes = self.unit_classes.values()
        if len(unit_classes) == 1:
            first_unit_class_entry = list(unit_classes)[0]
            default_unit = first_unit_class_entry.has_attribute(HedKey.DefaultUnits, return_value=True)
            return first_unit_class_entry.units.get(default_unit, None)

    def base_tag_has_attribute(self, tag_attribute) -> bool:
        """ Check to see if the tag has a specific attribute.

            This is primarily used to check for things like TopLevelTag on Definitions and similar.

        Parameters:
            tag_attribute (str): A tag attribute.

        Returns:
            bool: True if the tag has the specified attribute. False, if otherwise.

        """
        if not self._schema_entry:
            return False

        return self._schema_entry.base_tag_has_attribute(tag_attribute)

    @staticmethod
    def _get_schema_namespace(org_tag) -> str:
        """ Finds the library namespace for the tag.

        Parameters:
            org_tag (str): A string representing a tag.

        Returns:
            str: Library namespace string or empty.

        """
        first_slash = org_tag.find("/")
        first_colon = org_tag.find(":")

        if first_colon != -1:
            if first_slash != -1 and first_colon > first_slash:
                return ""

            return org_tag[:first_colon + 1]
        return ""

    @staticmethod
    def _get_tag_units_portion(extension_text, tag_unit_classes):
        """ Split a value portion into value, units and its valid unitEntry (if any).

        Parameters:
            extension_text (str): A string representing the value portion of a tag with unit classes.
            tag_unit_classes (dict): Dictionary of valid UnitClassEntry objects for this tag.

        Returns:
            stripped_value (str or None): The value with the units removed.
                                          This is filled in if there are no units as well.
            units (str or None); The units string or None if no units.
            unitEntry (UnitEntry or None): The matching unit entry if one is found

        Notes:
            value, None, None  -- value portion has no units.
            value, units, unitEntry -- value portion has value and valid units.
            value, units, None -- value portion has a value and invalid units.

        """
        value, _, units = extension_text.partition(" ")
        if not units:
            return value, None, None

        for unit_class_entry in tag_unit_classes.values():
            possible_match = unit_class_entry.get_derivative_unit_entry(units)
            if possible_match:
                return value, units, possible_match
        return value, units, None

    def is_placeholder(self) -> bool:
        """Returns if this tag has a placeholder in it.

        Returns:
            bool: True if it has a placeholder.
        """
        if "#" in self.org_tag or "#" in self._extension_value:
            return True
        return False

    def replace_placeholder(self, placeholder_value):
        """ If tag has a placeholder character(#), replace with value.

        Parameters:
            placeholder_value (str): Value to replace placeholder with.

        """
        if self.is_placeholder():
            if self._schema_entry:
                tag = self.tag.replace('#', placeholder_value)
                self._extension_value = self._extension_value.replace("#", placeholder_value)
                self.tag = tag
            else:
                self._tag = self.tag.replace("#", placeholder_value)

    def get_normalized_str(self):
        if self._schema_entry:
            return self._namespace + self._schema_entry.short_tag_name.casefold() + self._extension_value.casefold()
        else:
            return self.casefold()

    def __hash__(self):
        return hash(self.get_normalized_str())

    def __eq__(self, other):
        if self is other:
            return True

        if isinstance(other, str):
            return self.casefold() == other.casefold()

        if not isinstance(other, HedTag):
            return False

        if self.short_tag == other.short_tag:
            return True

        if self.org_tag.casefold() == other.org_tag.casefold():
            return True
        return False

    def __deepcopy__(self, memo):
        # Check if the object has already been copied.
        if id(self) in memo:
            return memo[id(self)]

        # create a new instance of HedTag class
        new_tag = self.__class__.__new__(self.__class__)
        new_tag.__dict__.update(self.__dict__)

        # add the new object to the memo dictionary
        memo[id(self)] = new_tag

        # Deep copy the attributes that need it(most notably, we don't copy schema/schema entry)
        new_tag._parent = copy.deepcopy(self._parent, memo)
        new_tag._expandable = copy.deepcopy(self._expandable, memo)
        new_tag._expanded = copy.deepcopy(self._expanded, memo)

        return new_tag
