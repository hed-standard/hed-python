""" A single event process with starting and ending times. """
from hed.models.hed_group import HedGroup
from hed.models.model_constants import DefTagNames


class TemporalEvent:
    """ A single event process with starting and ending times.

    Note:  the contents have the Onset and duration removed.
    """
    def __init__(self, contents, start_index, start_time):
        if not contents:
            raise ValueError("A temporal event must have contents")
        self.contents = None    # Must not have definition expanded if there is a definition.
        self.start_index = start_index
        self.start_time = float(start_time)
        self.end_index = None
        self.end_time = None
        self.anchor = None    # Lowercase def name with value
        self.internal_group = None
        self.insets = []
        self._split_group(contents)

    def set_end(self, end_index, end_time):
        """ Set end time information for an event process.

        Parameters:
            end_index (int): Position of ending event marker corresponding to the end of this event process.
            end_time (float): Ending time of the event (usually in seconds).

        """
        self.end_index = end_index
        self.end_time = end_time

    def _split_group(self, contents):
        to_remove = []
        for item in contents.children:
            if isinstance(item, HedGroup):
                self.internal_group = item
            elif item.short_base_tag == DefTagNames.ONSET_KEY:
                to_remove.append(item)
            elif item.short_base_tag == DefTagNames.DURATION_KEY:
                to_remove.append(item)
                self.end_time = self.start_time + item.value_as_default_unit()
            elif item.short_base_tag == DefTagNames.DEF_KEY:
                self.anchor = item.short_tag
        contents.remove(to_remove)
        if self.internal_group:
            self.contents = contents
        else:
            self.contents = self.anchor

    def __str__(self):
        """ Return a string representation of this event process.

        Returns:
            str: A string representation of this event process.

        """
        return f"[{self.start_index}:{self.end_index}] anchor:{self.anchor} contents:{self.contents}"
