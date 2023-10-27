from hed.models import HedGroup


class TemporalEvent:
    """ Represents an event process with starting and ending.

    Note:  the contents have the Onset and duration removed.
    """
    def __init__(self, contents, start_index, start_time):
        if not contents:
            raise(ValueError, "A temporal event must have contents")
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
        self.end_index = end_index
        self.end_time = end_time

    def _split_group(self, contents):
        to_remove = []
        for item in contents.children:
            if isinstance(item, HedGroup):
                self.internal_group = item
            elif item.short_base_tag.lower() == "onset":
                to_remove.append(item)
            elif item.short_base_tag.lower() == "duration":
                to_remove.append(item)
                self.end_time = self.short_time + float(item.extension.lower())  # Will need to be fixed for units
            elif item.short_base_tag.lower() == "def":
                self.anchor = item.short_tag
        contents.remove(to_remove)
        if self.internal_group:
            self.contents = contents
        else:
            self.contents = self.anchor

    def __str__(self):
        return f"[{self.start_index}:{self.end_index}] anchor:{self.anchor} contents:{self.contents}"
