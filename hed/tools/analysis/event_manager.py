""" Manages events of temporal extent. """

from hed.tools.analysis.temporal_event import TemporalEvent
from hed.models.model_constants import DefTagNames


class EventManager:

    def __init__(self, hed_strings, onsets, def_dict):
        """ Create an event manager for an events file. Manages events of temporal extent. This

        Parameters:
            data (TabularInput): A tabular input file.
            schema (HedSchema): A HED schema

        :raises HedFileError:
            - if there are any unmatched offsets.

        Notes:  Keeps the events of temporal extend by their starting index in events file. These events
        are separated from the rest of the annotations.

        """

        self.event_list = [[] for _ in range(len(onsets))]
        self.onsets = onsets
        self.hed_strings = hed_strings
        self.def_dict = def_dict
        self.contexts = []
        self._create_event_list()

    def iter_context(self):
        """ Iterate rows of context.

        Yields:
            int:  position in the dataFrame
            HedString: Context

        """

        for index in range(len(self.contexts)):
            yield index, self.contexts[index]

    def _create_event_list(self):
        """ Create a list of events of extended duration.

        :raises HedFileError:
            - If the hed_strings contain unmatched offsets.

        Notes:

        """
        onset_dict = {}  # Temporary dictionary keeping track of temporal events that haven't ended yet.
        for event_index, hed in enumerate(self.hed_strings):
            self._extract_temporal_events(hed, event_index, onset_dict)
        # Now handle the events that extend to end of list
        for item in onset_dict.values():
            item.set_end(len(self.onsets), None)

    def _extract_temporal_events(self, hed, event_index, onset_dict):
        """ Extract the temporal events and remove them from the other HED strings.

        Parameters:
            hed (HedString):  The assembled HedString at position event_index in the data.
            event_index (int): The position of this string in the data.
            onset_dict (dict):  Running dict that keeps track of temporal events that haven't yet ended.

        Note:
            This removes the events of temporal extent from the HED string.

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

    def _set_event_contexts(self):
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
        print("_set_event_contexts not implemented yet")

    def _update_onset_list(self, group, onset_dict, event_index):
        """ Process one onset or offset group to create onset_list.

        Parameters:
            group (HedGroup):  The HedGroup containing the onset or offset.
            onset_dict (dict): A dictionary of OnsetGroup objects that keep track of span of an event.
            event_index (int): The event number in the list.

        :raises HedFileError:
            - if an unmatched offset is encountered.

        Notes:
            - Modifies onset_dict and onset_list.
        """
        # def_tags = group.find_def_tags(recursive=False, include_groups=0)
        # name = def_tags[0].extension
        # onset_element = onset_dict.pop(name, None)
        # if onset_element:
        #     onset_element.end_index = event_index
        #     self.onset_list.append(onset_element)
        # elif is_offset:
        #     raise HedFileError("UnmatchedOffset", f"Unmatched {name} offset at event {event_index}", " ")
        # if not is_offset:
        #     onset_element = TemporalEvent(name, group, event_index)
        #     onset_dict[name] = onset_element
