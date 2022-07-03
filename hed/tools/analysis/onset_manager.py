from hed.models import HedString, TagExpressionParser
from hed.errors import HedFileError
from hed.models import Sidecar, TabularInput
from hed.schema import load_schema_version
from hed.tools.analysis.analysis_util import get_assembled_strings
import pandas as pd


class OnsetGroup:
    def __init__(self, name, start_index, end_index=None, contents=None):
        self.name = name
        self.start_index = start_index
        self.end_index = end_index
        self.contents = contents

    def __str__(self):
        return f"{self.name}:[{self.start_index}, {self.end_index}] contents {str(self.contents)}"


class OnsetManager:

    def __init__(self, events, schema):
        """ Create an onset manager for an events file.

        Args:
            events (TabularInput): A tabular input file with an onset column and relevant sidecar included.
            schema (HedSchema or HedSchemaGroup): The HED schema to use.

        """
        self.events = events
        self.schema = schema
        hed_strings, defs = get_assembled_strings(events, hed_schema=schema, expand_defs=False)
        self.hed_strings = hed_strings
        self.definitions = defs

    def create_onsets(self):
        for index, hed in enumerate(self.hed_strings):
            tag_tuples = hed.find_tags(['Onset'], recursive=False, include_groups=2)
            print("to here")


if __name__ == '__main__':
    import os

    schema = load_schema_version(xml_version="8.1.0")
    # test_string = 'Experiment-structure,(Def/Right-sym-cond,(Red),Onset),(Def/Initialize-recording,Onset)'
    # hed_1 = HedString(test_string, hed_schema=schema)
    # tag_tuples = hed_1.find_def_tags(recursive=True, include_groups=3)
    # index = 0
    # onset_dict = {}
    # onset_list = []
    # # tag_tuples = hed.find_tags(['Onset'], recursive=False, include_groups=1)
    # for tup in tag_tuples:
    #     name = tup[0].extension_or_value_portion
    #     children = tup[2].children
    #     groups = tup[2].groups()
    #     tups = tup[2].find_tags("Onset")
    #     x = tup[2].find_tags_with_term("Onset", recursive=False, include_groups=0)
    #     if x:
    #         onset_element = onset_dict.pop(name, None)
    #         if onset_element:
    #             onset_element.end_index = index
    #             onset_list.append(onset_element)
    #         groups = tup[2].groups()
    #         if groups:
    #             contents = groups[0]
    #         else:
    #             contents = None
    #         ongroup = OnsetGroup(name, index, contents=contents)
    #         print(ongroup)
    #         onset_dict[name] = ongroup
    #         continue
    #     y = tup[2].find_tags_with_term("Offset", recursive=False, include_groups=0)
    #     if y:
    #         onset_element = onset_dict.pop(name, None)
    #         if not onset_element:
    #             raise HedFileError("UnmatchedOnset", f"The offset {name} at event {index} has no onset")
    #         onset_element.end_index = index
    #         onset_list.append(onset_element)
    #
    #

    print("There")

    root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../tests/data/bids/eeg_ds003654s_hed')
    event_path = os.path.join(root_path, 'sub-002/eeg', 'sub-002_task-FacePerception_run-1_events.tsv')
    sidecar_path = os.path.join(root_path, 'task-FacePerception_events.json')
    print(os.path.abspath(event_path))
    print(os.path.abspath(sidecar_path))
    the_sidecar = Sidecar(sidecar_path)
    the_events = TabularInput(event_path, the_sidecar)
    print(the_sidecar)
    print(the_events)
    manager = OnsetManager(the_events, schema)
    hed_strings, defs = get_assembled_strings(the_events, hed_schema=schema, expand_defs=False)
    onset_dict = {}
    onset_list = []
    for index, hed in enumerate(hed_strings):
        tag_tuples = hed.find_def_tags(recursive=True, include_groups=3)
        # tag_tuples = hed.find_tags(['Onset'], recursive=False, include_groups=1)
        for tup in tag_tuples:
            name = tup[0].extension_or_value_portion
            children = tup[2].children
            groups = tup[2].groups()
            tups = tup[2].find_tags("Onset")
            print(f"{index}: {name}")
            x = tup[2].find_tags_with_term("Onset", recursive=False, include_groups=0)
            if x:
                onset_element = onset_dict.pop(name, None)
                if onset_element:
                    onset_element.end_index = index
                    onset_list.append(onset_element)
                groups = tup[2].groups()
                if groups:
                    contents = groups[0]
                else:
                    contents = None
                ongroup = OnsetGroup(name, index, contents=contents)
                onset_dict[name] = ongroup
                continue
            y = tup[2].find_tags_with_term("Offset", recursive=False, include_groups=0)
            if y:
                onset_element = onset_dict.pop(name, None)
                if not onset_element:
                    raise HedFileError("UnmatchedOnset", f"The offset {name} at event {index} has no onset")
                onset_element.end_index = index
                onset_list.append(onset_element)

            print("goodness")
    print("goodness")
    for item in onset_list:
        print(item)

    print("to here")

    # manager.create_onsets()
    #
    # y = '../../../tests/data/curation/sub-001_task-AuditoryVisualShift_run-01_events.tsv'
    # print(os.path.realpath(os.path.abspath(y)))
    # x = TabularInput(file=y, name=os.path.realpath(y))
    # bids_tabular_file.py
    # events_file =
    # for item in onset_list:
    #     print(item)
    # print("toHere")
