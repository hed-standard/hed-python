from hed.errors.error_types import TagQualityErrors
from hed.errors import ErrorHandler, ErrorContext, get_printable_issue_string
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
                                                           string=str(group), line=self.line_number)

        if len(event_tags) == 1:
            return self._check_event_group(group, event_tags[0], all_tags)

        # At this point, we know we have multiple event tags in the group.
        if any(tag.short_base_tag in event_tags for tag in group.tags()):
            return ErrorHandler.format_error_with_context(self.error_handler, TagQualityErrors.IMPROPER_EVENT_GROUPS,
                                                          string=str(group), line=self.line_number,
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
                                                      line=self.line_number)

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
                                                      string=str(hed_group), line=self.line_number)

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
                                                      string=str(hed_group), line=self.line_number)

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
        self.group_error_lines = []
        self.missing_error_lines = []
        self._initialize()

    def _initialize(self):

        event_manager = EventManager(self.input_data, self._schema)
        tag_man = HedTagManager(event_manager, remove_types=self.REMOVE_TYPES)
        self.hed_objs = tag_man.get_hed_objs(include_context=False, replace_defs=True)

    def validate_event_tags(self):
        """ Verify that the events in the HED strings validly represent events.

        Returns:
            list:  each element is a dictionary with 'code' and 'message' keys,
        """
        issues = []
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.FILE_NAME, self.name)
        for index, hed_obj in enumerate(self.hed_objs):
            if not hed_obj:
                continue
            error_handler.push_error_context(ErrorContext.LINE, index)
            event_check = EventChecker(hed_obj, index, error_handler)
            issues += event_check.issues
            error_handler.pop_error_context()
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
            lines = self.get_onset_lines(line)
            data_info = self.input_data._dataframe.iloc[lines]
            details = ["Sources:"]
            for index, row in data_info.iterrows():
               details += EventsChecker.get_issue_details(row, index, side_data)
            issue['details'] = details

    @staticmethod
    def get_issue_details(data_info, line, side_data):
        """ Get the source details for the issue.

        Parameters:
            data_info (pd.Series): The row information from the original tsv.
            line (list): A list of lines from the original tsv.
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
            col_line = f"\t[line:{line} column_name:{col} column_value:{data_info[col]}]" + col_line
            details.append(col_line)
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
        return error_lines


if __name__ == '__main__':
    import os
    from hed.schema.hed_schema_io import load_schema_version
    schema = load_schema_version('8.4.0')

    # Wakeman Henson example
    root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds003645s_hed'
    sidecar_path = os.path.join(root_dir, 'task-FacePerception_events.json')
    tsv_path = os.path.join(root_dir, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
    data_name = 'eeg_ds003645s_hed'

    # input = TabularInput(tsv_path, sidecar_path, data_name)
    # assembled = input.dataframe_a
    # other = input._dataframe
    # print("toHere")
    # # Attention shift example
    # root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds002893s_hed_attention_shift'
    # sidecar_path = os.path.join(root_dir, 'task-AuditoryVisualShift_events.json')
    # tsv_path = os.path.join(root_dir, 'sub-002/eeg/sub-002_task-AuditoryVisualShift_run-01_events.tsv')
    # data_name = 'eeg_ds002893s_hed_attention_shift'

    # # Sternberg example
    # root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds004117s_hed_sternberg'
    # sidecar_path = os.path.join(root_dir, 'task-WorkingMemory_events.json')
    # tsv_path = os.path.join(root_dir, 'sub-001/ses-01/eeg/sub-001_ses-01_task-WorkingMemory_run-1_events.tsv')
    # data_name = 'eeg_ds004117s_hed_sternberg'

    # Create the event summary
    input_data = TabularInput(tsv_path, sidecar_path, data_name)
    checker = EventsChecker(schema, input_data, data_name)

    # Check the validity of the event tags
    these_issues = checker.validate_event_tags()
    issue_lines = checker.get_error_lines(these_issues)
    for code, lines in issue_lines.items():
        print(f"Error code {code} found on {len(lines)} lines: {lines}")
    issues_filtered = ErrorHandler.filter_issues_by_count(these_issues, 2)
    checker.insert_issue_details(issues_filtered)
    print(issues_filtered)
    x = get_printable_issue_string(issues_filtered, '', add_link=True, show_details=True)
    print(x)
    # if issues_filtered:
    #     print(f"Errors found:\n{get_printable_issue_string(issues_filtered, '', add_link=True, show_details=True)}")
    # else:
    #     print(f"No errors found in {data_name}.")
    #
    # if issues_filtered:
    #     checker.insert_issue_details(issues_filtered)
    #     x = get_printable_issue_string(issues_filtered, '', add_link=True, show_details=True)
    #     print(f"Errors found:\n{get_printable_issue_string(issues_filtered, 'With details:')}")

    # df_a = checker.input_data.dataframe_a
    # df = checker.input_data._dataframe
    # for issue in issues_filtered:
    #     line = issue.get('ec_line')
    #     if not line:
    #         continue
    #     all_lines = checker.get_lines(line)

        # display = ''
        # for x in all_lines:
        #     display += f"Line {x}:"
        #     row = df_a.iloc[x]
        #     for col, value in row.items():
        #         if not value:
        #             continue
        #         display += f"\n  {col}={df.at[x, col]}: {value}"
        #
        # print(display)

    # details = f"> Details:\n"
    # for col, value in row_info.items():
    #     if not value:
    #         continue
    #     details += f">[Column:{col}, value:{data_info[col]}]\n" + \
    #                f">    HED={value}\n"
    #     if side_data and col in side_data and side_data[col]:
    #         hed_dict = side_data[col].hed_dict
    #         if hed_dict:
    #             details += f">    sidecar source={self.get_hed_source(hed_dict, value)}\n"
    # return details