import os
import json
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_io import load_schema, load_schema_version
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.util.data_util import get_new_dataframe
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile
from hed.validator import HedValidator


LIBRARY_URL_BASE = "https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/library_schemas/"


class BidsDataset:
    """Represents the metadata for a BIDS dataset primarily focused on HED evaluation."""

    def __init__(self, root_path, schema_group=None):
        """ Constructor for a BIDS dataset.

        Args:
            root_path (str):  Root path of the BIDS dataset.
            schema_group (HedSchemaGroup):  An optional HedSchemaGroup that overrides the one specified in dataset.

        """
        self.root_path = os.path.realpath(root_path)
        with open(os.path.join(self.root_path, "dataset_description.json"), "r") as fp:
            self.dataset_description = json.load(fp)
        self.participants = get_new_dataframe(os.path.join(self.root_path, "participants.tsv"))
        if schema_group:
            self.schemas = schema_group
        else:
            self.schemas = HedSchemaGroup(self._schema_from_description())
        self.tabular_files = {"events": BidsFileGroup(root_path, suffix="_events", type="tabular")}

    def validate(self, check_for_warnings=True):
        validator = HedValidator(hed_schema=self.schemas)
        event_files = self.tabular_files["events"]
        issues1 = event_files.validate_sidecars(hed_ops=[validator], check_for_warnings=check_for_warnings)
        issues2 = event_files.validate_datafiles(hed_ops=[validator], check_for_warnings=check_for_warnings)
        return issues1 + issues2

    def _schema_from_description(self):
        hed = self.dataset_description.get("HEDVersion", None)
        if isinstance(hed, str):
            return [load_schema_version(xml_version=hed)]
        elif not isinstance(hed, dict):
            return []

        hed_list = []
        if 'base' in hed:
            hed_list.append(load_schema_version(xml_version=hed['base']))
        if 'libraries' in hed:
            for key, library in hed['libraries'].items():
                library_pieces = library.split('_')
                url = LIBRARY_URL_BASE + library_pieces[0] + '/hedxml/HED_' + library + '.xml'
                hed_list.append(load_schema(url, library_prefix=key))
        return hed_list

    def get_summary(self):
        summary = {"dataset": self.dataset_description['Name'],
                   "hed_schema_versions": self.get_schema_versions()}
        return summary

    def get_schema_versions(self):
        version_list = []
        for prefix, schema in self.schemas._schemas.items():
            name = schema.version
            if schema.library:
                name = schema.library + '_' + name
            name = prefix + name
            version_list.append(name)
        return version_list


if __name__ == '__main__':
    # path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                     '../../../tests/data/bids/eeg_ds003654s_hed_library')
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        '../../../tests/data/bids/eeg_ds003654s_hed_inheritance')

    bids = BidsDataset(path)
    issue_list = bids.validate(check_for_warnings=False)
    if issue_list:
        issue_str = get_printable_issue_string(issue_list, "HED validation errors:")
    else:
        issue_str = "No issues"
    print(issue_str)
    # summary1 = bids.get_summary()
    # print(json.dumps(summary1, indent=4))
