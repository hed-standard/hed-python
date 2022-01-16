import os
import json
from hed.tools.data_util import get_new_dataframe
from hed.schema.hed_schema_file import load_schema, load_schema_version
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_event_files import BidsEventFiles

LIBRARY_URL_BASE = "https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/hedxml/HED_"


class BidsDataset:
    """Represents a bids dataset."""

    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        with open(os.path.join(self.root_path, "dataset_description.json"), "r") as fp:
            self.dataset_description = json.load(fp)
        self.participants = get_new_dataframe(os.path.join(self.root_path, "participants.tsv"))
        y = self._schema_from_description()
        self.hed_schema = HedSchemaGroup(self._schema_from_description())
        self.event_files = BidsEventFiles(root_path)

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
                x = load_schema(hed_url_path=url, library_prefix=key)
                x.set_library_prefix(key)  #TODO: temporary work around
                hed_list.append(x)
        return hed_list


if __name__ == '__main__':
    path = 'D:\\Research\\HED\\hed-examples\\datasets\\eeg_ds003654s_hed_library'
    bids = BidsDataset(path)