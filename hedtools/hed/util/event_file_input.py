from hed.util.hed_event_mapper import EventMapper
from hed.util.base_file_input import BaseFileInput

class EventFileInput(BaseFileInput):
    """A class to parse bids style spreadsheets into a more general format."""

    def __init__(self, filename, worksheet_name=None, tag_columns=None,
                 has_column_names=True, column_prefix_dictionary=None,
                 json_event_files=None, attribute_columns=None,
                 hed_dictionary=None):
        """Constructor for the EventFileInput class.

         Parameters
         ----------
         filename: str
             An xml/tsv file to open.
         worksheet_name: str
             The name of the Excel workbook worksheet that contains the HED tags.  Not applicable to tsv files.
         tag_columns: list
             A list of ints containing the columns that contain the HED tags. The default value is the 2nd column.
         has_column_names: bool
             True if file has column names. The validation will skip over the first line of the file. False, if
             otherwise.
         column_prefix_dictionary: dict
             A dictionary with keys pertaining to the required HED tag columns that correspond to tags that need to be
             prefixed with a parent tag path. For example, prefixed_needed_tag_columns = {3: 'Event/Description',
             4: 'Event/Label/', 5: 'Event/Category/'} The third column contains tags that need Event/Description/ prepended to them,
             the fourth column contains tags that need Event/Label/ prepended to them, and the fifth column contains tags
             that needs Event/Category/ prepended to them.
         json_event_files : str or [str]
             A list of json filenames to pull events from
         attribute_columns: str/int or [str/int]
             A list of column names or numbers to treat as attributes.
         """
        if tag_columns is None:
            tag_columns = [2]
        if column_prefix_dictionary is None:
            column_prefix_dictionary = {}

        new_mapper = EventMapper(tag_columns=tag_columns, column_prefix_dictionary=column_prefix_dictionary,
                                 hed_dictionary=hed_dictionary)
        new_mapper.add_json_file_events(json_event_files)
        new_mapper.add_attribute_columns(attribute_columns)
        for entry in new_mapper._key_validation_issues:
            for issue in new_mapper._key_validation_issues[entry]:
                print(issue["message"])

        super().__init__(filename, worksheet_name, has_column_names, new_mapper)

        # Finalize mapping information
        if self._dataframe is not None and self._has_column_names:
            columns = self._dataframe.columns
            self._mapper.set_column_map(columns)
        else:
            raise ValueError("You are attempting to open a bids style file with no column headers provided.\n"
                             "This is probably not intended.")


if __name__ == '__main__':
    from hed.util.hed_dictionary import HedDictionary
    local_hed_xml = "examples/data/HED7.1.1.xml"
    hed_dictionary = HedDictionary(local_hed_xml)
    event_file = EventFileInput("examples/data/basic_events_test.xlsx",
                                json_event_files="examples/data/both_types_events.json", attribute_columns=["onset"],
                                hed_dictionary=hed_dictionary)

    for stuff in event_file:
        print(stuff)
