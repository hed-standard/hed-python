import pandas as pd
import os
from functools import lru_cache


class BidsFile:
    def __init__(self, file_path):
        """ Constructor for a file path.

        Parameters:
            file_path(str): Full path of the file.

        """
        self.file_path = os.path.realpath(file_path)
        [self.basename, self.suffix, self.extension, self.entities] = self.get_entities(self.file_path)
        self._contents = None
        self.has_hed = False

    @property
    def contents(self):
        """ Return the current contents of this object. """
        return self._contents

    @staticmethod
    def get_entities(file_path):
        basename = os.path.basename(file_path)
        stem = basename.split('.', 1)
        if len(stem) == 2:
            extension = stem[1]
        else:
            extension = ''
        suffix = ''
        parts = stem[0].split('_')
        if len(parts) > 1 or parts[-1].isalnum():
            suffix = parts.pop()
        entities = {}
        for part in parts:
            entity, _, label = part.partition('-')
            entities[entity] = label if label else 'NO_ENTITY'
        return basename, suffix, extension, entities


class JsonFile(BidsFile):

    def __init__(self, file_path):
        """ Constructor for a file path.

        Parameters:
            file_path(str): Full path of the file.

        """
        super().__init__(file_path)
        self._initialize_contents()

    def _initialize_contents(self):
        # Read the sidecar as a string
        with open(self.file_path, 'r', encoding='utf-8') as fp:
            json_string = fp.read()

        if '"HED":' in json_string:
            self.has_hed = True
            self._contents = json_string


class TabularFile(BidsFile):

    def __init__(self, file_path):
        """ Constructor for a file path.

        Parameters:
            file_path(str): Full path of the file.

        """
        super().__init__(file_path)
        self._initialize_contents()

    def _initialize_contents(self):
        # Read the tsv header if the file is not empty
        try:
            self._contents = list(pd.read_csv(self.file_path, sep='\t', nrows=0).columns)
            if '"HED":' in self._contents:
                self.has_hed = True
        except Exception as e:
            self._contents = None


@lru_cache(maxsize=None)
def get_bids_file(filename):
    # dot = filename.find('.')
    # if dot == -1:
    #     stem, extension = filename, ''
    # else:
    #     stem, extension = filename[:dot], filename[dot:]
    splits = filename.split('.')
    if len(splits) != 2:
        return None
    extension = splits[1].lower()
    if extension == '.json':
        return JsonFile(filename)
    elif extension == '.tsv':
        return TabularFile(filename)
    else:
        return None
