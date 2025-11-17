import json
import os
import unittest
import pandas as pd
from hed.models import HedString, TabularInput, Sidecar
from hed.schema import load_schema_version
from hed.tools.analysis.hed_tag_counts import HedTagCounts
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_tag_manager import HedTagManager
from io import StringIO
from hed.models.df_util import expand_defs
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_hed_tags_op import SummarizeHedTagsOp, HedTagSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/"))
        cls.data_path = os.path.realpath(os.path.join(path, "sub-002_task-FacePerception_run-1_events.tsv"))
        cls.json_path = os.path.realpath(os.path.join(path, "task-FacePerception_events.json"))
        base_parameters = {
            "summary_name": "get_summary hed tags",
            "summary_filename": "summarize_hed_tags",
            "tags": {
                "Sensory events": ["Sensory-event", "Sensory-presentation", "Task-stimulus-role", "Experimental-stimulus"],
                "Agent actions": [
                    "Agent-action",
                    "Agent",
                    "Action",
                    "Agent-task-role",
                    "Task-action-type",
                    "Participant-response",
                ],
                "Task properties": ["Task-property"],
                "Objects": ["Item"],
                "Properties": ["Property"],
            },
            "include_context": False,
            "replace_defs": False,
            "remove_types": ["Condition-variable", "Task"],
        }
        cls.base_parameters = base_parameters
        cls.json_parms = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_do_op_no_replace_no_context_remove_on(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertEqual(200, len(df_new), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new.columns), "summarize_hed_type_op has correct number of columns")
        self.assertIn(sum_op.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op.summary_name], HedTagSummary)
        counts = dispatch.summary_dicts[sum_op.summary_name].summary_dict["subj2_run1"]
        self.assertIsInstance(counts, HedTagCounts)
        self.assertEqual(len(counts.tag_dict), 16)
        self.assertIn("def", counts.tag_dict)
        self.assertNotIn("task", counts.tag_dict)
        self.assertNotIn("condition-variable", counts.tag_dict)
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run2", sidecar=self.json_path)
        self.assertEqual(len(dispatch.summary_dicts[sum_op.summary_name].summary_dict["subj2_run2"].tag_dict), 16)

    def test_do_op_options(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.2.0"])
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")

        # no replace, no context, types removed
        parms1 = json.loads(self.json_parms)
        parms1["summary_name"] = "tag summary 1"
        sum_op1 = SummarizeHedTagsOp(parms1)
        df_new1 = sum_op1.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertIsInstance(sum_op1, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        self.assertEqual(200, len(df_new1), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new1.columns), "summarize_hed_type_op has correct number of columns")
        self.assertIn(sum_op1.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op1.summary_name], HedTagSummary)
        counts1 = dispatch.summary_dicts[sum_op1.summary_name].summary_dict["subj2_run1"]
        self.assertIsInstance(counts1, HedTagCounts)
        self.assertEqual(len(counts1.tag_dict), 16)
        self.assertNotIn("event-context", counts1.tag_dict)
        self.assertIn("def", counts1.tag_dict)
        self.assertNotIn("task", counts1.tag_dict)
        self.assertNotIn("condition-variable", counts1.tag_dict)

        # no replace, context, types removed
        parms2 = json.loads(self.json_parms)
        parms2["include_context"] = True
        parms2["summary_name"] = "tag summary 2"
        sum_op2 = SummarizeHedTagsOp(parms2)
        df_new2 = sum_op2.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertIsInstance(sum_op2, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        self.assertEqual(200, len(df_new2), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new2.columns), "summarize_hed_type_op has correct number of columns")
        self.assertIn(sum_op2.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op2.summary_name], HedTagSummary)
        counts2 = dispatch.summary_dicts[sum_op2.summary_name].summary_dict["subj2_run1"]
        self.assertIsInstance(counts2, HedTagCounts)
        self.assertEqual(len(counts2.tag_dict), len(counts1.tag_dict) + 1)
        self.assertIn("event-context", counts2.tag_dict)
        self.assertIn("def", counts2.tag_dict)
        self.assertNotIn("task", counts2.tag_dict)
        self.assertNotIn("condition-variable", counts2.tag_dict)

        # no replace, context, types removed
        parms3 = json.loads(self.json_parms)
        parms3["include_context"] = True
        parms3["replace_defs"] = True
        parms3["summary_name"] = "tag summary 3"
        sum_op3 = SummarizeHedTagsOp(parms3)
        df_new3 = sum_op3.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertIsInstance(sum_op3, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        self.assertEqual(200, len(df_new3), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new3.columns), "summarize_hed_type_op has correct number of columns")
        self.assertIn(sum_op3.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op3.summary_name], HedTagSummary)
        counts3 = dispatch.summary_dicts[sum_op3.summary_name].summary_dict["subj2_run1"]
        self.assertIsInstance(counts3, HedTagCounts)
        self.assertEqual(33, len(counts3.tag_dict))
        self.assertIn("event-context", counts3.tag_dict)
        self.assertNotIn("def", counts3.tag_dict)
        self.assertNotIn("task", counts3.tag_dict)
        self.assertNotIn("condition-variable", counts3.tag_dict)

    def test_quick3(self):
        remove_types = []
        my_schema = load_schema_version("8.2.0")
        my_json = {
            "code": {"HED": {"code1": "((Def/Blech1, Green), Blue)", "code2": "((Def/Blech3, Description/Help me), Blue)"}},
            "defs": {"HED": {"def1": "(Definition/Blech1, (Condition-variable/Cat, Description/this is hard))"}},
        }
        my_json_str = json.dumps(my_json)
        my_sidecar = Sidecar(StringIO(my_json_str))
        data = [
            [0.5, 0, "code1", "Description/This is a test, Label/Temp, (Def/Blech1, Green)"],
            [0.6, 0, "code2", "Sensory-event, ((Description/Animal, Condition-variable/Blech))"],
        ]
        df = pd.DataFrame(data, columns=["onset", "duration", "code", "HED"])
        input_data = TabularInput(df, sidecar=my_sidecar, name="myName")
        tag_man = HedTagManager(EventManager(input_data, my_schema), remove_types=remove_types)
        counts = HedTagCounts("myName", 2)
        self.assertIsInstance(counts, HedTagCounts)
        self.assertIsInstance(tag_man, HedTagManager)
        # hed_objs = tag_man.get_hed_objs(include_context=include_context, replace_defs=replace_defs)
        # for hed in hed_objs:
        #     counts.update_tag_counts(hed, 'myName')
        # summary_dict['myName'] = counts

    def test_quick4(self):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/"))
        data_path = os.path.realpath(os.path.join(path, "sub-002_task-FacePerception_run-1_events.tsv"))
        json_path = os.path.realpath(os.path.join(path, "task-FacePerception_events.json"))
        schema = load_schema_version("8.1.0")
        sidecar = Sidecar(
            json_path,
        )
        input_data = TabularInput(data_path, sidecar=sidecar)
        counts = HedTagCounts("myName", 2)
        summary_dict = {}
        definitions = input_data.get_def_dict(schema)
        df = pd.DataFrame({"HED_assembled": input_data.series_a})
        expand_defs(df, schema, definitions)

        # type_defs = input_data.get_definitions().gathered_defs
        for hed in df["HED_assembled"]:
            counts.update_tag_counts(HedString(hed, schema), "myName")
        summary_dict["myName"] = counts

    def test_get_summary_details(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")
        sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertIn(sum_op.summary_name, dispatch.summary_dicts)
        sum_context = dispatch.summary_dicts[sum_op.summary_name]
        self.assertIsInstance(sum_context, HedTagSummary)
        sum_obj1 = sum_context.get_summary_details()
        self.assertIsInstance(sum_obj1, dict)
        json_str1 = json.dumps(sum_obj1, indent=4)
        self.assertIsInstance(json_str1, str)
        json_obj1 = json.loads(json_str1)
        self.assertIsInstance(json_obj1, dict)
        sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run2", sidecar=self.json_path)
        sum_context2 = dispatch.summary_dicts[sum_op.summary_name]
        sum_obj2 = sum_context2.get_summary_details()
        json_str2 = json.dumps(sum_obj2, indent=4)
        self.assertIsInstance(json_str2, str)
        sum_obj3 = sum_context2.get_summary_details(include_individual=False)
        self.assertFalse(sum_obj3["Individual files"])

    def test_get_summary_text_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")
        df = dispatch.prep_data(df)
        sum_op.do_op(dispatch, df, "subj2_run1", sidecar=self.json_path)
        sum_op.do_op(dispatch, df, "subj2_run2", sidecar=self.json_path)
        sum_context1 = dispatch.summary_dicts[sum_op.summary_name]
        text_sum_none = sum_context1.get_text_summary(individual_summaries="none")
        self.assertIn("Dataset", text_sum_none)
        self.assertIsInstance(text_sum_none["Dataset"], str)
        self.assertFalse(text_sum_none.get("Individual files", {}))

        text_sum_consolidated = sum_context1.get_text_summary(individual_summaries="consolidated")
        self.assertIn("Dataset", text_sum_consolidated)
        self.assertIsInstance(text_sum_consolidated["Dataset"], str)
        self.assertFalse(text_sum_consolidated.get("Individual files", {}))
        self.assertGreater(len(text_sum_consolidated["Dataset"]), len(text_sum_none["Dataset"]))

        text_sum_separate = sum_context1.get_text_summary(individual_summaries="separate")
        self.assertIn("Dataset", text_sum_separate)
        self.assertIsInstance(text_sum_separate["Dataset"], str)
        self.assertIn("Individual files", text_sum_separate)
        self.assertIsInstance(text_sum_separate["Individual files"], dict)
        self.assertEqual(len(text_sum_separate["Individual files"]), 2)

    def test_sample_example(self):
        remodel_list = [
            {
                "operation": "summarize_hed_tags",
                "description": "Produce a summary of HED tags.",
                "parameters": {
                    "summary_name": "summarize_hed_tags",
                    "summary_filename": "summarize_hed_tags",
                    "tags": {
                        "Sensory events": [
                            "Sensory-event",
                            "Sensory-presentation",
                            "Task-stimulus-role",
                            "Experimental-stimulus",
                        ],
                        "Agent actions": [
                            "Agent-action",
                            "Agent",
                            "Action",
                            "Agent-task-role",
                            "Task-action-type",
                            "Participant-response",
                        ],
                        "Objects": ["Item"],
                    },
                    "include_context": False,
                },
            }
        ]

        sample_data = [
            [0.0776, 0.5083, "go", "n/a", 0.565, "correct", "right", "female"],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, 0.49, "correct", "right", "female"],
            [9.5856, 0.5084, "go", "n/a", 0.45, "correct", "right", "female"],
            [13.5939, 0.5083, "succesful_stop", 0.2, "n/a", "n/a", "n/a", "female"],
            [17.1021, 0.5083, "unsuccesful_stop", 0.25, 0.633, "correct", "left", "male"],
            [21.6103, 0.5083, "go", "n/a", 0.443, "correct", "left", "male"],
        ]
        sample_columns = [
            "onset",
            "duration",
            "trial_type",
            "stop_signal_delay",
            "response_time",
            "response_accuracy",
            "response_hand",
            "sex",
        ]

        sidecar_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_events.json")
        )

        dispatch = Dispatcher(remodel_list, data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df = pd.DataFrame(sample_data, columns=sample_columns)
        df = dispatch.prep_data(df)
        for operation in dispatch.parsed_ops:
            df = operation.do_op(dispatch, df, "sample", sidecar=sidecar_path)
        context_dict = dispatch.summary_dicts.get("summarize_hed_tags")
        text_summary = context_dict.get_text_summary()
        self.assertIsInstance(text_summary["Dataset"], str)

    def test_convert_summary_to_word_dict(self):
        # Assume we have a valid summary_json
        summary_json = {
            "Main tags": {
                "tag_category_1": [{"tag": "tag1", "events": 5}, {"tag": "tag2", "events": 3}],
                "tag_category_2": [{"tag": "tag3", "events": 7}],
            }
        }
        expected_output = {"tag1": 5, "tag2": 3, "tag3": 7}

        word_dict = HedTagSummary.summary_to_dict(summary_json, transform=None, scale_adjustment=0)
        self.assertEqual(word_dict, expected_output)


if __name__ == "__main__":
    unittest.main()
