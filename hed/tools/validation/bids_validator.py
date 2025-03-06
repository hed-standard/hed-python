import os
import io
import json
from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.schema.hed_schema_io import load_schema_version
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.errors import HedFileError, HedExceptions, ErrorHandler
from hed.tools.validation.bids_file import BidsFile, JsonFile, TabularFile, get_bids_file
from hed.tools.util import io_util
from hed import load_schema_version, get_printable_issue_string


class BidsValidator:
    """ A BIDS dataset validator class.

    Attributes:
        root_path (str):  Real root path of the BIDS dataset.
        schema (HedSchema or HedSchemaGroup):  The schema used for evaluation.


    """
    def __init__(self, root_path, schema=None, suffix_types=['events', 'participants'],
                 exclude_dirs=['sourcedata', 'derivatives', 'code', 'stimuli'],
                 check_for_warnings=False, verbose=False):
        """ Constructor for a BIDS dataset.

        Parameters:
            root_path (str):  Root path of the BIDS dataset.
            schema (HedSchema or HedSchemaGroup):  A schema that overrides the one specified in dataset.
            suffix_types (list or None):  List of strings specifying the suffixes (no under_bar) of files to include.
                                         The default is
            exclude_dirs (list or None): The default is ['sourcedata', 'derivatives', 'code', 'phenotype']
            check_for_warnings (bool): If true, also check for warnings.
            verbose (bool): If true give progress output.

        """
        self.root_path = os.path.realpath(root_path)
        self.exclude_dirs = exclude_dirs
        self.suffix_types = suffix_types
        self.schema = self._get_schema(schema)
        self.check_for_warnings = check_for_warnings
        self.verbose = verbose
        self.error_handler = ErrorHandler(check_for_warnings=self.check_for_warnings)
        self.issues = []

    def process_dataset(self):
        self.process_sidecars()

    def process_sidecars(self):

        if self.suffix_types:
            name_suffix = self.suffix_types
        else:
            name_suffix = None
        json_paths = io_util.get_file_list(self.root_path, name_suffix=name_suffix, extensions=['.json'],
                                           exclude_dirs=self.exclude_dirs)
        if self.verbose:
            print(f"Validating {len(json_paths)} JSON files:")

        for json_path in json_paths:
            # Read the sidecar metadata and contents as a string.
            json_file = JsonFile(json_path)
            if not json_file.has_hed:
                continue

            # Validate the sidecar
            sidecar = Sidecar(files=io.StringIO(json_file.contents), name=json_file.basename)
            issues = sidecar.validate(self.schema, name=sidecar.name, error_handler=self.error_handler)
            if self.verbose:
                print(f"\tValidating {json_file.basename}: found {len(issues)} issues")
            self.issues += issues

    def process_tabular(self):

        if self.suffix_types:
            name_suffix = self.suffix_types
        else:
            name_suffix = None
        tabular_paths = io_util.get_file_list(self.root_path, name_suffix=name_suffix, extensions=['.tsv'],
                                              exclude_dirs=self.exclude_dirs)
        if self.verbose:
            print(f"Validating {len(tabular_paths)} tsv files:")

        for tabular_path in tabular_paths:
            tabular_file = TabularFile(tabular_path)
            sidecar_dict = self.get_merged_sidecar(tabular_file)
            if sidecar_dict:
                sidecar_name = os.path.splitext(os.path.basename(tabular_path))[0] + '.json'
                sidecar = Sidecar(files=io.StringIO(json.dumps(sidecar_dict)), name=sidecar_name)
            else:
                sidecar = None
            print(tabular_file.basename)
            tabular = TabularInput(file=tabular_file.file_path, sidecar=sidecar, name=tabular_file.basename)
            issues = tabular.validate(self.schema, error_handler=self.error_handler)
            if self.verbose:
                print(f"\tValidating {tabular_file.basename}: found {len(issues)} issues")
            self.issues += issues

    def _get_schema(self, schema):
        if schema and isinstance(schema, (HedSchema, HedSchemaGroup)):
            return schema
        elif schema:
            raise HedFileError(HedExceptions.SCHEMA_INVALID,
                               f"The schema passed was not a valid HedSchema or HedSchemaGroup", "")

        # Try to read the schema
        with open(os.path.join(self.root_path, "dataset_description.json"), "r") as fp:
            dataset_description = json.load(fp)
        if not dataset_description:
            raise HedFileError(HedExceptions.SCHEMA_LOAD_FAILED,
                               f"A schema could not be found for dataset {self.root_path}", "")
        return load_schema_version(dataset_description.get("HEDVersion", None))

    def get_merged_sidecar(self, tsv_file):
        sidecar_files = [file for file in self.walk_back(tsv_file, inherit=True)]
        merged_sidecar = {}
        while sidecar_files:
            this_sidecar = sidecar_files.pop()
            merged_sidecar.update(this_sidecar.get_contents)
        return merged_sidecar

    def walk_back(self, tsv_file, inherit=True):
        source_dir = os.path.dirname(tsv_file.file_path)
        while source_dir:
            candidates = self.get_candidates(source_dir, tsv_file)

            if len(candidates) == 1:
                yield candidates[0]

            exact_match = self.find_exact_match(candidates, tsv_file.entities)
            if exact_match:
                yield exact_match
            elif len(candidates) > 1:
                paths = sorted(file.file_path for file in candidates)
                raise Exception({
                    "code": "MULTIPLE_INHERITABLE_FILES",
                    "location": paths[0],
                    "affects": tsv_file.file_path,
                    "issueMessage": f"Candidate files: {paths}",
                })

            if not inherit:
                break

            if source_dir == os.path.dirname(source_dir):
                source_dir = None
            else:
                source_dir = os.path.dirname(source_dir)

    @staticmethod
    def get_candidates(source_dir, tsv_file):
        candidates = []
        for file in os.listdir(source_dir):
            this_path = os.path.realpath(os.path.join(source_dir, file))
            if not os.path.isfile(this_path):
                continue
            bids_file = get_bids_file(this_path)
            if not bids_file:
                continue
            if BidsValidator.matches_criteria(bids_file, tsv_file):
                candidates.append(bids_file)
        return candidates

    @staticmethod
    def matches_criteria(bids_file, tsv_file):
        extension_is_valid = bids_file.extension.lower() == ".json"
        suffix_is_valid = (bids_file.suffix == tsv_file.suffix) or not tsv_file.suffix
        entities_match = all(
            bids_file.entities.get(entity) == tsv_file.entities.get(entity) for entity in tsv_file.entities.keys())
        return extension_is_valid and suffix_is_valid and entities_match

    @staticmethod
    def find_exact_match(candidates, source_entities):
        for bids_file in candidates:
            if all(bids_file.entities.get(entity) == source_entities.get(entity) for entity in source_entities.keys()):
                return bids_file
        return None


if __name__ == '__main__':
    dataset_dir = os.path.realpath('d:/eeg_ds003645s_hed_demo')
    validator = BidsValidator(dataset_dir, suffix_types=None, check_for_warnings=False, verbose=True)
    validator.process_sidecars()
    issue_list = validator.issues
    if issue_list:
        issue_str = get_printable_issue_string(issue_list, "HED validation errors: ", skip_filename=False)
    else:
        issue_str = "No HED validation errors in JSON files"
    print(issue_str)

    validator.process_tabular()
    issue_list = validator.issues
    if issue_list:
        issue_str = get_printable_issue_string(issue_list, "HED validation errors: ", skip_filename=False)
    else:
        issue_str = "No HED validation errors in tsv files"
    print(issue_str)
    # files = io_util.get_file_list(dataset_dir, name_suffix=None, extensions=['.json'], exclude_dirs=None)
