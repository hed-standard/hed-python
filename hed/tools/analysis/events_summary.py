import os
from hed import TabularInput
from hed.errors import ErrorHandler
from hed.schema import load_schema_version
from hed.errors.error_types import TagQualityErrors
from hed.tools.analysis.event_checker import EventsChecker


class EventsSummary:
    # Excluding tags for condition-variables and task -- these can be done separately if we want to.
    REMOVE_TYPES = ['Condition-variable', 'Task']
    # Tags organized by whether they are found with either of these
    MATCH_TYPES = ['Experimental-stimulus', 'Participant-response', 'Cue', 'Feedback', 'Instructional', 'Sensory-event', 'Agent-action']

    # If a tag has any of these as a parent, it is excluded
    EXCLUDED_PARENTS = {'data-marker', 'data-resolution', 'quantitative-value', 'spatiotemporal-value',
                        'statistical-value', 'informational-property', 'organizational-property',
                        'grayscale', 'hsv-color', 'rgb-color', 'luminance', 'luminance-contrast', 'opacity',
                        'task-effect-evidence', 'task-relationship', 'relation'}

    # If a tag has any of these as a parent, it is replaced by this parent only
    CUTOFF_TAGS = {'blue-color', 'brown-color', 'cyan-color', 'gray-color', 'green-color', 'orange-color',
                   'pink-color', 'purple-color', 'red-color', 'white-color', 'yellow-color',
                   'visual-presentation'}

    # These tags are removed at the end as non-informational
    FILTERED_TAGS = {'event', 'agent', 'action', 'move-body-part', 'item', 'biological-item', 'anatomical-item',
                     'body-part',
                     'lower-extremity-part', 'upper-extremity-part', 'head-part', 'torso-part', 'face-part',
                     'language-item', 'object', 'geometric-object',
                     'man-made-object', 'device', 'computing-device', 'io-device', 'input-device', 'output-device',
                     'auditory-device', 'display-device',
                     'recording-device', 'natural-object', 'document', 'media', 'media-clip', 'visualization',
                     'property', 'agent-property', 'agent-state',
                     'agent-cognitive-state', 'agent-emotional-state', 'agent-physiological-state',
                     'agent-postural-state',
                     'agent-task-role', 'agent-trait',
                     'data-property', 'biological-artifact', 'nonbiological-artifact',
                     'spatial-property', 'temporal-property', 'spectral-property', 'dara-source-type', 'data-value',
                     'categorical-value', 'categorical-class-value', 'categorical-judgment-value',
                     'categorical-level-value', 'categorical-location-value', 'categorical-orientation-value',
                     'physical-value', 'data-variability-attribute', 'environmental-property', 'sensory-property',
                     'sensory-attribute', 'auditory-attribute', 'gustatory-attribute', 'olfactory-attribute',
                     'tactile-attribute', 'visual-attribute', 'sensory-presentation', 'task-property',
                     'task-action-type',
                     'task-attentional-demand', 'task-event-role', 'task-stimulus-role'}

    def __init__(self, hed_schema, file, sidecar=None, name=None):
        """ Constructor for the HedString class."""
        self.checker = None
        self.fatal_errors = False
        self._initialize(hed_schema, file, sidecar, name)

    def _initialize(self, hed_schema, file, sidecar, name):
        self.input_data = TabularInput(file, sidecar, name)
        errors = self.input_data.validate(hed_schema, error_handler=ErrorHandler(check_for_warnings=False))
        if errors:
            self.fatal_errors=True
            return
        self.checker = EventsChecker(hed_schema, self.input_data, name)
        self.issues = self.checker.validate_event_tags()
        self.error_lines = EventsChecker.get_error_lines(self.issues)

    def extract_tag_summary(self):
        """ Extract a summary of the tags in a given tabular input file.

        Returns:
            tuple[dict, list]:
            - dict: A dictionary with the summary information - (str, list)
            - list: A set of tags that do not match any of the specified types but are not excluded.
        """

        group_dict = {key: set() for key in self.MATCH_TYPES}
        other = set()
        group_error_lines = self.error_lines.get(TagQualityErrors.IMPROPER_EVENT_GROUPS, [])
        for index, hed_obj in enumerate(self.checker.hed_objs):
            if not hed_obj or index in group_error_lines:
                continue
            all_tags = hed_obj.get_all_tags()
            found = False
            for key, tags in group_dict.items():
                if self.match_tags(all_tags, key):
                    group_dict[key] = self.update_tags(group_dict[key], all_tags)
                    found = True
                    break
            if not found:
                other = self.update_tags(other, all_tags)

        for key, tags in group_dict.items():
            group_dict[key] = sorted(tags - self.FILTERED_TAGS)
        other = sorted(other - self.FILTERED_TAGS)
        return group_dict, other

    @staticmethod
    def match_tags(all_tags, key):
        return any(tag.short_base_tag == key for tag in all_tags)

    def update_tags(self, tag_set, all_tags):
        for tag in all_tags:
            terms = tag.tag_terms
            if any(item in self.EXCLUDED_PARENTS for item in terms):
                continue
            match = next((item for item in terms if item in self.CUTOFF_TAGS), None)
            if match:
                tag_set.add(match)
            else:
                tag_set.update(tag.tag_terms)
        return tag_set


def summarize_tags(schema, tsv, sidecar, name):
    """ Summarize the tags in a given tabular input file.

    Parameters:
        schema: The HED schema to use for validation.
        tsv: The path to the input file.
        sidecar: The path to the sidecar file (optional).
        name: The name of the dataset (optional).

    Returns:
        tuple[dict, list]:
        - dict: A dictionary with the summary information - (str, list).
        - list: A set of tags that do not match any of the specified types but are not excluded.
    """
    events_summary = EventsSummary(schema, tsv, sidecar, name)
    if events_summary.fatal_errors:
        return None
    summary, others = events_summary.extract_tag_summary()
    return summary

