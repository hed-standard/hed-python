from hed.errors import HedFileError
from hed.schema import load_schema_version


class OnsetGroup:
    def __init__(self, name, start_index, end_index=None, contents=None):
        self.name = name
        self.start_index = start_index
        self.end_index = end_index
        self.contents = contents

    def __str__(self):
        return f"{self.name}:[{self.start_index}, {self.end_index}] contents {str(self.contents)}"


class OnsetManager:

    def __init__(self, hed_strings, hed_schema):
        """ Create an onset manager for an events file.

        Args:
            hed_strings (list): A list of hed_strings to be managed.
            hed_schema (HedSchema or HedSchemaGroup): The HED schema to use.

        Raises:
            HedFileError: if there are any unmatched offsets.

        """

        self.hed_schema = hed_schema
        self.hed_strings = hed_strings
        self.onset_list = []
        self.contexts = []
        self._create_onset_list()
        self._set_event_contexts()

    def _create_onset_list(self):
        """ Create a list of events of extended duration.

        Raises:
            HedFileError if the hed_strings contain unmatched offsets.

        """

        self.onset_list = []
        onset_dict = {}
        for event_index, hed in enumerate(self.hed_strings):
            to_remove = []  # tag_tuples = hed.find_tags(['Onset'], recursive=False, include_groups=1)
            onset_tuples = hed.find_tags(["onset"], recursive=True, include_groups=2)
            for tup in onset_tuples:
                group = tup[1]
                group.remove([tup[0]])
                self._update_onset_list(group, onset_dict, event_index, is_offset=False)
            offset_tuples = hed.find_tags(["offset"], recursive=True, include_groups=2)
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
        contexts = [0]*len(self.hed_strings)
        for i in range(len(self.hed_strings)):
            contexts[i] = []
        for onset in self.onset_list:
            for i in range(onset.start_index+1, onset.end_index):
                contexts[i].append(onset.contents)
        self.contexts = contexts

    def _update_onset_list(self, group, onset_dict, event_index, is_offset=False):
        """ Process one onset or offset group to create onset_list.

        Args:
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
            raise HedFileError("Unmatched offset", f"Unmatched {name} offset at event {event_index}", " ")
        if not is_offset:
            onset_element = OnsetGroup(name, event_index, contents=group)
            onset_dict[name] = onset_element


if __name__ == '__main__':
    from hed import HedString
    schema = load_schema_version(xml_version="8.1.0")
    test_strings1 = [HedString('Sensory-event,(Def/Cond1,(Red, Blue),Onset),(Def/Cond2,Onset),Green,Yellow',
                               hed_schema=schema),
                     HedString('(Def/Cond1, Offset)', hed_schema=schema),
                     HedString('White, Black, Condition-variable/Wonder, Condition-variable/Fast', hed_schema=schema),
                     HedString('', hed_schema=schema),
                     HedString('(Def/Cond2, Onset)', hed_schema=schema),
                     HedString('(Def/Cond3/4.3, Onset)', hed_schema=schema),
                     HedString('Arm, Leg, Condition-variable/Fast', hed_schema=schema)]
    manager = OnsetManager(test_strings1, schema)
