import os
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file import BidsFile


class BidsSidecarFile(BidsFile):
    """ A BIDS sidecar file. """

    def __init__(self, file_path):
        super().__init__(file_path)

    def is_sidecar_for(self, obj):
        """ Return true if this is a sidecar for obj.

         Args:
             obj (BidsFile):  A BidsFile object to check.

         Returns:
             bool:   True if this is a BIDS parent of obj and False otherwise.

         Notes:
             - A sidecar is a sidecar for itself.

         """

        if obj.file_path == self.file_path:
            return True
        elif obj.suffix != self.suffix:
            return False
        elif os.path.dirname(self.file_path) != os.path.commonpath([obj.file_path, self.file_path]):
            return False

        for key, item in self.entity_dict.items():
            if key not in obj.entity_dict or obj.entity_dict[key] != item:
                return False
        return True

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of the sidecar.

        Args:
            content_info (list, str, or None): If None, create a Sidecar from the object's file-path.
            overwrite (bool): If True, overwrite contents if already set.

        Notes:
            - The handling of content_info is as follows:
                - None: This object's file_path is used.
                - str:  The string is interpreted as a path of the JSON.
                - list: The list is of paths.

         """
        if not overwrite and self.contents:
            return
        if not content_info:
            content_info = self.file_path
        self.contents = Sidecar(files=content_info,
                                name=os.path.realpath(os.path.basename(self.file_path)))
        self.has_hed = self.is_hed(self.contents.loaded_dict)

    @staticmethod
    def is_hed(json_dict):
        """ Return True if the json has HED.

        Args:
            json_dict (dict): A dictionary representing a JSON file or merged file.

        Returns:
            bool:  True if the dictionary has HED or HED_assembled as a first or second-level key.

        """

        if not json_dict or not isinstance(json_dict, dict):
            return False
        json_keys = json_dict.keys()
        if 'HED' in json_keys or 'HED_assembled' in json_keys:
            return True
        for key, value in json_dict.items():
            if not isinstance(value, dict):
                continue
            val_keys = value.keys()
            if 'HED' in val_keys or 'HED_assembled' in val_keys:
                return True

        return False


if __name__ == '__main__':
    from hed import load_schema, HedValidator, load_schema_version, HedSchemaGroup
    score_url = f"https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/library_schemas" \
                f"/score/prerelease/HED_score_1.0.0.xml"
    path = f"../../../sub-eegArtifactTUH_ses-eeg01_task-rest_run-001_events.json"
    bids_json = BidsSidecarFile(path)
    bids_json.set_contents()
    schema_base = load_schema_version(xml_version="8.1.0")
    schema_score = load_schema(score_url, schema_prefix="sc")
    schemas = HedSchemaGroup([schema_base, schema_score])
    validator = HedValidator(hed_schema=schemas)
    issues = bids_json.contents.validate_entries(hed_ops=validator, check_for_warnings=False)
    print(f"issues:{str(issues)}")
