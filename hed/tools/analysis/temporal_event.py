from hed.models import HedTag, HedGroup, HedString


class TemporalEvent:
    def __init__(self, event_group, start_index, start_time):
        self.event_group = event_group
        self.start_index = start_index
        self.start_time = start_time
        self.duration = None
        self.end_index = None
        self.end_time = None
        self.anchor = None
        self.internal_group = None
        self._split_group()
        
    def set_end(self, end_index, end_time):
        self.end_index = end_index
        self.end_time = end_time

    def _split_group(self):
        for item in self.event_group.children:
            if isinstance(item, HedTag) and (item.short_tag.lower() != "onset"):
                self.anchor = item.extension.lower()
            elif isinstance(item, HedTag):
                continue
            elif isinstance(item, HedGroup):
                self.internal_group = item

    def __str__(self):
        return f"{self.name}:[event markers {self.start_index}:{self.end_index} contents:{self.contents}]"
