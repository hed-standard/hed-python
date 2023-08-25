""" Manages events of temporal extent. """

from hed.models import HedString
from hed.models.model_constants import DefTagNames
from hed.models.df_util import get_assembled
from hed.tools.analysis.temporal_event import TemporalEvent
from hed.tools.analysis.hed_type_defs import HedTypeDefs


class EventManager:

    def __init__(self, input_data, hed_schema, extra_defs=None):
        """ Create an event manager for an events file. Manages events of temporal extent.

        Parameters:
            input_data (TabularInput): Represents an events file with its sidecar.
            hed_schema (HedSchema): HED schema used in this
            extra_defs (DefinitionDict):  Extra type_defs not included in the input_data information.

        :raises HedFileError:
            - if there are any unmatched offsets.

        Notes:  Keeps the events of temporal extend by their starting index in events file. These events
        are separated from the rest of the annotations.

        """

        self.event_list = [[] for _ in range(len(input_data.dataframe))]
        self.hed_schema = hed_schema
        self.input_data = input_data
        self.def_dict = input_data.get_def_dict(hed_schema, extra_def_dicts=extra_defs)
        self.onsets = input_data.dataframe['onset'].tolist()
        self.hed_strings = None  # Remaining HED strings copy.deepcopy(hed_strings)
        self._create_event_list(input_data)

    def _create_event_list(self, input_data):
        """ Populate the event_list with the events with temporal extent indexed by event number.

        Parameters:
            input_data (TabularInput): A tabular input that includes its relevant sidecar.

        :raises HedFileError:
            - If the hed_strings contain unmatched offsets.

        Notes:

        """
        hed_strings, def_dict = get_assembled(input_data, input_data._sidecar, self.hed_schema,
                                              extra_def_dicts=None, join_columns=True,
                                              shrink_defs=True, expand_defs=False)
        onset_dict = {}  # Temporary dictionary keeping track of temporal events that haven't ended yet.
        for event_index, hed in enumerate(hed_strings):
            self._extract_temporal_events(hed, event_index, onset_dict)
        # Now handle the events that extend to end of list
        for item in onset_dict.values():
            item.set_end(len(self.onsets), None)
        self.hed_strings = hed_strings

    def _extract_temporal_events(self, hed, event_index, onset_dict):
        """ Extract the temporal events and remove them from the other HED strings.

        Parameters:
            hed (HedString):  The assembled HedString at position event_index in the data.
            event_index (int): The position of this string in the data.
            onset_dict (dict):  Running dict that keeps track of temporal events that haven't yet ended.

        Note:
            This removes the events of temporal extent from hed.

         """
        if not hed:
            return
        group_tuples = hed.find_top_level_tags(anchor_tags={DefTagNames.ONSET_KEY, DefTagNames.OFFSET_KEY},
                                               include_groups=2)
        to_remove = []
        for tup in group_tuples:
            anchor_tag = tup[1].find_def_tags(recursive=False, include_groups=0)[0]
            anchor = anchor_tag.extension.lower()
            if anchor in onset_dict or tup[0].short_base_tag.lower() == DefTagNames.OFFSET_KEY:
                temporal_event = onset_dict.pop(anchor)
                temporal_event.set_end(event_index, self.onsets[event_index])
            if tup[0] == DefTagNames.ONSET_KEY:
                new_event = TemporalEvent(tup[1], event_index, self.onsets[event_index])
                self.event_list[event_index].append(new_event)
                onset_dict[anchor] = new_event
            to_remove.append(tup[1])
        hed.remove(to_remove)

    # def _set_event_contexts(self):
        """ Creates an event context for each hed string.

        Notes:
            The event context would be placed in an event context group, but is kept in a separate array without the
            event context group or tag.

        """
        # contexts = [[] for _ in range(len(self.hed_strings))]
        # for onset in self.onset_list:
        #     for i in range(onset.start_index+1, onset.end_index):
        #         contexts[i].append(onset.contents)
        # for i in range(len(self.hed_strings)):
        #     contexts[i] = HedString(",".join(contexts[i]), hed_schema=self.hed_schema)
        # self.contexts = contexts

    def unfold_context(self):
        """ Creates an event context for each hed string.

        Returns:
            list of str
            list of list of str
            list of list of str

        """
        hed = ["" for _ in range(len(self.hed_strings))]
        for index, item in enumerate(self.hed_strings):
            if item:
                hed[index] = str(item)
        base = [[] for _ in range(len(self.hed_strings))]
        contexts = [[] for _ in range(len(self.hed_strings))]
        for events in self.event_list:
            for event in events:
                this_str = str(event.contents)
                base[event.start_index].append(this_str)
                for i in range(event.start_index + 1, event.end_index):
                    contexts[i].append(this_str)
        return hed, self.compress_strings(base), self.compress_strings(contexts)    # these are each a list of lists of strings

    @staticmethod
    def compress_strings(list_to_compress):
        result_list = ["" for _ in range(len(list_to_compress))]
        for index, item in enumerate(list_to_compress):
            if item:
                result_list[index] = ",".join(item)
        return result_list
            
    def find_type_defs(self, types):
        def_names = {}
        for type_tag in types:
            type_defs = HedTypeDefs(self.def_dict, type_tag=type_tag)
            def_names[type_tag] = type_defs.def_map
        return def_names
    
    def filter_type(self): 
        print("to here")
    
    # def unfold_context(self):
    #     """ Creates an event context for each hed string.
    # 
    #     Returns:
    #         (tuple): list of hed str, list of list of hed str
    # 
    #     """
    #     hed = [[] for _ in range(len(self.hed_strings))]
    #     for index, item in enumerate(self.hed_strings):
    #         if item:
    #             hed[index] = [str(item)]
    #     contexts = [[] for _ in range(len(self.hed_strings))]
    #     for events in self.event_list:
    #         for event in events:
    #             this_str = str(event.contents)
    #             hed[event.start_index].append(this_str)
    #             for i in range(event.start_index + 1, event.end_index):
    #                 contexts[i].append(this_str)
    #     return hed, contexts  # these are each a list of lists of strings
    
    @staticmethod
    def fix_list(hed_list, hed_schema, as_string=False):
        for index, item in enumerate(hed_list):
            if not item:
                hed_list[index] = None
            elif as_string:
                hed_list[index] = ",".join(str(item))
            else:
                hed_list[index] = HedString(",".join(str(item)), hed_schema)
        return hed_list
