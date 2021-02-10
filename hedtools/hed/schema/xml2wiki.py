from hed.util import file_util
from hed.util.hed_schema import HedSchema, HedKey
from hed.schema.schema_validator import validate_schema


class HEDXml2Wiki:
    def __init__(self):
        self.current_tag_string = ""
        self.current_tag_extra = ""
        self.output = []

    def process_schema(self, hed_schema):
        """
        Takes a HedSchema object and returns a list of strings representing it's .mediawiki version.

        Parameters
        ----------
        hed_schema : HedSchema

        Returns
        -------
        mediawiki_strings: [str]
            A list of strings representing the .mediawiki version of this schema.
        """
        self.output = []

        self._output_header(hed_schema)
        self._output_tags(hed_schema)
        self._output_units(hed_schema)
        self._output_unit_modifiers(hed_schema)

        self.current_tag_string = "!# end hed"
        self._flush_current_tag()

        return self.output

    def _output_header(self, hed_schema):
        hed_attrib_string = self._get_attribs_string_from_schema(hed_schema)
        self.current_tag_string = f"HED {hed_attrib_string}"
        self._flush_current_tag()
        self._add_blank_line()
        self.current_tag_string = "!# start hed"
        self._flush_current_tag()

    def _output_tags(self, hed_schema):
        all_tags = hed_schema.get_all_tags()

        for tag in all_tags:
            if "/" not in tag:
                self._add_blank_line()
                self.current_tag_string += f"'''{tag}'''"
            else:
                count = tag.count("/")
                short_tag = tag.split("/")[-1]
                # takes value tags should appear after the nowiki tag.
                if short_tag.endswith("#"):
                    self.current_tag_string += f"{'*' * count}"
                    self.current_tag_extra += short_tag + " "
                else:
                    self.current_tag_string += f"{'*' * count} {short_tag}"
            self.current_tag_extra += self._format_props_and_desc(hed_schema, tag)
            self._flush_current_tag()

        self._add_blank_line()
        self._add_blank_line()

    def _output_units(self, hed_schema):
        self.current_tag_string += "'''Unit classes'''"
        self._flush_current_tag()
        for unit_name, unit_types in hed_schema.dictionaries[HedKey.Units].items():
            self.current_tag_string += f"* {unit_name}"
            self.current_tag_extra += self._format_props_and_desc(hed_schema, unit_name, HedKey.Units,
                                                                         [HedKey.DefaultUnits])
            self._flush_current_tag()

            for unit_type in unit_types:
                self.current_tag_string += f"** {unit_type}"
                self.current_tag_extra += self._format_props_and_desc(
                    hed_schema, unit_type, HedKey.Units, [HedKey.DefaultUnits, HedKey.SIUnit, HedKey.UnitSymbol])
                self._flush_current_tag()

        self._add_blank_line()

    def _output_unit_modifiers(self, hed_schema):
        self.current_tag_string += "'''Unit modifiers'''"
        self._flush_current_tag()
        for modifier_name in hed_schema.dictionaries[HedKey.SIUnitModifier]:
            self.current_tag_string += f"* {modifier_name}"
            self.current_tag_extra += self._format_props_and_desc(
                hed_schema, modifier_name, HedKey.SIUnitModifier, [HedKey.SIUnitModifier, HedKey.SIUnitSymbolModifier])
            self._flush_current_tag()

    def _flush_current_tag(self):
        if self.current_tag_string or self.current_tag_extra:
            if self.current_tag_extra:
                new_tag = f"{self.current_tag_string} <nowiki>{self.current_tag_extra}</nowiki>"
            else:
                new_tag = self.current_tag_string
            self.output.append(new_tag)
            self.current_tag_string = ""
            self.current_tag_extra = ""

    def _add_blank_line(self):
        self.output.append("")

    # Should this be a function?
    def _format_props_and_desc(self, hed_schema, tag_name, tag_class=HedKey.AllTags, keys=None):
        prop_string = ""
        tag_props = hed_schema.get_all_tag_attributes(tag_name, keys)
        if tag_props:
            prop_string += self._format_tag_props(tag_props)
        desc = hed_schema.get_tag_description(tag_name, tag_class)
        if desc:
            if tag_props:
                prop_string += " "
            prop_string += f"[{desc}]"

        return prop_string

    @staticmethod
    def _format_tag_props(tag_props):
        """
            Takes a dictionary of tag attributes and returns a string with the .mediawiki representation

        Parameters
        ----------
        tag_props : {str:str}
            {attribute_name : attribute_value}
        Returns
        -------
        str:
            The formatted string that should be output to the file.
        """
        prop_string = ""
        final_props = []
        for prop, value in tag_props.items():
            if value is None:
                continue
            if value is True or value == "true":
                final_props.append(prop)
            else:
                if "," in value:
                    split_values = value.split(",")
                    for split_value in split_values:
                        final_props.append(f"{prop}={split_value}")
                else:
                    final_props.append(f"{prop}={value}")

        if final_props:
            prop_string += "{"
            final_prop_string = ", ".join(final_props)
            prop_string += final_prop_string
            prop_string += "}"

        return prop_string

    @staticmethod
    def _get_attribs_string_from_schema(hed_schema):
        """
        Gets the schema attributes and converts it to a string.

        Parameters
        ----------
        hed_schema : HedSchema
            The schema to get attributes from

        Returns
        -------
        str:
            A string of the attributes that can be written to a .mediawiki formatted file
        """
        # Hardcode version to always be the first thing in attributes
        attrib_values = [f"version:{hed_schema.schema_attributes['version']}"]
        attrib_values.extend([f"{attr}:{value}" for attr, value in
                              hed_schema.schema_attributes.items() if attr != "version"])
        final_attrib_string = ", ".join(attrib_values)
        return final_attrib_string


def convert_hed_xml_2_wiki(hed_xml_url, local_xml_file=None, check_for_issues=True,
                           display_filename=None):
    """Converts the local HED xml file into a wikimedia file

    Parameters
    ----------
    hed_xml_url: str or None
        url pointing to the .xml file to use
    local_xml_file: str or None
        filepath to local xml hed schema(overrides hed_xml_url)
    check_for_issues : bool
        After conversion checks for warnings like capitalization or invalid characters.
    display_filename: str
        If present, will use this as the filename for context, rather than using the actual filename
        Useful for temp filenames.
    Returns
    -------
    mediawiki_filename: str
        Location of output mediawiki file, None on complete failure
    issues_list: [{}]
        returns a list of error/warning dictionaries
    """
    if local_xml_file is None:
        local_xml_file = file_util.url_to_file(hed_xml_url)

    hed_schema = HedSchema(local_xml_file)
    xml2wiki = HEDXml2Wiki()
    output_strings = xml2wiki.process_schema(hed_schema)
    local_mediawiki_file = file_util.write_strings_to_file(output_strings, ".mediawiki")

    issue_list = []
    if check_for_issues:
        warnings = validate_schema(local_xml_file, display_filename=display_filename)
        issue_list += warnings

    return local_mediawiki_file, issue_list
