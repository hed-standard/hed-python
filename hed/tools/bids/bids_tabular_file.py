""" A BIDS tabular file including its associated sidecar. """

import os
from hed.models.tabular_input import TabularInput
from hed.tools.bids.bids_file import BidsFile


class BidsTabularFile(BidsFile):
    """ A BIDS tabular file including its associated sidecar. """

    def __init__(self, file_path):
        """ Constructor for a BIDS tabular file.

        Parameters:
            file_path (str):  Path of the tabular file.
        """
        super().__init__(file_path)
        self.sidecar = None

    def set_contents(self, content_info=None, overwrite=False):
        """ Set the contents of this tabular file.

        Parameters:
            content_info (None):   This always uses the internal file_path to create the contents.
            overwrite:  If False (The Default), do not overwrite existing contents if any.

        """
        if self._contents and not overwrite:
            return

        if self.sidecar:
            self._contents = TabularInput(file=self.file_path, sidecar=self.sidecar.contents,
                                          name=os.path.realpath(self.file_path))
            self.has_hed = True
        else:
            self._contents = TabularInput(file=self.file_path, name=os.path.realpath(self.file_path))
        columns = self._contents.columns
        if 'HED' in columns or 'HED_assembled' in columns:
            self.has_hed = True

    def set_sidecar(self, sidecar):
        """ Set the sidecar for this tabular file.

        Parameters:
            sidecar (Sidecar):  The sidecar for this tabular file.

        """
        self.sidecar = sidecar