import os
import json
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema_io import load_schema, load_schema_version
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.data_util import get_new_dataframe
from hed.tools.bids.bids_event_files import BidsEventFiles
from hed.validator import HedValidator

LIBRARY_URL_BASE = "https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/hedxml/HED_"


class BidsDataset:
    """Represents a bids_old dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        with open(os.path.join(self.root_path, "dataset_description.json"), "r") as fp:
            self.dataset_description = json.load(fp)
        self.participants = get_new_dataframe(os.path.join(self.root_path, "participants.tsv"))
        self.schemas = HedSchemaGroup(self._schema_from_description())
        self.event_files = BidsEventFiles(root_path)

    def validate(self, check_for_warnings=True):
        validator = HedValidator(hed_schema=self.schemas)
        issues = self.event_files.validate(validators=[validator], check_for_warnings=check_for_warnings)
        return issues

    def _schema_from_description(self):
        hed = self.dataset_description.get("HEDVersion", None)
        if isinstance(hed, str):
            return [load_schema_version(xml_version_number=hed)]
        elif not isinstance(hed, dict):
            return []

        hed_list = []
        if 'base' in hed:
            hed_list.append(load_schema_version(xml_version_number=hed['base']))
        if 'libraries' in hed:
            for key, library in hed['libraries'].items():
                url = LIBRARY_URL_BASE + library + '.xml'
                x = load_schema(url, library_prefix=key)
                x.set_library_prefix(key)  # TODO: temporary work around
                hed_list.append(x)
        return hed_list

    def get_summary(self):
        summary = {"hed_schema_versions": self.get_schema_versions()}
        return summary

    def get_schema_versions(self):
        version_list = []
        x = self.schemas
        for prefix, schema in self.schemas._schemas.items():
            name = schema.version
            if schema.library:
                name = schema.library + '_' + name
            name = prefix + name
            version_list.append(name)
        return version_list


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '../../../tests/data/bids/eeg_ds003654s_hed_library')
    bids = BidsDataset(path)
    # issue_list = bids.validate()
    # if issue_list:
    #     issue_str = get_printable_issue_string(issue_list, "HED_library")
    # else:
    #     issue_str = "No issues"
    # print(issue_str)
    summary1 = bids.get_summary()
    print(json.dumps(summary1, indent=4))
