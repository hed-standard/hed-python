"""Schema entry classes representing individual nodes in the HED vocabulary."""

from __future__ import annotations

import itertools
import math
from typing import Any

import inflect

from hed.schema.hed_schema_constants import ANY_UNITS_CLASS, HedKey, HedSectionKey

pluralize = inflect.engine()
pluralize.defnoun("hertz", "hertz")


class HedSchemaEntry:
    """A single node in the HED schema vocabulary.

    Every term, unit, unit class, value class, attribute, and property that
    appears in a loaded :class:`~hed.schema.HedSchema` is represented as a
    ``HedSchemaEntry`` (or one of its subclasses). The entry stores the node's
    name, all declared attributes (e.g. ``takesValue``, ``allowedCharacter``),
    its description, and a back-reference to its containing
    :class:`~hed.schema.HedSchemaSection`.

    Concrete subclasses add section-specific state:

    - :class:`HedTagEntry` — vocabulary tag nodes.
    - :class:`UnitClassEntry` — unit class nodes (e.g. *time*, *mass*).
    - :class:`UnitEntry` — individual unit nodes (e.g. *second*, *gram*).

    **Use this class (or its subclasses) directly when you need to:**

    - Introspect schema vocabulary (e.g. list all tags with ``takesValue``).
    - Build schema validators, schema browsers, or schema-diff tools.
    - Implement custom HED annotation tooling that looks up tag metadata.

    **Most users never need this class** — :meth:`~hed.schema.HedSchema.get_tag_entry`
    and :meth:`~hed.schema.HedSchema.get_all_schema_tags` are sufficient for the
    common lookup patterns.
    """

    def __init__(self, name, section):
        """Constructor for HedSchemaEntry.

        Parameters:
            name (str): The name of the entry.
            section (HedSchemaSection):  The section to which it belongs.

        """
        self.name = name
        # key: property/attribute name, value = property value. Will often be a bool
        self.attributes = {}
        self.description = None
        self._section = section

        # This section is largely unused. It will only be filled in when we try to add an attribute
        # that isn't valid in this section.
        self._unknown_attributes = None

    def finalize_entry(self, schema):
        """Called once after loading to set internal state.

        Parameters:
            schema (HedSchema): The schema that holds the rules.

        """
        # Clear out any known attributes from the unknown section
        to_remove = []
        if self._unknown_attributes:
            for attribute in self._unknown_attributes:
                if attribute in self._section.valid_attributes:
                    to_remove.append(attribute)

            for item in to_remove:
                self._unknown_attributes.pop(item)

    def has_attribute(self, attribute, return_value=False) -> bool | Any:
        """Checks for the existence of an attribute in this entry.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            Union[bool, any]: If return_value is False, returns True if the attribute exists and False otherwise.
            If return_value is True, returns the value of the attribute if it exists, else returns None.

        Notes:
            - The existence of an attribute does not guarantee its validity.
        """
        if return_value:
            return self.attributes.get(attribute, None)
        else:
            return attribute in self.attributes

    def attribute_has_property(self, attribute, property_name) -> bool:
        """Return True if attribute has property.

        Parameters:
            attribute (str): Attribute name to check for property_name.
            property_name (str): The property value to return.

        Returns:
            bool: Returns True if this entry has the property.

        """
        attr_entry = self._section.valid_attributes.get(attribute)
        if attr_entry and attr_entry.has_attribute(property_name):
            return True
        return False

    def _set_attribute_value(self, attribute, attribute_value):
        """Add attribute and set its value.

        Parameters:
            attribute (str): The name of the schema entry attribute.
            attribute_value (bool or str):  The value of the attribute.

        Notes:
            - If this an invalid attribute name, it will be also added as an unknown attribute.

        """
        if not attribute_value:
            return

        # todo: remove this patch and redo the code
        # This check doesn't need to be done if the schema is valid.
        if attribute not in self._section.valid_attributes:
            if self._unknown_attributes is None:
                self._unknown_attributes = {}
            self._unknown_attributes[attribute] = attribute_value
        self.attributes[attribute] = attribute_value

    @property
    def section_key(self):
        """Returns the HedSectionKey identifying which schema section owns this entry.

        Returns:
            HedSectionKey: The section key for this entry's parent section.

        """
        return self._section.section_key

    def __eq__(self, other):
        if self.name != other.name:
            return False
        if not self._compare_attributes_no_order(self.attributes, other.attributes):
            return False
        if self.description != other.description:
            return False
        return True

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    @staticmethod
    def _compare_attributes_no_order(left, right):
        if left != right:
            left = {
                name: (set(value.split(",")) if isinstance(value, str) else value) for (name, value) in left.items()
            }
            right = {
                name: (set(value.split(",")) if isinstance(value, str) else value) for (name, value) in right.items()
            }

        return left == right


