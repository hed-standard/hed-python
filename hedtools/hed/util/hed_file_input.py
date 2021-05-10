from hed.util.column_mapper import ColumnMapper
from hed.util.base_file_input import BaseFileInput


class HedFileInput(BaseFileInput):
    """A class to parse basic hed style spreadsheets into a more general format."""
    def __init__(self, filename, worksheet_name=None, tag_columns=None,
                 has_column_names=True, column_prefix_dictionary=None,
                 definition_mapper=None, hed_schema=None,
                 data_as_csv_string=None):
        """Constructor for the HedFileInput class.

        Parameters
        ----------
        filename: str
            An xml/tsv file to open.
        worksheet_name: str
            The name of the Excel workbook worksheet that contains the HED tags.  Not applicable to tsv files.
        tag_columns: []
            A list of ints containing the columns that contain the HED tags. The default value is the 2nd column.
        has_column_names: bool
            True if file has column names. The validation will skip over the first line of the file. False, if
            otherwise.
        column_prefix_dictionary: {}
            A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
            prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
            4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/
            prepended to them, the fourth column contains tags that need Event/Label/ prepended to them,
            and the fifth column contains tags that needs Event/Category/ prepended to them.
        definition_mapper: DefinitionMapper
            The definition mapper to use to remove and replace definition labels in HED data.
        hed_schema: HedSchema
             Used to create definitions.
        data_as_csv_string: str or None
            The data to treat as this file.  eg web services passing a string.
        """
        if tag_columns is None:
            tag_columns = [2]
        if column_prefix_dictionary is None:
            column_prefix_dictionary = {}

        new_mapper = ColumnMapper(tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary,
                                  definition_mapper=definition_mapper)
        super().__init__(filename, worksheet_name, has_column_names, new_mapper, hed_schema=hed_schema,
                                  data_as_csv_string=data_as_csv_string)
