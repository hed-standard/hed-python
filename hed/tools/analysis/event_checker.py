import os
from hed import load_schema_version, get_printable_issue_string
from hed.tools.analysis.event_manager import EventManager
from hed.errors.error_reporter import ErrorHandler, ErrorContext
from hed.errors.error_types import TagQualityErrors
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.hed_tag_manager import HedTagManager

class EventChecker:
    EVENT_TAGS = {'Event', 'Sensory-event', 'Agent-action', 'Data-feature', 'Experiment-control',
                  'Experiment-structure', 'Measurement-event'}
    NON_TASK_EVENTS = {'Data-feature', 'Experiment-control', 'Experiment-structure', 'Measurement-event'}
    TASK_ROLES = {'Experimental-stimulus', 'Participant-response', 'Incidental', 'Instructional', 'Mishap',
                  'Task-activity', 'Warning'}
    ACTION_ROLES = {'Appropriate-action', 'Correct-action', 'Correction', 'Done-indication',
                   'Imagined-action', 'Inappropriate-action', 'Incorrect-action', 'Indeterminate-action', 'Miss',
                   'Near-miss', 'Omitted-action', 'Ready-indication'}
    STIMULUS_ROLES = {'Cue', 'Distractor', 'Expected', 'Extraneous', 'Feedback', 'Go-signal', 'Meaningful',
                      'Newly-learned', 'Non-informative', 'Non-target', 'Not-meaningful', 'Novel', 'Oddball',
                      'Penalty', 'Planned', 'Priming', 'Query', 'Reward', 'Stop-signal', 'Target', 'Threat',
                      'Timed', 'Unexpected', 'Unplanned'}

    ALL_ROLES = TASK_ROLES.union(ACTION_ROLES).union(STIMULUS_ROLES)

    def __init__(self, hed_obj, line_number, error_handler=None):
        """ Constructor for the EventChecker class.

        Parameters:
            hed_obj (HedString): The HED string to check.
            line_number (int or None): The index of the HED string in the file.
            error_handler (ErrorHandler): The ErrorHandler object to use for error handling.

        """
        self.hed_obj = hed_obj
        self.line_number = line_number
        if error_handler is None:
            self.error_handler = ErrorHandler()
        else:
            self.error_handler = error_handler
        self.issues = self._verify_events(self.hed_obj)
        self.group_error = any(issue['code'] == TagQualityErrors.IMPROPER_TAG_GROUPING for issue in self.issues)

    def _verify_events(self, hed_obj):
        """ Verify that the events in the HED string are properly grouped.

        Parameters:
            hed_obj (HedString): The HED string to verify.

        Returns:
            list: list of issues
        """
        if not hed_obj:
            return []
        hed_groups = [hed_obj]  # Initialize with the top-level HedGroup
        while len(hed_groups) > 0:
            issues = self._check_grouping(hed_groups)
            if issues:
                return issues
        return []

    def _check_grouping(self, hed_groups):
        """ Check for event tagging errors in a group.

        Parameters:
            hed_groups (list): A list of the HED Groups to check.

        Returns:
            list: list of issues

        """
        group = hed_groups.pop()
        all_tags = group.get_all_tags()
        event_tags = [tag.short_base_tag for tag in all_tags if tag.short_base_tag in self.EVENT_TAGS]
        if not event_tags:
            return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.MISSING_EVENT_TYPE,
                                                           string=str(group), line=self.line_number)
        if len(event_tags) == 1:
            return self._check_task_role(group, event_tags[0], all_tags)

        # At this point, we know we have multiple event tags in the group.
        if any(tag.short_base_tag in event_tags for tag in group.tags()):
            return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.IMPROPER_TAG_GROUPING,
                                                          string=str(group), line=self.line_number,
                                                          event_types =', '.join(event_tags))
        hed_groups.extend(group.groups())
        return []

    def _check_task_role(self, hed_group, event_tag, all_tags):
        """ Check that a group with a single event tag has at least one task role tag.

        Parameters:
            hed_group (HedGroup): The HED group to check (should have a single event tag).
            event_tag (str): The single event tag associated with the group.
            all_tags (list): A list of all the HedTag objects in the group.

        Returns:
            list: list of issues

        ."""

        if event_tag in self.NON_TASK_EVENTS:
            return []
        has_task_role = any(tag.short_base_tag in self.TASK_ROLES for tag in all_tags)
        if has_task_role:
            return []
        if event_tag == 'Agent-action' and any(tag.short_base_tag in self.ACTION_ROLES for tag in all_tags):
            return []

        if event_tag == 'Sensory-event' and any(tag.short_base_tag in self.STIMULUS_ROLES for tag in all_tags):
            return []

        return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.MISSING_TASK_ROLE,
                                                      event_type=event_tag, string=str(hed_group),
                                                      line=self.line_number)

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
        """ Constructor for the HedString class.

        Parameters:
            hed_schema (HedSchema): The HedSchema object to use for the summary.
            file (str or FileLike or pd.Dataframe): A tsv file to open.
            sidecar (str or Sidecar or FileLike): A Sidecar or source file/filename.
            name (str): The name to display for this file for error purposes.


        """
        self._schema = hed_schema
        self.name = name
        if name is None and isinstance(file, str):
            self.name = file
        self.hed_objs = self._initialize_hed(file, sidecar, name)
        self.group_error_lines = []
        self.missing_error_lines = []

    def _initialize_hed(self, file, sidecar, name):
        input_data = TabularInput(file, sidecar, name=name)
        event_manager = EventManager(input_data, self._schema)
        tag_man = HedTagManager(event_manager, remove_types=self.REMOVE_TYPES)
        return tag_man.get_hed_objs(include_context=False, replace_defs=True)

    def validate_event_tags(self):
        """ Verify that the events in the HED strings validly represent events.

        Returns:
            dict: A dictionary with the summary information.
            set: A set of tags that do not match any of the specified types but are not excluded.
        """
        all_issues = []
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.FILE_NAME, self.name)
        for index, hed_obj in enumerate(self.hed_objs):
            if not hed_obj:
                continue
            event_check = EventChecker(hed_obj, index, error_handler)
            if event_check.group_error:
                self.group_error_lines.append(index)
            if event_check.issues:
                self.missing_error_lines.append(index)
                all_issues += event_check.issues
        return all_issues

    def extract_tag_summary(self):
        """ Extract a summary of the tags in a given tabular input file.

        Returns:
            dict: A dictionary with the summary information - (str, list)
            list: A set of tags that do not match any of the specified types but are not excluded.
        """

        group_dict = {key: set() for key in self.MATCH_TYPES}
        other = set()

        for index, hed_obj in enumerate(self.hed_objs):
            if not hed_obj or index in self.group_error_lines:
                continue
            all_tags = hed_obj.get_all_tags()
            if index in self.missing_error_lines:
                other = self.update_tags(other, all_tags)
                continue
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