class UnitClassEntry(HedSchemaEntry):
    """A unit class node in the HED schema (e.g. *time*, *mass*, *frequency*).

    Extends :class:`HedSchemaEntry` with the set of :class:`UnitEntry` objects
    that belong to the class and a pre-computed ``derivative_units`` dict that
    maps every accepted surface form (including SI prefixes and plurals) to its
    canonical :class:`UnitEntry`.

    Typical access pattern::

        unit_class = schema.get_tag_entry("time", HedSectionKey.UnitClasses)
        for name, unit in unit_class.units.items():
            print(name, unit.attributes)

    Attributes:
        units (dict[str, UnitEntry]): Map from unit name to entry after
            :meth:`finalize_entry` is called.
        derivative_units (dict[str, UnitEntry]): Map from every accepted
            surface form (plural, SI-prefixed, etc.) to the base unit entry.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._units = []
        self.units = []
        self.derivative_units = {}

    @property
    def children(self):
        """Alias to get the units for this class

        Returns:
            unit_list(list): The unit list for this class
        """
        return self.units

    def add_unit(self, unit_entry):
        """Add the given unit entry to this unit class.

        Parameters:
            unit_entry (HedSchemaEntry): Unit entry to add.

        """
        self._units.append(unit_entry)

    def finalize_entry(self, schema):
        """Called once after schema load to set state.

        Parameters:
            schema (HedSchema): The object with the schema rules.

        """
        super().finalize_entry(schema)
        self.units = {unit_entry.name: unit_entry for unit_entry in self._units}
        for unit_entry in self.units.values():
            unit_entry.unit_class_entry = self
        derivative_units = {}
        for unit_entry in self.units.values():
            derivative_units.update(dict.fromkeys(unit_entry.derivative_units.keys(), unit_entry))

        self.derivative_units = derivative_units

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if self.units != other.units:
            return False
        return True

    def get_derivative_unit_entry(self, units):
        """Gets the (derivative) unit entry if it exists

        All unit strings are case-sensitive, so this is a single exact lookup: unit names may be pluralized
        and carry an SI modifier, unit symbols may carry a modifier but are never pluralized, and none of
        them may change case (``milliseconds`` and ``uV`` match; ``Milliseconds``, ``MS`` and ``UV`` do not).

        Parameters:
            units (str): The unit string as written, possibly plural or with a modifier.

        Returns:
            Union[UnitEntry, None]: The unit entry if it exists.

        """
        return self.derivative_units.get(units)


class UnitEntry(HedSchemaEntry):
    """A single unit node in the HED schema (e.g. *second*, *gram*, *hertz*).

    Extends :class:`HedSchemaEntry` with the list of SI unit modifiers that
    apply to this unit, a pre-computed ``derivative_units`` mapping (surface
    form → conversion factor), and a back-reference to the parent
    :class:`UnitClassEntry`.

    Attributes:
        unit_modifiers (list[HedSchemaEntry]): SI modifier entries (e.g. *milli*, *kilo*).
        derivative_units (dict[str, float]): Map from every accepted surface
            form to its numeric conversion factor relative to the SI base unit.
        unit_class_entry (UnitClassEntry): The parent unit class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_modifiers = []
        self.derivative_units = {}
        self.unit_class_entry = None

    def finalize_entry(self, schema):
        """Called once after loading to set internal state.

        Parameters:
            schema (HedSchema): The schema rules come from.

        Notes:
            Unit strings are case-sensitive, so every key is built from the name exactly as listed.
            Unit names may be pluralized; unit symbols never are. A compound SI unit (one whose name
            contains ``-per-`` or ``^``, such as ``m-per-s^2``) is expanded component-wise: each
            component may carry one SI modifier, so ``cm-per-us`` and ``mm^3`` are accepted while
            ``kmm-per-s`` is not. Every other unit accepts one modifier in front of the whole name.
        """
        super().finalize_entry(schema)
        self.unit_modifiers = schema._get_modifiers_for_unit(self.name)
        components = self._compound_components()
        if components is not None:
            self.derivative_units = self._compound_derivative_units(components)
            return

        derivative_units = {}
        if self.has_attribute(HedKey.UnitSymbol):
            base_plural_units = {self.name}
        else:
            base_plural_units = {self.name, pluralize.plural(self.name)}

        base_factor = self._parse_factor(self.attributes)
        for derived_unit in base_plural_units:
            derivative_units[derived_unit] = base_factor
            for modifier in self.unit_modifiers:
                derivative_units[modifier.name + derived_unit] = base_factor * self._parse_factor(modifier.attributes)
        self.derivative_units = derivative_units

    def _compound_components(self):
        """Split a compound SI unit name into its components.

        Returns:
            Union[list[tuple[str, int]], None]: ``(base, exponent)`` per component, in name order, when this
                unit has SIUnit and its name contains ``-per-`` or ``^``; None for every other unit. The
                first component is the numerator, the rest are denominators. None is also returned when
                a component is not of the form ``base`` or ``base^n`` with an integer ``n``, so a name the
                rule does not describe falls back to the whole-string path.
        """
        if not self.has_attribute(HedKey.SIUnit) or ("-per-" not in self.name and "^" not in self.name):
            return None
        components = []
        for component in self.name.split("-per-"):
            base, _, exponent = component.partition("^")
            if not base:
                return None
            if not exponent:
                components.append((base, 1))
                continue
            try:
                components.append((base, int(exponent)))
            except ValueError:
                return None
        return components

    def _compound_derivative_units(self, components):
        """Build the derivative map of a compound unit, one optional modifier per component.

        Parameters:
            components (list[tuple[str, int]]): Output of :meth:`_compound_components`.

        Returns:
            dict[str, float]: Every accepted surface form mapped to its conversion factor. The factor is
                the listed factor times the product of each component's modifier factor raised to the
                component's exponent, negative for denominator components: ``cm-per-us`` in speed is
                ``1.0 * 0.01 * (1e-6) ** -1 = 10000`` m-per-s and ``mm^3`` is ``1e-9`` m^3.
        """
        base_factor = self._parse_factor(self.attributes)
        modifier_choices = [("", 1.0)] + [
            (modifier.name, self._parse_factor(modifier.attributes)) for modifier in self.unit_modifiers
        ]
        derivative_units = {}
        for choice in itertools.product(modifier_choices, repeat=len(components)):
            parts = []
            factor = base_factor
            for index, ((base, exponent), (prefix, modifier_factor)) in enumerate(
                zip(components, choice, strict=False)
            ):
                parts.append(prefix + base + (f"^{exponent}" if exponent != 1 else ""))
                signed_exponent = exponent if index == 0 else -exponent
                factor *= math.pow(modifier_factor, signed_exponent)
            derivative_units["-per-".join(parts)] = factor
        return derivative_units

    @staticmethod
    def _parse_factor(attributes):
        """Return the conversionFactor in *attributes* as a float, or 1.0 when absent or unparsable."""
        try:
            return float(attributes.get(HedKey.ConversionFactor, "1.0").replace("^", "e"))
        except (ValueError, AttributeError):
            return 1.0

    def get_conversion_factor(self, unit_name):
        """Returns the conversion factor from combining this unit with the specified modifier

        Parameters:
            unit_name (str or None): the full name of the unit with modifier

        Returns:
            Union[float, None]: Returns the conversion factor, or None if this unit has no conversionFactor
                                or unit_name is not one of its accepted forms.
        """
        if HedKey.ConversionFactor in self.attributes:
            factor = self.derivative_units.get(unit_name)
            if factor is not None:
                return float(factor)
        return None


