import os
from hed.models.timeseries_input import TimeseriesInput
from hed.tools.bids.bids_file import BidsFile


class BidsTimeseriesFile(BidsFile):
    """ A BIDS continuous file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS events file. """
        super().__init__(file_path)

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of this timeseries file.

        Args:
            content_info (None):   This always uses the internal file_path to create the contents.
            overwrite:  If False, do not overwrite existing contents if any.

        """
        # if self.contents and not overwrite:
        #     return
        #
        # if self.sidecar:
        #     self.contents = TimeseriesInput(file=self.file_path, sidecar=self.sidecar.contents,
        #                                     name=os.path.realpath(self.file_path))
        #     if self.sidecar.has_hed:
        #         self.has_hed = True
        # else:
        #     self.contents = TimeseriesInput(file=self.file_path, name=os.path.realpath(self.file_path))
        # columns = self.contents._mapper._column_map.values()
        # if 'HED' in columns or 'HED_assembled' in columns:
        #     self.has_hed = True