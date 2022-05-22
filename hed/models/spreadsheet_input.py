from hed.models.column_mapper import ColumnMapper
from hed.models.base_input import BaseInput
from hed.models.def_mapper import DefMapper


class SpreadsheetInput(BaseInput):
    """ Class representing a spreadsheet of HED tags."""

    def __init__(self, file=None, file_type=None, worksheet_name=None, tag_columns=None,
                 has_column_names=True, column_prefix_dictionary=None,
                 def_dicts=None, name=None):
        """Constructor for the SpreadsheetInput class.

        Args:
            file (str or file like): An xlsx/tsv file to open or a File object.
            file_type (str or None): ".xlsx" for excel, ".tsv" or ".txt" for tsv. data. If file is a string, the
            worksheet_name (str or None): The name of the Excel workbook worksheet that contains the HED tags.
                Not applicable to tsv files. If omitted for Excel, the first worksheet is assumed.
            tag_columns (list): A list of ints containing the columns that contain the HED tags.
                The default value is [2] indicating only the second column has tags.
            has_column_names (bool): True if file has column names. Validation will skip over the
                first line of the file if the spreadsheet as column names.
            column_prefix_dictionary (dict): A dictionary with column number keys and prefix values.
            def_dicts (DefinitionDict or list):  A DefinitionDict or list of DefDicts containing definitions for this
                object other than the ones extracted from the SpreadsheetInput object itself.

        Examples:
            A prefix dictionary {3: 'Label/', 5: 'Description/'} indicates that column 3 and 5 have HED tags
            that need to be prefixed by Label/ and Description/ respectively.
            Column numbers 3 and 5 should also be included in the tag_columns list.

        """
        if tag_columns is None:
            tag_columns = [1]
        if column_prefix_dictionary is None:
            column_prefix_dictionary = {}

        new_mapper = ColumnMapper(tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary)

        def_mapper = DefMapper(def_dicts)

        super().__init__(file, file_type, worksheet_name, has_column_names, new_mapper, def_mapper=def_mapper,
                         name=name)


if __name__ == '__main__':
    import os
    from hed.schema import load_schema_version
    path1 = os.path.realpath('H:/HEDPython/hed-web/tests/data/ExcelMultipleSheets.xlsx')
    base1 = SpreadsheetInput(path1, tag_columns=[4], worksheet_name='LKT 8HED3')
    hed_schema = load_schema_version(xml_version='8.0.0')
    issues = base1.convert_to_long(hed_schema=hed_schema)
    base1.to_excel('D:/temp.xlsx', output_processed_file=True)