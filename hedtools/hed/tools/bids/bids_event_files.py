import os
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema
from hed.tools.bids.bids_event_file import BidsEventFile
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile
from hed.models.events_input import EventsInput
from hed.tools.io_util import get_dir_dictionary, get_file_list, get_path_components
from hed.validator.hed_validator import HedValidator


class BidsEventFiles:
    """ Represents the event files and their sidecars in a BIDS dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.sidecar_dict = {}  # Dict uses os.path.abspath(file) as key
        self.event_files_dict = {}
        self.sidecar_dir_dict = {}
        self._set_sidecar_dict()  # Dict uses os.path.abspath(file) as key
        self._set_event_file_dict()
        self._set_sidecar_dir_dict()

        for bids_obj in self.event_files_dict.values():
            bids_obj.set_sidecars(self.get_sidecars_from_path(bids_obj))

    def _set_event_file_dict(self):
        """ Get a dictionary of BidsEventFile objects with underlying EventInput objects not set"""
        files = get_file_list(self.root_path, name_suffix='_events', extensions=['.tsv'])
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BidsEventFile(file)
        self.event_files_dict = file_dict

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

    def validate(self, validators, check_for_warnings=True, keep_events=False):
        issues = []
        for json_obj in self.sidecar_dict.values():
            extra_defs = []
            issues += json_obj.contents.validate_entries(validators=validators, check_for_warnings=check_for_warnings)
        if issues:
            return issues
        for event_obj in self.event_files_dict.values():
            contents = event_obj.contents
            if not contents:
                contents = EventsInput(file=event_obj.file_path, sidecars=event_obj.sidecars)
                if keep_events:
                    event_obj.my_contents = contents
            issues += contents.validate_file(validators=validators, check_for_warnings=check_for_warnings)
        return issues


if __name__ == '__main__':
    # path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s_inheritance'
    path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
    # path = 'G:\\WH_working3'
    bids = BidsEventFiles(path)

    for file_obj in bids.sidecar_dict.values():
        print(file_obj)

    for file_obj in bids.event_files_dict.values():
        print(file_obj)

    print("Now validating.....")
    hed_schema = load_schema(
            hed_url_path='https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
    validator = HedValidator(hed_schema=hed_schema)
    validation_issues = bids.validate(validators=[validator], check_for_warnings=False)
    issue_str = get_printable_issue_string(validation_issues, skip_filename=False)
    print(f"Issues: {issue_str}")
