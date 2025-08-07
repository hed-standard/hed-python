""" Manager of events of temporal extent. """
import pandas as pd
import bisect

from hed.errors.exceptions import HedFileError
from hed.models.hed_string import HedString
from hed.models.model_constants import DefTagNames
from hed.models import df_util
from hed.models import string_util
from hed.tools.analysis.temporal_event import TemporalEvent
from hed.tools.analysis.hed_type_defs import HedTypeDefs


class EventManager:
    """ Manager of events of temporal extent. """

    def __init__(self, input_data, hed_schema, extra_defs=None):
        """ Create an event manager for an events file. Manages events of temporal extent.

        Parameters:
            input_data (TabularInput): Represents an events file with its sidecar.
            hed_schema (HedSchema): HED schema used.
            extra_defs (DefinitionDict):  Extra definitions not included in the input_data information.

        Raises:
            HedFileError: If there are any unmatched offsets.

        Notes:  Keeps the events of temporal extend by their starting index in events file. These events
        are separated from the rest of the annotations, which are contained in self.hed_strings.

        """
        if input_data.onsets is not None and input_data.needs_sorting:
            raise HedFileError("OnsetsNotOrdered", "Events must have numeric non-decreasing onset values", "")
        self.hed_schema = hed_schema
        self.input_data = input_data
        self.def_dict = input_data.get_def_dict(hed_schema, extra_def_dicts=extra_defs)
        self.onsets = None  # list of onset times or None if not an events file
        self.original_index = None  # list of original indices of the events
        self.base = None  # list of strings containing the starts of event processes
        self.context = None  # list of strings containing the contexts of event processes
        self.hed_strings = None  # list of HedString objects without the temporal events
        self.event_list = None
        self._create_event_list(input_data)

    def _create_event_list(self, input_data):
        """ Populate the event_list with the events with temporal extent indexed by event number.

        Parameters:
            input_data (TabularInput): A tabular input that includes its relevant sidecar.

        Raises:
            HedFileError: If the hed_strings contain unmatched offsets.

        Notes:

        """
        hed_strings = input_data.series_a
        df_util.shrink_defs(hed_strings, self.hed_schema)
        if input_data.onsets is None:
            self.hed_strings = [HedString(hed_string, self.hed_schema) for hed_string in hed_strings]
            return
        delay_df = df_util.split_delay_tags(hed_strings, self.hed_schema, input_data.onsets)

        hed_strings = [HedString(hed_string, self.hed_schema) for hed_string in delay_df.HED]
        self.onsets = pd.to_numeric(delay_df.onset, errors='coerce')
        self.original_index = pd.to_numeric(delay_df.original_index, errors='coerce')
        self.event_list = [[] for _ in range(len(hed_strings))]
        onset_dict = {}  # Temporary dictionary keeping track of temporal events that haven't ended yet.
        for event_index, hed in enumerate(hed_strings):
            self._extract_temporal_events(hed, event_index, onset_dict)
            self._extract_duration_events(hed, event_index)
        # Now handle the events that extend to end of list
        for item in onset_dict.values():
            item.set_end(len(self.onsets), None)
        self.hed_strings = hed_strings
        self._extract_context()

    def _extract_duration_events(self, hed, event_index):
        groups = hed.find_top_level_tags(anchor_tags={DefTagNames.DURATION_KEY})
        to_remove = []
        for duration_tag, group in groups:
            start_time = self.onsets[event_index]
            new_event = TemporalEvent(group, event_index, start_time)
            end_time = new_event.end_time
            # Todo: This may need updating.  end_index==len(self.onsets) in the edge
            end_index = bisect.bisect_left(self.onsets, end_time)
            new_event.set_end(end_index, end_time)
            self.event_list[event_index].append(new_event)
            to_remove.append(group)
        hed.remove(to_remove)

    def _extract_temporal_events(self, hed, event_index, onset_dict):
        """ Extract the temporal events and remove them from the other HED strings.

        Parameters:
            hed (HedString):  The assembled HedString at position event_index in the data.
            event_index (int): The position of this string in the data.
            onset_dict (dict):  Running dict that keeps track of temporal events that haven't yet ended.

        Note:
            This removes the events of temporal extent from HED.

         """
        if not hed:
            return
        group_tuples = hed.find_top_level_tags(anchor_tags={DefTagNames.ONSET_KEY, DefTagNames.OFFSET_KEY},
                                               include_groups=2)

        to_remove = []
        for def_tag, group in group_tuples:
            anchor_tag = group.find_def_tags(recursive=False, include_groups=0)[0]
            anchor = anchor_tag.extension.casefold()
            if anchor in onset_dict or def_tag == DefTagNames.OFFSET_KEY:
                temporal_event = onset_dict.pop(anchor)
                temporal_event.set_end(event_index, self.onsets[event_index])
            if def_tag == DefTagNames.ONSET_KEY:
                new_event = TemporalEvent(group, event_index, self.onsets[event_index])
                self.event_list[event_index].append(new_event)
                onset_dict[anchor] = new_event
            to_remove.append(group)
        hed.remove(to_remove)

    def unfold_context(self, remove_types=[]):
        """ Unfold the event information into a tuple based on context.

        Parameters:
            remove_types (list):  List of types to remove.

        Returns:
            tuple[Union[list(str),  HedString], Union[list(str),  HedString, None], Union[list(str),  HedString, None]]:
            Union[list(str),  HedString]: The information without the events of temporal extent.
            Union[list(str),  HedString, None]: The onsets of the events of temporal extent.
            Union[list(str),  HedString, None]: The ongoing context information.

        """

        remove_defs = self.get_type_defs(remove_types)  # definitions corresponding to remove types to be filtered out
        new_hed = ["" for _ in range(len(self.hed_strings))]
        for index, item in enumerate(self.hed_strings):
            new_hed[index] = self._filter_hed(item, remove_types=remove_types,
                                              remove_defs=remove_defs, remove_group=False)
        if self.onsets is None:
            return new_hed, None, None
        new_base, new_contexts = self._get_base_contexts(remove_types, remove_defs)
        return new_hed, new_base, new_contexts

    def _get_base_contexts(self, remove_types, remove_defs):
        """ Expand the context and filter to remove specified types.

        Parameters:
            remove_types (list):  List of types to remove.
            remove_defs (list):  List of definitions to remove.

        """
        new_base = ["" for _ in range(len(self.hed_strings))]
        new_contexts = ["" for _ in range(len(self.hed_strings))]
        for index, item in enumerate(self.hed_strings):
            new_base[index] = self._filter_hed(self.base[index], remove_types=remove_types,
                                               remove_defs=remove_defs, remove_group=True)
            new_contexts[index] = self._filter_hed(self.contexts[index], remove_types=remove_types,
                                                   remove_defs=remove_defs, remove_group=True)
        return new_base, new_contexts   # these are each a list of strings

    def _extract_context(self):
        """ Expand the onset and the ongoing context for additional processing.

        Notes: For each event, the Onset goes in the base list and the remainder of the times go in the contexts list.

        """
        base = [[] for _ in range(len(self.hed_strings))]
        contexts = [[] for _ in range(len(self.hed_strings))]
        for events in self.event_list:
            for event in events:
                this_str = str(event.contents)
                base[event.start_index].append(this_str)
                for i in range(event.start_index + 1, event.end_index):
                    contexts[i].append(this_str)
        self.base = self.compress_strings(base)
        self.contexts = self.compress_strings(contexts)

    def _filter_hed(self, hed, remove_types=[], remove_defs=[], remove_group=False):
        """ Remove types and definitions from a HED string.

        Parameters:
            hed (string or HedString): The HED string to be filtered.
            remove_types (list): List of HED tags to filter as types (usually Task and Condition-variable).
            remove_defs (list): List of definition names to filter out.
            remove_group (bool): (Default False) Whether to remove the groups included when removing.

        Returns:
            str: The resulting filtered HED string.

        """
        if not hed:
            return ""
        # Reconvert even if HED is already a HedString to make sure a copy and expandable.
        hed_obj = HedString(str(hed), hed_schema=self.hed_schema, def_dict=self.def_dict)
        hed_obj, temp1 = string_util.split_base_tags(hed_obj, remove_types, remove_group=remove_group)
        if remove_defs:
            hed_obj, temp2 = string_util.split_def_tags(hed_obj, remove_defs, remove_group=remove_group)
        return str(hed_obj)

    def str_list_to_hed(self, str_list):
        """ Create a HedString object from a list of strings.

        Parameters:
            str_list (list): A list of strings to be concatenated with commas and then converted.

        Returns:
            Union[HedString, None]:  The converted list.

        """
        filtered_list = [item for item in str_list if item != '']  # list of strings
        if not filtered_list:  # empty lists don't contribute
            return None
        return HedString(",".join(filtered_list), self.hed_schema, def_dict=self.def_dict)

    def get_type_defs(self, types):
        """ Return a list of definition names (lower case) that correspond to any of the specified types.

        Parameters:
            types (list or None):  List of tags that are treated as types such as 'Condition-variable'

        Returns:
            list:  List of definition names (lower-case) that correspond to the specified types

        """
        def_list = []
        if not types:
            return def_list
        for this_type in types:
            type_defs = HedTypeDefs(self.def_dict, type_tag=this_type)
            def_list = def_list + list(type_defs.def_map.keys())
        return def_list

    @staticmethod
    def compress_strings(list_to_compress):
        """ Compress a list of lists of strings into a single str with comma-separated elements.

        Parameters:
            list_to_compress (list):  List of lists of HED str to turn into a list of single HED strings.

        Returns:
            list: List of same length as list_to_compress with each entry being a str.

        """
        result_list = ["" for _ in range(len(list_to_compress))]
        for index, item in enumerate(list_to_compress):
            if item:
                result_list[index] = ",".join(item)
        return result_list