if __name__ == '__main__':
    schema = load_schema_version('8.4.0')

    # # Wakeman Henson example
    # root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds003645s_hed'
    # sidecar_path = os.path.join(root_dir, 'task-FacePerception_events.json')
    # tsv_path = os.path.join(root_dir, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
    # data_name = 'eeg_ds003645s_hed'

    # # Attention shift example
    # root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds002893s_hed_attention_shift'
    # sidecar_path = os.path.join(root_dir, 'task-AuditoryVisualShift_events.json')
    # tsv_path = os.path.join(root_dir, 'sub-002/eeg/sub-002_task-AuditoryVisualShift_run-01_events.tsv')
    # data_name = 'eeg_ds002893s_hed_attention_shift'

    # Sternberg example
    root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds004117s_hed_sternberg'
    sidecar_path = os.path.join(root_dir, 'task-WorkingMemory_events.json')
    tsv_path = os.path.join(root_dir, 'sub-001/ses-01/eeg/sub-001_ses-01_task-WorkingMemory_run-1_events.tsv')
    data_name = 'eeg_ds004117s_hed_sternberg'

    # Create the event summary
    events_summary = EventsSummary(schema, tsv_path, sidecar_path, data_name)

    # Check the validity of the event tags
    issues = events_summary.validate_event_tags()
    if issues:
        print(f"Errors found in {get_printable_issue_string(issues, '')}")
    else:
        print(f"No errors found in {data_name}.")

    # Extract the tag summary
    tag_dict, others = events_summary.extract_tag_summary()

    for the_key, the_item in tag_dict.items():
        if not the_item:
            continue
        print(f"{the_key}:")
        for tag in the_item:
            print(f"  {tag}")

    print("Other:")
    for tag in others:
        print(f"  {tag}")