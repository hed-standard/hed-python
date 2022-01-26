""" SidecarSummary: Holds a summary of Json Sidecar """

from hed.models.sidecar import Sidecar


class SidecarSummary:

    def __init__(self, sidecar):
        """ Construct a summary of a Sidecar

        Parameters:
            sidecar: Sidecar
            The sidecar to be summarized.

        """
        self.sidecar = sidecar
        self.definitions = {}


    def __str__(self):
        return "Has summary"