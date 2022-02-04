import os
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.bids.bids_event_file import BidsEventFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile
from hed.tools.summaries.col_dict import ColumnDict
from hed.models.events_input import EventsInput
from hed.util.io_util import get_dir_dictionary, get_file_list, get_path_components
from hed.validator.hed_validator import HedValidator


class BidsEventFiles:
    """ Container for the event files and sidecars in a BIDS dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.sidecar_dict = {}  # Dict uses os.path.abspath(file) as key
        self.events_dict = {}
        self.sidecar_dir_dict = {}
        self._set_sidecar_dict()  # Dict uses os.path.abspath(file) as key
        self._set_event_file_dict()
        self._set_sidecar_dir_dict()

        for bids_obj in self.events_dict.values():
            bids_obj.set_sidecars(self.get_sidecars_from_path(bids_obj))

    def _set_event_file_dict(self):
        """ Get a dictionary of BidsEventFile objects with underlying EventInput objects not set"""
        files = get_file_list(self.root_path, name_suffix='_events', extensions=['.tsv'])
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BidsEventFile(file)
        self.events_dict = file_dict

    def _set_sidecar_dict(self):
        """ Get a dictionary of BidsSidecarFile objects with underlying Sidecar objects set"""
        files = get_file_list(self.root_path, name_suffix='_events', extensions=['.json'])
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BidsSidecarFile(os.path.abspath(file), set_contents=True)
        self.sidecar_dict = file_dict

    def _set_sidecar_dir_dict(self):
        """ Set the dictionary with direct pointers to sidecars rather than paths"""
        dir_dict = get_dir_dictionary(self.root_path, name_suffix='events', extensions=['.json'])
        sidecar_dir_dict = {}
        for this_dir, dir_list in dir_dict.items():
            new_dir_list = []
            for s_file in dir_list:
                new_dir_list.append(self.sidecar_dict[os.path.abspath(s_file)])
            sidecar_dir_dict[os.path.abspath(this_dir)] = new_dir_list
        self.sidecar_dir_dict = sidecar_dir_dict

    def get_sidecars_from_path(self, obj):
        sidecar_list = []
        current_path = ''
        for comp in get_path_components(obj.file_path, self.root_path):
            current_path = os.path.abspath(os.path.join(current_path, comp))
            sidecars = self.sidecar_dir_dict.get(current_path, None)
            sidecar = BidsSidecarFile.get_sidecar(obj, sidecars)
            if sidecar:
                sidecar_list.append(sidecar)
        return sidecar_list

    def summarize(self, value_cols=None, skip_cols=None):
        col_info = ColumnDict(value_cols=None, skip_cols=None)
        for event_obj in self.events_dict.values():
            col_info.update(event_obj.file_path)
        return col_info

    def validate(self, validators, check_for_warnings=True, keep_events=False):
        issues = []
        for json_obj in self.sidecar_dict.values():
            issues += json_obj.contents.validate_entries(hed_ops=validators, check_for_warnings=check_for_warnings)
        if issues:
            return issues
        for event_obj in self.events_dict.values():
            contents = event_obj.contents
            if not contents:
                contents = EventsInput(file=event_obj.file_path, sidecars=event_obj.sidecars)
                if keep_events:
                    event_obj.my_contents = contents
            issues += contents.validate_file(hed_ops=validators, check_for_warnings=check_for_warnings)
        return issues


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '../../../tests/data/bids/eeg_ds003654s_hed')
    bids = BidsEventFiles(path)

    for file_obj in bids.sidecar_dict.values():
        print(file_obj)

    for file_obj in bids.events_dict.values():
        print(file_obj)

    hed_schema = load_schema_version(xml_version="8.0.0")
    # print("Now validating.....")
    # validator = HedValidator(hed_schema=hed_schema)
    # validation_issues = bids.validate(validators=[validator], check_for_warnings=False)
    # issue_str = get_printable_issue_string(validation_issues, skip_filename=False)
    # print(f"Issues: {issue_str}")

    col_info = bids.summarize()
    col_info.print()
