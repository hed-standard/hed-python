""" The contents of a BIDS dataset. """

import os
import logging
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.tools.bids import bids_util
from hed.tools.util import io_util


class BidsDataset:
    """ A BIDS dataset representation primarily focused on HED evaluation.

    Attributes:
        root_path (str):  Real root path of the BIDS dataset.
        schema (HedSchema or HedSchemaGroup):  The schema used for evaluation.
        file_groups (dict):  A dictionary of BidsFileGroup objects with a given file suffix.

    """

    def __init__(self, root_path, schema=None, suffixes=['events', 'participants'],
                 exclude_dirs=['sourcedata', 'derivatives', 'code', 'stimuli']):
        """ Constructor for a BIDS dataset.

        Parameters:
            root_path (str):  Root path of the BIDS dataset.
            schema (HedSchema or HedSchemaGroup):  A schema that overrides the one specified in dataset.
            suffixes (list or None): File name suffixes of items to include.
                If None or empty, then ['_events', 'participants'] is assumed.
            exclude_dirs=['sourcedata', 'derivatives', 'code', 'phenotype']:

        """
        logger = logging.getLogger('hed.bids_dataset')
        logger.debug(f"Initializing BidsDataset for path: {root_path}")
        
        self.root_path = os.path.realpath(root_path)
        logger.debug(f"Real root path resolved to: {self.root_path}")
        
        if schema:
            self.schema = schema
            logger.debug(f"Using provided schema: {schema.get_schema_versions() if hasattr(schema, 'get_schema_versions') else 'custom'}")
        else:
            logger.debug("Loading schema from dataset description...")
            self.schema = bids_util.get_schema_from_description(self.root_path)
            if self.schema:
                logger.info(f"Loaded schema from dataset: {self.schema.get_schema_versions()}")
            else:
                logger.warning("No valid schema found in dataset description")

        self.exclude_dirs = exclude_dirs
        self.suffixes = suffixes
        logger.debug(f"Using suffixes: {suffixes}, excluding directories: {exclude_dirs}")
        
        logger.info("Setting up file groups...")
        self.file_groups = self._set_file_groups()
        self.bad_files = []
        
        logger.info(f"BidsDataset initialized with {len(self.file_groups)} file groups: {list(self.file_groups.keys())}")

    def get_file_group(self, suffix):
        """ Return the file group of files with the specified suffix.

        Parameters:
            suffix (str):  Suffix of the BidsFileGroup to be returned.

        Returns:
            Union[BidsFileGroup, None]:  The requested tabular group.

        """
        return self.file_groups.get(suffix, None)

    def validate(self, check_for_warnings=False, schema=None):
        """ Validate the dataset.

        Parameters:
            check_for_warnings (bool):  If True, check for warnings.
            schema (HedSchema or HedSchemaGroup or None):  The schema used for validation.

        Returns:
            list:  List of issues encountered during validation. Each issue is a dictionary.

        """
        logger = logging.getLogger('hed.bids_dataset')
        logger.info(f"Starting validation of {len(self.file_groups)} file groups")
        logger.debug(f"Check for warnings: {check_for_warnings}")
        
        issues = []
        if schema:
            this_schema = schema
            logger.debug("Using provided schema for validation")
        elif self.schema:
            this_schema = self.schema
            logger.debug(f"Using dataset schema for validation: {this_schema.get_schema_versions()}")
        else:
            logger.error("No valid schema available for validation")
            return [{"code": "SCHEMA_LOAD_FAILED",
                     "message": "BIDS dataset_description.json has invalid HEDVersion and passed schema was invalid}"}]
        
        for suffix, group in self.file_groups.items():
            if group.has_hed:
                logger.info(f"Validating file group: {suffix} ({len(group.datafile_dict)} files)")
                group_issues = group.validate(this_schema, check_for_warnings=check_for_warnings)
                logger.info(f"File group {suffix} validation completed: {len(group_issues)} issues found")
                issues += group_issues
            else:
                logger.debug(f"Skipping file group {suffix} - no HED content")
        
        logger.info(f"Dataset validation completed: {len(issues)} total issues found")
        return issues

    def get_summary(self):
        """ Return an abbreviated summary of the dataset. """
        summary = {"dataset": self.root_path,
                   "hed_schema_versions": self.schema.get_schema_versions(),
                   "file_group_types": f"{str(list(self.file_groups.keys()))}"}
        return summary

    def _set_file_groups(self):
        logger = logging.getLogger('hed.bids_dataset')
        logger.debug(f"Searching for files with extensions ['.tsv', '.json'] and suffixes {self.suffixes}")
        
        file_paths = io_util.get_file_list(self.root_path, extensions=['.tsv', '.json'],
                                           exclude_dirs=self.exclude_dirs, name_suffix=self.suffixes)
        logger.debug(f"Found {len(file_paths)} files matching criteria")
        
        file_dict = bids_util.group_by_suffix(file_paths)
        logger.debug(f"Files grouped by suffix: {[(suffix, len(files)) for suffix, files in file_dict.items()]}")

        file_groups = {}
        for suffix, files in file_dict.items():
            logger.debug(f"Creating file group for suffix '{suffix}' with {len(files)} files")
            file_group = BidsFileGroup.create_file_group(self.root_path, files, suffix)
            if file_group:
                file_groups[suffix] = file_group
                logger.debug(f"Successfully created file group for '{suffix}'")
            else:
                logger.warning(f"Failed to create file group for suffix '{suffix}'")

        self.suffixes = list(file_groups.keys())
        logger.info(f"Created {len(file_groups)} file groups: {list(file_groups.keys())}")
        return file_groups
