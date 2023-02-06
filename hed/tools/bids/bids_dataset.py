""" The contents of a BIDS dataset. """

import os
import json
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_io import load_schema_version
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.validator.hed_validator import HedValidator


LIBRARY_URL_BASE = "https://raw.githubusercontent.com/hed-standard/hed-schemas/main/library_schemas/"


class BidsDataset:
    """ A BIDS dataset representation primarily focused on HED evaluation.

    Attributes:
        root_path (str):  Real root path of the BIDS dataset.  
        schema (HedSchema or HedSchemaGroup):  The schema used for evaluation.  
        tabular_files (dict):  A dictionary of BidsTabularDictionary objects containing a given type.  

    """

    def __init__(self, root_path, schema=None, tabular_types=None,
                 exclude_dirs=['sourcedata', 'derivatives', 'code', 'stimuli']):
        """ Constructor for a BIDS dataset.

        Parameters:
            root_path (str):  Root path of the BIDS dataset.
            schema (HedSchema or HedSchemaGroup):  A schema that overrides the one specified in dataset.
            tabular_types (list or None):  List of strings specifying types of tabular types to include.
                If None or empty, then ['events'] is assumed.
            exclude_dirs=['sourcedata', 'derivatives', 'code']):

        """
        self.root_path = os.path.realpath(root_path)
        with open(os.path.join(self.root_path, "dataset_description.json"), "r") as fp:
            self.dataset_description = json.load(fp)
        if schema:
            self.schema = schema
        else:
            self.schema = load_schema_version(self.dataset_description.get("HEDVersion", None))

        self.exclude_dirs = exclude_dirs
        self.tabular_files = {"participants": BidsFileGroup(root_path, suffix="participants", obj_type="tabular")}
        if not tabular_types:
            self.tabular_files["events"] = BidsFileGroup(root_path, suffix="events", obj_type="tabular",
                                                         exclude_dirs=exclude_dirs)
        else:
            for suffix in tabular_types:
                self.tabular_files[suffix] = BidsFileGroup(root_path, suffix=suffix, obj_type="tabular",
                                                           exclude_dirs=exclude_dirs)

    def get_tabular_group(self, obj_type="events"):
        """ Return the specified tabular file group.

        Parameters:
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

        Parameters:
            types (list):  A list of strings indicating the file group types to be validated.
            check_for_warnings (bool):  If True, check for warnings.

        Returns:
            list:  List of issues encountered during validation. Each issue is a dictionary.

        """
        validator = HedValidator(hed_schema=self.schema)
        error_handler = ErrorHandler()
        if not types:
            types = list(self.tabular_files.keys())
        issues = []
        for tab_type in types:
            files = self.tabular_files[tab_type]
            issues += files.validate_sidecars(hed_ops=[validator],
                                              check_for_warnings=check_for_warnings, error_handler=error_handler)
            issues += files.validate_datafiles(hed_ops=[validator],
                                               check_for_warnings=check_for_warnings,
                                               error_handler=error_handler)
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
