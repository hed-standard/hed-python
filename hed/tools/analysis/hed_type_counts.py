
class HedTypeCount:
    """ Keeps a summary of one value of one type of variable.

    Parameters:
        type_value (str)  The value of the variable to be counted
        type_tag (str)   The type of variable.

    Examples:
        HedTypeCounts('SymmetricCond', 'condition-variable') keeps counts of Condition-variable/Symmetric

    """

    def __init__(self, type_value, type_tag):
        self.type_value = type_value
        self.type_tag = type_tag.lower()
        self.direct_references = 0
        self.total_events = 0
        self.events = 0
        self.files = {}
        self.multiple_events = 0
        self.multiple_event_maximum = 0
        self.level_counts = {}

    def update(self, type_sum, name=None):
        """ Update the counts from a HedTypeValues.

        Parameters:
            type_sum (dict): Information about the contents for a particular data file.
            name (str or None):  Name of the file associated with the counts.

        """

        self.direct_references += type_sum['direct_references']
        self.total_events += type_sum['total_events']
        self.events += type_sum['events']
        if name:
            self.files[name] = ''
        self.multiple_events += type_sum['multiple_events']
        self.multiple_event_maximum = max(self.multiple_event_maximum, type_sum['multiple_event_maximum'])
        self._update_levels(type_sum.get('level_counts', {}))

    def to_dict(self):
        return {'type_value': self.type_value, 'type_tag': self.type_tag,
                'direct_references': self.direct_references, 'total_events': self.total_events,
                'events': self.events, 'files': self.files, 'multiple_events': self.multiple_events,
                'multiple_event_maximum': self.multiple_event_maximum, 'level_counts': self.level_counts}

    def _update_levels(self, level_dict):
        for key, item in level_dict.items():
            if key not in self.level_counts:
                self.level_counts[key] = {'files': 0, 'events': 0, 'tags': '', 'description': ''}
            level_counts = self.level_counts[key]
            if not isinstance(item, dict):
                level_counts['files'] = level_counts['files'] + 1
                level_counts['events'] = level_counts['events'] + item
                continue
            level_counts['files'] = level_counts['files'] + item['files']
            level_counts['events'] = level_counts['events'] + item['events']
            if not level_counts['tags']:
                level_counts['tags'] = item['tags']
            if not level_counts['description']:
                level_counts['description'] = item['description']

    def get_summary(self):
        summary = {'type_value': self.type_value,
                   'type_tag': self.type_tag,
                   'levels': len(self.level_counts.keys()),
                   'direct_references': self.direct_references,
                   'total_events': self.total_events,
                   'events': self.events,
                   'multiple_events': self.multiple_events,
                   'multiple_event_maximum': self.multiple_event_maximum,
                   'files': list(self.files.keys())}
        if self.level_counts:
            summary['level_counts'] = self.level_counts
        return summary


class HedTypeCounts:
    """ Keeps a summary of tag counts for a file.


    """

    def __init__(self, type_tag="", name=""):
        self.name = name
        self.type_tag = type_tag
        self.type_dict = {}

    def update_summary(self, type_sum, file_id):
        """ Update this summary based on the type variable map.

        Parameters:
            type_sum (dict):  Contains the information about the value of a type.
            file_id (str):   Unique identifier for the associated file.
        """

        for type_val, type_counts in type_sum.items():
            if type_val not in self.type_dict:
                self.type_dict[type_val] = HedTypeCount(type_val, self.type_tag)
            val_counts = self.type_dict[type_val]
            val_counts.update(type_counts, file_id)

    def add_descriptions(self, type_defs):
        """ Update this summary based on the type variable map.

        Parameters:
            type_defs (HedTypeDefinitions):  Contains the information about the value of a type.

        """

        for type_val, type_count in self.type_dict.items():
            if type_val not in type_defs.type_map:
                continue
            for level in type_defs.type_map[type_val]:
                if level not in type_count.level_counts:
                    continue
                level_dict = type_defs.def_map[level]
                type_count.level_counts[level]['tags'] = level_dict['tags']
                type_count.level_counts[level]['description'] = level_dict['description']

    def update_dict(self, other_dict):
        for key, count in other_dict.items():
            if key not in self.type_dict:
                self.type_dict[key] = HedTypeCount(count.type_value, count.type_tag)
            this_count = self.type_dict[key]
            this_count.update(count.to_dict())

    def get_summary(self):
        details = {}
        for type_value, count in self.type_dict.items():
            details[type_value] = count.get_summary()
        return {'name': str(self.name), 'type tag': self.type_tag, 'details': details}
