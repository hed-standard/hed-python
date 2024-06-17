"""
Create a HedSchema object from a .mediawiki file.
"""

from abc import abstractmethod
from hed.schema.hed_schema_constants import HedSectionKey, HedKey
from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.schema_io.base2schema import SchemaLoader


class SchemaLoaderText(SchemaLoader):
    """ Intermediate class to handle text based formats(tsv, wiki)

        Cannot be used directly
    """
    def __init__(self, filename, schema_as_string=None, schema=None, file_format=None, name=""):
        super().__init__(filename, schema_as_string, schema, file_format, name)
        self._no_name_msg = f"No tag name found in row."
        self._no_name_error = HedExceptions.GENERIC_ERROR

    def _add_tag_meta(self, parent_tags, row_number, row, level_adj):
        tag_entry = self._add_tag_line(parent_tags, row_number, row)
        if not tag_entry:
            # This will have already raised an error
            return None, parent_tags, level_adj

        try:
            rooted_entry = self.find_rooted_entry(tag_entry, self._schema, self._loading_merged)
            if rooted_entry:
                parent_tags = rooted_entry.long_tag_name.split("/")
                level_adj = len(parent_tags)
                # Create the entry again for rooted tags, to get the full name.
                tag_entry = self._add_tag_line(parent_tags, row_number, row)
        except HedFileError as e:
            self._add_fatal_error(row_number, row, e.message, e.code)
            return None, parent_tags, level_adj

        tag_entry = self._add_to_dict(row_number, row, tag_entry, HedSectionKey.Tags)

        if tag_entry.name.endswith("/#"):
            parent_tags.append("#")
        else:
            parent_tags.append(tag_entry.short_tag_name)

        return tag_entry, parent_tags, level_adj

    def _add_tag_line(self, parent_tags, row_number, row):
        """ Add a tag to the dictionaries.

        Parameters:
            parent_tags (list): A list of parent tags in order.
            row_number (int): The row number to report errors as
            row (str or pd.Series): A tag row or pandas series(depends on format)

        Returns:
            HedSchemaEntry: The entry for the added tag.

        Notes:
            Includes attributes and description.
        """
        tag_name, _ = self._get_tag_name(row)
        if tag_name:
            if parent_tags:
                long_tag_name = "/".join(parent_tags) + "/" + tag_name
            else:
                long_tag_name = tag_name
            return self._create_entry(row_number, row, HedSectionKey.Tags, long_tag_name)

        self._add_fatal_error(row_number, row, self._no_name_msg, error_code=self._no_name_error)

    def _add_to_dict(self, row_number, row, entry, key_class):
        if entry.has_attribute(HedKey.InLibrary) and not self._loading_merged and not self.appending_to_schema:
            self._add_fatal_error(row_number, row,
                                  "Library tag in unmerged schema has InLibrary attribute",
                                  HedExceptions.IN_LIBRARY_IN_UNMERGED)

        return self._add_to_dict_base(entry, key_class)

    @abstractmethod
    def _create_entry(self, row_number, row, key_class, full_tag_name=None):
        """ Create a tag entry from the given row

        Parameters:
            row_number (int): The row number to report errors as
            row (str or pd.Series): A tag row or pandas series(depends on format)
            key_class(HedSectionKey): The HedSectionKey for this object
            full_tag_name (str): The full long form tag name, overrides value found in row.

        Returns:
            HedSchemaEntry or None: The entry for the added tag.
        """
        raise NotImplementedError("Required in subclass")

    @abstractmethod
    def _get_tag_name(self, row):
        """ Returns the tag name for the given row

        Parameters:
            row (str or pd.Series): A tag row or pandas series(depends on format)

        Returns:
            entry_name(str): The tag name for the given row

        Notes:
            Should be set to add a fatal error if no name returned
        """
        raise NotImplementedError("Required in subclass")
