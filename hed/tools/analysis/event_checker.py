from hed.errors.error_types import TagQualityErrors
from hed.errors import ErrorHandler, ErrorContext, sort_issues
from hed import TabularInput
from hed.tools import EventManager, HedTagManager


class EventChecker:
    EVENT_TAGS = {'Event', 'Sensory-event', 'Agent-action', 'Data-feature', 'Experiment-control',
                  'Experiment-structure', 'Measurement-event'}
    NON_TASK_EVENTS = {'Data-feature', 'Experiment-control', 'Experiment-structure', 'Measurement-event'}
    TASK_ROLES = {'Experimental-stimulus', 'Participant-response', 'Incidental', 'Instructional', 'Mishap',
                  'Task-activity', 'Warning', 'Cue', 'Feedback'}
    ACTION_ROLES = {'Appropriate-action', 'Correct-action', 'Correction', 'Done-indication',
                   'Imagined-action', 'Inappropriate-action', 'Incorrect-action', 'Indeterminate-action', 'Miss',
                   'Near-miss', 'Omitted-action', 'Ready-indication'}
    STIMULUS_ROLES = { 'Distractor', 'Expected', 'Extraneous', 'Go-signal', 'Meaningful',
                      'Newly-learned', 'Non-informative', 'Non-target', 'Not-meaningful', 'Novel', 'Oddball',
                      'Penalty', 'Planned', 'Priming', 'Query', 'Reward', 'Stop-signal', 'Target', 'Threat',
                      'Timed', 'Unexpected', 'Unplanned'}

    ALL_ROLES = TASK_ROLES.union(ACTION_ROLES).union(STIMULUS_ROLES)

    def __init__(self, hed_obj, line_number, original_line_number=None, error_handler=None):
        """ Constructor for the EventChecker class.

        Parameters:
            hed_obj (HedString): The HED string to check.
            line_number (int or None): The index of the HED string in the file.
            original_line_number (int or None): The original line number in the file.
            error_handler (ErrorHandler): The ErrorHandler object to use for error handling.

        """
        self.hed_obj = hed_obj
        self.line_number = line_number
        if original_line_number is None:
            self.original_line_number = line_number
        else:
            self.original_line_number = int(original_line_number)
        if error_handler is None:
            self.error_handler = ErrorHandler()
        else:
            self.error_handler = error_handler
        self.issues = self._verify_events(self.hed_obj)

    def _verify_events(self, hed_obj):
        """ Verify that the events in the HED string are properly grouped.

        Parameters:
            hed_obj (HedString): The HED string to verify.

        Returns:
            list: list of issues

        Errors are detected for the following cases:
            1. The HED string has no event tags.
            2. The HED string has multiple event tags that aren't in separate groups.
            3. The HED string has multiple event tags and a top-level group doesn't have an event tag.
            4. The HED string has no task role tags.
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
                                                           string=str(group), line=self.original_line_number)

        if len(event_tags) == 1:
            return self._check_event_group(group, event_tags[0], all_tags)

        # At this point, we know we have multiple event tags in the group.
        if any(tag.short_base_tag in event_tags for tag in group.tags()):
            return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.IMPROPER_EVENT_GROUPS,
                                                          string=str(group), line=self.original_line_number,
                                                          event_types =', '.join(event_tags))
        hed_groups.extend(group.groups())
        return []

    def _check_event_group(self, hed_group,  event_tag, all_tags):
        """ Check that a group with a single event tag has the right supporting tags

        Parameters:
            hed_group (HedGroup): The HED group to check (should have a single event tag).
            event_tag (str): The single event tag associated with the group.
            all_tags (list): A list of all the HedTag objects in the group.

        Returns:
            list: list of issues:

        """
        issues = self._check_task_role(hed_group, event_tag, all_tags)
        issues += self._check_presentation_modality(hed_group, event_tag, all_tags)
        issues += self._check_action_tags(hed_group, event_tag, all_tags)
        return issues

    def _check_task_role(self, hed_group, event_tag, all_tags):
        """ Check that a group with a single event tag has at least one task role tag unless it is a non-task event.

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
                                                      line=self.original_line_number)

    def _check_presentation_modality(self, hed_group, event_tag, all_tags):
        """ Check that a group with a single event sensory event tag

        Parameters:
            hed_group (HedGroup): The HED group to check (should have a single event tag).
            event_tag (str): The single event tag associated with the group.
            all_tags (list): A list of all the HedTag objects in the group.

        Returns:
            list: list of issues

        """
        if event_tag != 'Sensory-event':
            return []
        if any('sensory-presentation' in tag.tag_terms for tag in all_tags):
            return []
        return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.MISSING_SENSORY_PRESENTATION,
                                                      string=str(hed_group), line=self.original_line_number)

    def _check_action_tags(self, hed_group, event_tag, all_tags):
        """ Check that a group with a single event tag has at least one task role tag unless it is a non-task event.

        Parameters:
            hed_group (HedGroup): The HED group to check (should have a single event tag).
            event_tag (str): The single event tag associated with the group.
            all_tags (list): A list of all the HedTag objects in the group.

        Returns:
            list: list of issues

        """
        if event_tag != 'Agent-action':
            return []
        if any('action' in tag.tag_terms for tag in all_tags):
            return []
        return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.MISSING_ACTION_TAG,
                                                      string=str(hed_group), line=self.original_line_number)

