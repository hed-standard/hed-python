import os
from hed.tools.bids.bids_file import BidsFile
from hed.models import Sidecar, TabularInput


class BidsTabularFile(BidsFile):
    """ A BIDS tabular file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS tabular file.

        Args:
            file_path (str):  Path of the tabular file.
        """
        super().__init__(file_path)

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of this tabular file.

        Args:
            content_info (None):   This always uses the internal file_path to create the contents.
            overwrite:  If False, do not overwrite existing contents if any.

        """
        if self.contents and not overwrite:
            return

        if self.sidecar:
            self.contents = TabularInput(file=self.file_path, sidecar=self.sidecar.contents,
                                         name=os.path.realpath(self.file_path))
            if self.sidecar.has_hed:
                self.has_hed = True
        else:
            self.contents = TabularInput(file=self.file_path, name=os.path.realpath(self.file_path))
        columns = self.contents.columns
        if 'HED' in columns or 'HED_assembled' in columns:
            self.has_hed = True


if __name__ == '__main__':
    from hed import HedSchemaGroup, HedValidator, load_schema, load_schema_version, Sidecar, TabularInput

    # check_for_warnings = False
    # base_version = '8.1.0'
    # score_url = f"https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/" + \
    #             f"library_schemas/score/prerelease/HED_score_1.0.0.xml"
    #
    # schema_base = load_schema_version(xml_version="8.1.0")
    # schema_score = load_schema(score_url, schema_prefix="sc")
    # schema = HedSchemaGroup([schema_base, schema_score])
    # validator = HedValidator(hed_schema=schema)
    #
    # base_path = '../../../xeeg_hed_score/sub-ieegModulator/ses-ieeg01/ieeg'
    # tab_path = os.path.join(base_path, 'sub-ieegModulator_ses-ieeg01_task-photicstim_run-01_events.tsv')
    # side_path = os.path.join(base_path, 'sub-ieegModulator_ses-ieeg01_task-photicstim_run-01_events.json')
    #
    # bids_side = Sidecar(side_path)
    # bids_tab = TabularInput(tab_path, sidecar=bids_side)
    # issues = bids_tab.validate_file(hed_ops=validator, check_for_warnings=False)
    # print(f"Issues  {issues}")
    #
    # bids_tab1 = TabularInput(tab_path)
    # issues1 = bids_tab1.validate_file(hed_ops=validator, check_for_warnings=False)
    # print(f"Issues 1 {issues1}")

    y = '../../../tests/data/curation/sub-001_task-AuditoryVisualShift_run-01_events.tsv'
    print(os.path.realpath(os.path.abspath(y)))
    x = TabularInput(file=y, name=os.path.realpath(y))
