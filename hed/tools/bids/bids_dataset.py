import os
import json
from hed.errors.error_reporter import get_printable_issue_string
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_io import load_schema, load_schema_version
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.validator import HedValidator


LIBRARY_URL_BASE = "https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/library_schemas/"


class BidsDataset:
    """ A BIDS dataset primarily focused on HED evaluation.

    Attributes:
        root_path (str):  Real root path of the BIDS dataset.
        schema (HedSchema or HedSchemaGroup):  The schema used for evaluation.
        tabular_files (dict):  A dictionary of BidsTabularDictionary objects containing a given type.

    """

    def __init__(self, root_path, schema=None, tabular_types=None):
        """ Constructor for a BIDS dataset.

        Args:
            root_path (str):  Root path of the BIDS dataset.
            schema (HedSchema or HedSchemaGroup):  A schema that overrides the one specified in dataset.
            tabular_types (list or None):  List of strings specifying types of tabular types to include.
                If None or empty, then ['events'] is assumed.

        """
        self.root_path = os.path.realpath(root_path)
        with open(os.path.join(self.root_path, "dataset_description.json"), "r") as fp:
            self.dataset_description = json.load(fp)
        if schema:
            self.schema = schema
        else:
            self.schema = load_schema_version(self.dataset_description.get("HEDVersion", None))

        self.tabular_files = {"participants": BidsFileGroup(root_path, suffix="participants", obj_type="tabular")}
        if not tabular_types:
            self.tabular_files["events"] = BidsFileGroup(root_path, suffix="events", obj_type="tabular")
        else:
            for suffix in tabular_types:
                self.tabular_files[suffix] = BidsFileGroup(root_path, suffix=suffix, obj_type="tabular")

    def get_tabular_group(self, obj_type="events"):
        """ Return the specified tabular file group.

        Args:
            obj_type (str):  Suffix of the BidsFileGroup to be returned.

        Returns:
            BidsFileGroup or None:  The requested tabular group.

        """
        if obj_type in self.tabular_files:
            return self.tabular_files[obj_type]
        else:
            return None

    def validate(self, types=None, check_for_warnings=True):
        """ Validate the specified file group types.

        Args:
            types (list):  A list of strings indicating the file group types to be validated.
            check_for_warnings (bool):  If True, check for warnings.

        Returns:
            list:  List of issues encountered during validation. Each issue is a dictionary.

        """
        validator = HedValidator(hed_schema=self.schema)
        if not types:
            types = list(self.tabular_files.keys())
        issues = []
        for tab_type in types:
            files = self.tabular_files[tab_type]
            issues += files.validate_sidecars(hed_ops=[validator], check_for_warnings=check_for_warnings)
            issues += files.validate_datafiles(hed_ops=[validator], check_for_warnings=check_for_warnings)
        return issues

    def get_summary(self):
        """ Return an abbreviated summary of the dataset. """
        summary = {"dataset": self.dataset_description['Name'],
                   "hed_schema_versions": self.get_schema_versions(),
                   "file_group_types": f"{str(list(self.tabular_files.keys()))}"}
        return summary

    def get_schema_versions(self):
        """ Return the schema versions used in this dataset.

        Returns:
            list:  List of schema versions used in this dataset.

        """
        if isinstance(self.schema, HedSchema):
            return [self.schema.version]
        version_list = []
        for prefix, schema in self.schema._schemas.items():
            name = schema.version
            if schema.library:
                name = schema.library + '_' + name
            name = prefix + name
            version_list.append(name)
        return version_list


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        '../../../tests/data/bids/eeg_ds003654s_hed_library')
    # path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                     '../../../tests/data/bids/eeg_ds003654s_hed_inheritance')
    # path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                     '../../../tests/data/bids/eeg_ds003654s_hed')
    #
    bids = BidsDataset(path)
    issue_list = bids.validate(check_for_warnings=False)
    if issue_list:
        issue_str = get_printable_issue_string(issue_list, "HED validation errors:")
    else:
        issue_str = "No issues"
    print(issue_str)
    warnings = False
    path = '/XXX/bids-examples/xeeg_hed_score/'
    bids = BidsDataset(path)
    # summary1 = bids.get_summary()
    # print(json.dumps(summary1, indent=4))
    print("\nNow validating with the prerelease schema.")
    base_version = '8.1.0'
    score_url = f"https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/library_schemas/" \
                f"score/prerelease/HED_score_1.0.0.xml"

    schema_base = load_schema_version(xml_version="8.1.0")
    schema_score = load_schema(score_url, schema_prefix="sc")
    bids.schema = HedSchemaGroup([schema_base, schema_score])

    issue_list2 = bids.validate(check_for_warnings=warnings)
    if issue_list2:
        issue_str2 = get_printable_issue_string(issue_list2, "HED validation errors: ", skip_filename=False)
    else:
        issue_str2 = "No HED validation errors"
    print(issue_str2)