class HedTagEntry(HedSchemaEntry):
    """A vocabulary tag node in the HED schema.

    Extends :class:`HedSchemaEntry` with full/short tag name forms, value-class
    and unit-class associations, and helper methods for tag-path traversal.

    Typical access pattern::

        entry = schema.get_tag_entry("Sensory-event")
        print(entry.long_tag_name)   # "Event/Sensory-event"
        print(entry.takes_value_child)  # child "#" entry if tag takes a value

    Attributes:
        unit_classes (dict[str, UnitClassEntry]): Unit classes accepted by this
            tag\'s value (non-empty only if ``takesValue`` is set).
        value_classes (dict[str, HedSchemaEntry]): Value classes that constrain
            the value format.
        long_tag_name (str): The full slash-separated path from the schema root,
            with any trailing ``/#`` stripped.
        short_tag_name (str): The final component of the tag path (short form).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_classes = {}
        self.value_classes = {}
        # These always have any /# stripped off the end, so they can easily be used with normal code.
        self.long_tag_name = None
        self.short_tag_name = None
        self.takes_value_child_entry = None  # this is a child takes value tag, if one exists
        self._parent_tag = None
        self.tag_terms = ()
        # During setup, it's better to have attributes shadow inherited before getting its own copy later.
        self.inherited_attributes = self.attributes
        # Descendent tags below this one
        self.children = {}

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if not self._compare_attributes_no_order(self.inherited_attributes, other.inherited_attributes):
            return False
        return True

    def has_attribute(self, attribute, return_value=False):
        """Returns th existence or value of an attribute in this entry.

            This also checks parent tags for inheritable attributes like ExtensionAllowed.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            Union[bool, any]: If return_value is False, returns True if the attribute exists and False otherwise.
            If return_value is True, returns the value of the attribute if it exists, else returns None.

        Notes:
            - The existence of an attribute does not guarantee its validity.
        """
        val = self.inherited_attributes.get(attribute)
        if not return_value:
            val = val is not None
        return val

    def _check_inherited_attribute_internal(self, attribute):
        """Gather up all instances of an attribute from this entry and any parent entries"""
        attribute_values = []

        iter_entry = self
        while iter_entry is not None:
            if iter_entry.takes_value_child_entry:
                break
            if attribute in iter_entry.attributes:
                attribute_values.append(iter_entry.attributes[attribute])
            iter_entry = iter_entry._parent_tag

        return attribute_values

    def _check_inherited_attribute(self, attribute, return_value=False):
        """
        Checks for the existence of an attribute in this entry and its parents.

        Parameters:
            attribute (str): The attribute to check for.
            return_value (bool): If True, returns the actual value of the attribute.
                                 If False, returns a boolean indicating the presence of the attribute.

        Returns:
            Union[bool, any]: Depending on the flag return_value,
            returns either the presence of the attribute, or its value.

        Notes:
            - The existence of an attribute does not guarantee its validity.
            - For string attributes, the values are joined with a comma as a delimiter from all ancestors.
            - For other attributes, only the value closest to the leaf is returned
        """
        attribute_values = self._check_inherited_attribute_internal(attribute)

        if return_value:
            if not attribute_values:
                return None
            try:
                return ",".join(attribute_values)
            except TypeError:
                return attribute_values[0]  # Return the lowest level attribute if we don't want the union
        return bool(attribute_values)

    def base_tag_has_attribute(self, tag_attribute):
        """Check if the base tag has a specific attribute.

        Parameters:
            tag_attribute (str): A tag attribute.

        Returns:
            bool: True if the tag has the specified attribute. False, if otherwise.

        Notes:
            This mostly is relevant for takes value tags.

        """
        base_entry = self
        if self.has_attribute(HedKey.TakesValue):
            base_entry = base_entry._parent_tag

        return base_entry.has_attribute(tag_attribute)

    @property
    def parent(self):
        """Get the parent entry of this tag"""
        return self._parent_tag

    @property
    def parent_name(self):
        """Gets the parent tag entry name"""
        if self._parent_tag:
            return self._parent_tag.name
        parent_name, _, child_name = self.name.rpartition("/")
        return parent_name

    def _finalize_classes(self, schema, attribute_key, section_key):
        result = {}
        if attribute_key in self.attributes:
            for attribute_name in self.attributes[attribute_key].split(","):
                entry = schema._get_tag_entry(attribute_name, section_key)
                if entry:
                    result[attribute_name] = entry
        return result

    def _finalize_takes_value_tag(self, schema):
        if self.name.endswith("/#"):
            self.unit_classes = self._finalize_classes(schema, HedKey.UnitClass, HedSectionKey.UnitClasses)
            if ANY_UNITS_CLASS in self.unit_classes:
                # unitClass=anyUnits (specification 4.0.0): the placeholder accepts a unit from every unit class
                # of the schema, so it resolves units against all of them. The attribute itself is unchanged.
                self.unit_classes = {
                    name: entry for name, entry in schema.unit_classes.items() if name != ANY_UNITS_CLASS
                }
            self.value_classes = self._finalize_classes(schema, HedKey.ValueClass, HedSectionKey.ValueClasses)

    def _finalize_inherited_attributes(self):
        # Replace the list with a copy we can modify.
        self.inherited_attributes = self.attributes.copy()
        for attribute in self._section.inheritable_attributes:
            value = self._check_inherited_attribute(attribute, return_value=True)
            # None means "not found in the hierarchy"; attribute values themselves are never None.
            if value is not None:
                self.inherited_attributes[attribute] = value

    def finalize_entry(self, schema):
        """Called once after schema loading to set state.

        Parameters:
            schema (HedSchema): The schema that the rules come from.

        """
        super().finalize_entry(schema)
        # Set the parent and child pointers. Child is just for "takes value"
        parent_name, _, child_name = self.name.rpartition("/")
        parent_tag = None
        if parent_name:
            parent_tag = schema._get_tag_entry(parent_name)
        self._parent_tag = parent_tag
        if self._parent_tag:
            self._parent_tag.children[self.short_tag_name] = self
        self.takes_value_child_entry = schema._get_tag_entry(self.name + "/#")
        self.tag_terms = tuple(self.long_tag_name.casefold().split("/"))

        self._finalize_inherited_attributes()
        self._finalize_takes_value_tag(schema)
