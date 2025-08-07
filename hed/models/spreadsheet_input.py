""" A spreadsheet of HED tags. """
from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput


class SpreadsheetInput(BaseInput):
    """ A spreadsheet of HED tags. """

    def __init__(self, file=None, file_type=None, worksheet_name=None, tag_columns=None,
                 has_column_names=True, column_prefix_dictionary=None,
                 name=None):
        """Constructor for the SpreadsheetInput class.

        Parameters:
            file (str or file like): An xlsx/tsv file to open or a File object.
            file_type (str or None): ".xlsx" for Excel, ".tsv" or ".txt" for tsv. data.
            worksheet_name (str or None): The name of the Excel workbook worksheet that contains the HED tags.
                Not applicable to tsv files. If omitted for Excel, the first worksheet is assumed.
            tag_columns (list): A list of ints or strs containing the columns that contain the HED tags.
                If ints then column numbers with [1] indicating only the second column has tags.
            has_column_names (bool): True if file has column names. Validation will skip over the first row.
                first line of the file if the spreadsheet as column names.
            column_prefix_dictionary (dict or None): Dictionary with keys that are column numbers/names and
                values are HED tag prefixes to prepend to the tags in that column before processing.

        Notes:
            - If file is a string, file_type is derived from file and this parameter is ignored.
            - column_prefix_dictionary may be deprecated/renamed.  These are no longer prefixes,
              but rather converted to value columns.
              e.g. {"key": "Description", 1: "Label/"} will turn into value columns as
              {"key": "Description/#", 1: "Label/#"}
              It will be a validation issue if column 1 is called "key" in the above example.
              This means it no longer accepts anything but the value portion only in the columns.

        Raises:
            HedFileError: for any of the following issues:
            - The file is blank.
            - An invalid dataframe was passed with size 0.
            - An invalid extension was provided.
            - A duplicate or empty column name appears.
            - Cannot open the indicated file.
            - The specified worksheet name does not exist.
        """

        self.tag_columns = tag_columns
        new_mapper = ColumnMapper(tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary,
                                  warn_on_missing_column=False)

        super().__init__(file, file_type, worksheet_name, has_column_names, new_mapper, name=name)
