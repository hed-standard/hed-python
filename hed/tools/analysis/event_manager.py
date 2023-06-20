""" Manages context and events of temporal extent. """

from hed.schema import HedSchema, HedSchemaGroup
from hed.tools.analysis.temporal_event import TemporalEvent
from hed.models.model_constants import DefTagNames
from hed.models.df_util import get_assembled


class EventManager:

    def __init__(self, data, schema):
        """ Create an event manager for an events file.

        Parameters:
            data (TabularInput): A tabular input file.
            schema (HedSchema): A HED schema

        :raises HedFileError:
            - if there are any unmatched offsets.

        """

        if not isinstance(schema, HedSchema) and not isinstance(schema, HedSchemaGroup):
            raise ValueError("ContextRequiresSchema", f"Context manager must have a valid HedSchema of HedSchemaGroup")
        self.schema = schema
        self.data = data
        self.event_list = [[] for _ in range(len(self.data.dataframe))]
        self.hed_strings = [None for _ in range(len(self.data.dataframe))]
        self.onset_count = 0
        self.offset_count = 0
        self.contexts = []
        self._create_event_list()

    def iter_context(self):
        """ Iterate rows of context.

        Yields:
            int:  position in the dataFrame
            HedStringGroup: Context

        """

        for index in range(len(self.contexts)):
            yield index, self.contexts[index]

    def _create_event_list(self):
        """ Create a list of events of extended duration.

        :raises HedFileError:
            - If the hed_strings contain unmatched offsets.

        """

        # self.hed_strings = [HedString(str(hed), hed_schema=hed_schema) for hed in hed_strings]
        # hed_list = list(self.data.iter_dataframe(hed_ops=[self.hed_schema], return_string_only=False,
        #                                     expand_defs=False, remove_definitions=True))

        onset_dict = {}
        event_index = 0
        self.hed_strings, definitions = get_assembled(self.data, self.data._sidecar, self.schema, extra_def_dicts=None,
                                                      join_columns=True, shrink_defs=True, expand_defs=False)
        for hed in self.hed_strings:
            # to_remove = []  # tag_tuples = hed.find_tags(['Onset'], recursive=False, include_groups=1)
            group_tuples = hed.find_top_level_tags(anchor_tags={DefTagNames.ONSET_KEY, DefTagNames.OFFSET_KEY},
                                                   include_groups=2)
            for tup in group_tuples:
                group = tup[1]
                anchor_tag = group.find_def_tags(recursive=False, include_groups=0)[0]
                anchor = anchor_tag.extension.lower()
                if anchor in onset_dict or tup[0].short_base_tag.lower() == "offset":
                    temporal_event = onset_dict.pop(anchor)
                    temporal_event.set_end(event_index, self.data.dataframe.loc[event_index, "onset"])
                if tup[0] == DefTagNames.ONSET_KEY:
                    new_event = TemporalEvent(tup[1], event_index, self.data.dataframe.loc[event_index, "onset"])
                    self.event_list[event_index].append(new_event)
                    onset_dict[anchor] = new_event
                # to_remove.append(tup[1])
            # hed.remove(to_remove)
            event_index = event_index + 1

        # Now handle the events that extend to end of list
        for item in onset_dict.values():
            item.set_end(len(self.data.dataframe), None)

    def _set_event_contexts(self):
        """ Creates an event context for each hed string.

        Notes:
            The event context would be placed in a event context group, but is kept in a separate array without the
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
