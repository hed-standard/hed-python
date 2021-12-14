import os
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_file import load_schema
from hed.tools.bids_file import BidsJsonFile, BidsEventFile
from hed.models.events_input import EventsInput
from hed.tools.io_utils import get_dir_dictionary, get_file_list, get_path_components
from hed.validator.hed_validator import HedValidator


class BidsFiles:
    """Represents the event files and their my_sidecars in a BIDS dataset."""

    def __init__(self, root_path):
        self.root_path = root_path
        self.suffix = 'events'
        self.dataset_description = ''
        self.json_files = self.set_json_files()
        self.event_files = self.set_event_files()

        self.dir_dict = get_dir_dictionary(self.root_path, name_suffix='events', extensions=['.json'])

        for bids_obj in self.json_files.values():
            bids_obj.set_sidecars(self._get_sidecars_from_path(bids_obj))
        for bids_obj in self.event_files.values():
            bids_obj.set_sidecars(self._get_sidecars_from_path(bids_obj))

    def set_json_files(self):
        files = get_file_list(self.root_path, name_suffix='_events', extensions=['.json'])
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BidsJsonFile(file)
        return file_dict

    def set_event_files(self):
        files = get_file_list(self.root_path, name_suffix='_events', extensions=['.tsv'])
        file_dict = {}
        for file in files:
            file_dict[os.path.abspath(file)] = BidsEventFile(file)
        return file_dict

    def _get_sidecar(self, obj, sidecar_files):
        if not sidecar_files:
            return None
        for sidecar_file in sidecar_files:
            sidecar_obj = self.json_files[sidecar_file]
            if sidecar_obj.is_sidecar_for(obj):
                return sidecar_obj.my_contents
        return None

    def _get_sidecars_from_path(self, obj):
        sidecar_list = []
        current_path = ''
        for comp in get_path_components(obj.file_path, self.root_path):
            current_path = os.path.abspath(os.path.join(current_path, comp))
            sidecars = self.dir_dict.get(current_path, None)
            sidecar = self._get_sidecar(obj, sidecars)
            if sidecar:
                sidecar_list.append(sidecar)
        return sidecar_list

    def validate(self, validators, check_for_warnings=True, keep_events=False):
        issues = []
        for json_obj in self.json_files.values():
            print(json_obj.file_path)
            extra_defs = []
            for sidecar_obj in json_obj.my_sidecars:
                print(sidecar_obj)
                def_dicts = [column_entry.def_dict for column_entry in sidecar_obj]
                extra_defs = extra_defs + def_dicts
            new_issues = json_obj.my_contents.validate_entries(validators=validators, extra_def_dicts=extra_defs,
                                                               check_for_warnings=check_for_warnings)
            issues += json_obj.my_contents.validate_entries(validators=None, extra_def_dicts=json_obj.my_sidecars,
                                                            check_for_warnings=check_for_warnings)
        if issues:
            return issues
        for event_obj in self.event_files.values():

            if not event_obj.my_contents:
                my_contents = EventsInput(file=event_obj.file_path, sidecars=event_obj.my_sidecars)
                if keep_events:
                    event_obj.my_contents = my_contents
            new_issues = my_contents.validate_file(validators=None, check_for_warnings=check_for_warnings)
            print(f"{event_obj.file_path} ")
            if new_issues:
                issues += my_contents.validate_file(validators=None, check_for_warnings=check_for_warnings)
        return issues


if __name__ == '__main__':
    path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s_inheritance'
    # path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
    bids = BidsFiles(path)

    for file_obj in bids.json_files.values():
        print(file_obj)

    for file_obj in bids.event_files.values():
        print(file_obj)

    print("Now validating.....")
    hed_schema = \
        load_schema(hed_url_path=
                    'https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
    validator = HedValidator(hed_schema=hed_schema)
    validation_issues = bids.validate(validators=[validator], check_for_warnings=False)
    issue_str = get_printable_issue_string(validation_issues, skip_filename=False)
    print(f"Issues: {issue_str}")