class EventsChecker:
    """ Class to check for event tag quality errors in an event file."""

 # Excluding tags for condition-variables and task -- these can be done separately if we want to.
    REMOVE_TYPES = ['Condition-variable', 'Task']


    def __init__(self, hed_schema, input_data, name=None):
        """ Constructor for the EventChecker class.

        Parameters:
            hed_schema (HedSchema): The HedSchema object to check.
            input_data (TabularInput): The input data object to check.
            name (str): The name to display for this file for error purposes.

        """
        self._schema = hed_schema
        self.input_data = input_data
        self.name = name
        self._initialize()

    def _initialize(self):

        event_manager = EventManager(self.input_data, self._schema)
        tag_man = HedTagManager(event_manager, remove_types=self.REMOVE_TYPES)
        self.hed_objs = tag_man.get_hed_objs(include_context=False, replace_defs=True)
        self.onsets = event_manager.onsets
        self.original_index = event_manager.original_index

    def validate_event_tags(self):
        """ Verify that the events in the HED strings validly represent events.

        Returns:
            list:  each element is a dictionary with 'code' and 'message' keys,
        """
        issues = []
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.FILE_NAME, self.name)
        for index, hed_obj in enumerate(self.hed_objs):
            if not hed_obj or hed_obj is None:
                continue
            error_handler.push_error_context(ErrorContext.LINE, int(self.original_index.iloc[index]))
            event_check = EventChecker(hed_obj, index, int(self.original_index.iloc[index]), error_handler)
            issues += event_check.issues
            error_handler.pop_error_context()
        issues = sort_issues(issues)
        return issues

    def insert_issue_details(self, issues):
        """ Inserts issue details as part of the 'message' key for a list of issues.

        Parameters:
            issues (list): List of issues to get details for.

        """
        side_data = self.input_data._mapper.sidecar_column_data
        for issue in issues:
            line = issue.get('ec_line')
            if line is None:
                continue
            data_info = self.input_data._dataframe.iloc[line]
            details = [f"Sources: line:{line} onset:{self.onsets[line]}"] + \
                 EventsChecker.get_issue_details(data_info, side_data)
            issue['details'] = details

    @staticmethod
    def get_issue_details(data_info, side_data):
        """ Get the source details for the issue.

        Parameters:
            data_info (pd.Series): The row information from the original tsv.
            side_data (pd.Series): The sidecar data.

        Returns:
            list: The HED associated with the relevant columns.
        """
        details = []
        for col, value in data_info.items():
            if value == 'n/a':
                continue
            col_line = ''
            # Check to see if it has HED in the sidecar for this column
            if side_data and col in side_data and side_data[col] and side_data[col].hed_dict:
                col_line = f"  => sidecar_source:{EventsChecker.get_hed_source(side_data[col].hed_dict, value)}"
            if not col_line and col != 'HED':
                continue
            details.append(f"\t[Column_name:{col} Column_value:{data_info[col]}]" + col_line)
        return details

    @staticmethod
    def get_hed_source(hed_dict, value):
        """ Get the source of the HED string.

        Parameters:
            hed_dict (HedTag): The HedTag object to get the source for.

        Returns:
            str: The source of the HED string.
        """
        if isinstance(hed_dict, dict):
            return hed_dict.get(value)
        else:
            return hed_dict

    def get_onset_lines(self, line):
        """ Get the lines in the input data with the same line numbers as the data_frame. """
        none_positions = [i for i in range(line + 1, len(self.hed_objs)) if self.hed_objs[i] is None]
        return [line] + none_positions

    @staticmethod
    def get_error_lines(issues):
        """ Get the lines grouped by code.

        Parameters:
            issues (list): A list of issues to check.

        Returns:
           dict: A dict with keys that are error codes and values that are lists of line numbers.
        """
        error_lines = {}
        for issue in issues:
            code = issue.get('code')
            if code not in error_lines:
                error_lines[code] = []
            line = issue.get('ec_line')
            if line:
                error_lines[code].append(line)
        for key, value in error_lines.items():
            error_lines[key] = set(value)
        return error_lines
