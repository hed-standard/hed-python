""" Manages context and events of temporal extent. """

from hed.errors.exceptions import HedFileError
from hed.models import HedGroup, HedString
from hed.schema import HedSchema, HedSchemaGroup
from hed.tools.analysis.analysis_util import hed_to_str


class OnsetGroup:
    def __init__(self, name, contents, start_index, end_index=None):
        self.name = name
        self.start_index = start_index
        self.end_index = end_index
        self.contents = hed_to_str(contents, remove_parentheses=True)

    def __str__(self):
        return f"{self.name}:[events {self.start_index}:{self.end_index} contents:{self.contents}]"


class HedContextManager:

    def __init__(self, hed_strings, hed_schema):
        """ Create an context manager for an events file.

        Parameters:
            hed_strings (list): A list of hed_strings to be managed.

        Raises:
            HedFileError: if there are any unmatched offsets.

        Notes:
            The constructor has the side-effect of splitting each element of the hed_strings list into two
            by removing the Offset groups and the Onset tags. The context has the temporal extent information.
            For users wanting to use only Onset events, self.hed_strings contains the information.

        """

        self.hed_strings = [HedString(str(hed), hed_schema=hed_schema) for hed in hed_strings]
        if not isinstance(hed_schema, HedSchema) and not isinstance(hed_schema, HedSchemaGroup):
            raise ValueError("ContextRequiresSchema", f"Context manager must have a valid HedSchema of HedSchemaGroup")
        self.hed_schema = hed_schema
        self.onset_list = []
        self.onset_count = 0
        self.offset_count = 0
        self.contexts = []
        self._create_onset_list()
        self._set_event_contexts()

    def iter_context(self):
        """ Iterate rows of context.

        Yields:
            HedString:  The HedString.
            HedStringGroup: Context

        """

        for index in range(len(self.hed_strings)):
            yield self.hed_strings[index], self.contexts[index]

    def _create_onset_list(self):
        """ Create a list of events of extended duration.

        Raises:
            HedFileError: If the hed_strings contain unmatched offsets.

        """

        self.onset_list = []
        onset_dict = {}
        for event_index, hed in enumerate(self.hed_strings):
            to_remove = []  # tag_tuples = hed.find_tags(['Onset'], recursive=False, include_groups=1)
            onset_tuples = hed.find_tags(["onset"], recursive=True, include_groups=2)
            self.onset_count += len(onset_tuples)
            for tup in onset_tuples:
                group = tup[1]
                group.remove([tup[0]])
                self._update_onset_list(group, onset_dict, event_index, is_offset=False)
            offset_tuples = hed.find_tags(["offset"], recursive=True, include_groups=2)
            self.offset_count += len(offset_tuples)
            for tup in offset_tuples:
                group = tup[1]
                to_remove.append(group)
                self._update_onset_list(group, onset_dict, event_index, is_offset=True)
            hed.remove(to_remove)

        # Now handle the events that extend to end of list
        for key, value in onset_dict.items():
            value.end_index = len(self.hed_strings)
            self.onset_list.append(value)

    def _set_event_contexts(self):
        """ Creates an event context for each hed string.

        Notes:
            The event context would be placed in a event context group, but is kept in a separate array without the
            event context group or tag.

        """
        contexts = [[] for _ in range(len(self.hed_strings))]
        for onset in self.onset_list:
            for i in range(onset.start_index+1, onset.end_index):
                contexts[i].append(onset.contents)
        for i in range(len(self.hed_strings)):
            contexts[i] = HedString(",".join(contexts[i]), hed_schema=self.hed_schema)
        self.contexts = contexts

    def _update_onset_list(self, group, onset_dict, event_index, is_offset=False):
        """ Process one onset or offset group to create onset_list.

        Parameters:
            group (HedGroup):  The HedGroup containing the onset or offset.
            onset_dict (dict): A dictionary of OnsetGroup objects that keep track of span of an event.
            event_index (int): The event number in the list.
            is_offset (bool):  True if processing an offset.

        Raises:
            HedFileError if an unmatched offset is encountered.

        Notes:
            - Modifies onset_dict and onset_list.
        """
        def_tags = group.find_def_tags(recursive=False, include_groups=0)
        name = def_tags[0].extension_or_value_portion
        onset_element = onset_dict.pop(name, None)
        if onset_element:
            onset_element.end_index = event_index
            self.onset_list.append(onset_element)
        elif is_offset:
            raise HedFileError("UnmatchedOffset", f"Unmatched {name} offset at event {event_index}", " ")
        if not is_offset:
            onset_element = OnsetGroup(name, group, event_index)
            onset_dict[name] = onset_element
