""" Manages events of temporal extent. """

from hed.models import HedString
from hed.models.model_constants import DefTagNames
from hed.models.df_util import get_assembled
from hed.models.string_util import split_base_tags, split_def_tags
from hed.tools.analysis.temporal_event import TemporalEvent
from hed.tools.analysis.hed_type_defs import HedTypeDefs


class EventManager:

    def __init__(self, input_data, hed_schema, extra_defs=None):
        """ Create an event manager for an events file. Manages events of temporal extent.

        Parameters:
            input_data (TabularInput): Represents an events file with its sidecar.
            hed_schema (HedSchema): HED schema used in this
            extra_defs (DefinitionDict):  Extra definitions not included in the input_data information.

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

    def unfold_context(self, remove_types=[]):
        """ Unfolds the event information into hed, base, and contexts either as arrays of str or of HedString.

        Parameters:
            remove_types (list):  List of types to remove.

        Returns:
            list of str or HedString representing the information without the events of temporal extent
            list of str or HedString representing the onsets of the events of temporal extent
            list of str or HedString representing the ongoing context information.

        """

        placeholder = ""
        remove_defs = self.get_type_defs(remove_types)
        new_hed = [placeholder for _ in range(len(self.hed_strings))]
        new_base = [placeholder for _ in range(len(self.hed_strings))]
        new_contexts = [placeholder for _ in range(len(self.hed_strings))]
        base, contexts = self._expand_context()
        for index, item in enumerate(self.hed_strings):
            new_hed[index] = self._process_hed(item, remove_types=remove_types,
                                               remove_defs=remove_defs, remove_group=False)
            new_base[index] = self._process_hed(base[index], remove_types=remove_types,
                                                remove_defs=remove_defs, remove_group=True)
            new_contexts[index] = self._process_hed(contexts[index], remove_types=remove_types,
                                                    remove_defs=remove_defs, remove_group=True)
        return new_hed, new_base, new_contexts   # these are each a list of strings

    def _expand_context(self):
        """ Expands the onset and the ongoing context for additional processing.

        """
        base = [[] for _ in range(len(self.hed_strings))]
        contexts = [[] for _ in range(len(self.hed_strings))]
        for events in self.event_list:
            for event in events:
                this_str = str(event.contents)
                base[event.start_index].append(this_str)
                for i in range(event.start_index + 1, event.end_index):
                    contexts[i].append(this_str)

        return self.compress_strings(base), self.compress_strings(contexts)

    def _process_hed(self, hed, remove_types=[], remove_defs=[], remove_group=False):
        if not hed:
            return ""
        # Reconvert even if hed is already a HedString to make sure a copy and expandable.
        hed_obj = HedString(str(hed), hed_schema=self.hed_schema, def_dict=self.def_dict)
        hed_obj, temp1 = split_base_tags(hed_obj, remove_types, remove_group=remove_group)
        if remove_defs:
            hed_obj, temp2 = split_def_tags(hed_obj, remove_defs, remove_group=remove_group)
        return str(hed_obj)

    def str_list_to_hed(self, str_list):
        """ Create a HedString object from a list of strings.

        Parameters:
            str_list (list): A list of strings to be concatenated with commas and then converted.

        Returns:
            HedString or None:  The converted list.

        """
        filtered_list = [item for item in str_list if item != '']  # list of strings
        if not filtered_list:  # empty lists don't contribute
            return None
        return HedString(",".join(filtered_list), self.hed_schema, def_dict=self.def_dict)

    @staticmethod
    def compress_strings(list_to_compress):
        result_list = ["" for _ in range(len(list_to_compress))]
        for index, item in enumerate(list_to_compress):
            if item:
                result_list[index] = ",".join(item)
        return result_list

    def get_type_defs(self, types):
        """ Return a list of definition names (lower case) that correspond to one of the specified types.

        Parameters:
            types (list):  List of tags that are treated as types such as 'Condition-variable'

        Returns:
            list:  List of definition names (lower-case) that correspond to the specified types

        """
        def_list = []
        for this_type in types:
            type_defs = HedTypeDefs(self.def_dict, type_tag=this_type)
            def_list = def_list + list(type_defs.def_map.keys())
        return def_list

    # @staticmethod
    # def fix_list(hed_list, hed_schema, as_string=False):
    #     for index, item in enumerate(hed_list):
    #         if not item:
    #             hed_list[index] = None
    #         elif as_string:
    #             hed_list[index] = ",".join(str(item))
    #         else:
    #             hed_list[index] = HedString(",".join(str(item)), hed_schema)
    #     return hed_list
