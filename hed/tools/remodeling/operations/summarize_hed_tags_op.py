""" Summarize the HED tags in collection of tabular files.  """
import os
import numpy as np
import pandas as pd
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.hed_tag_counts import HedTagCounts
from hed.tools.analysis.event_manager import EventManager
from hed.tools.analysis.hed_tag_manager import HedTagManager
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.remodeling.operations.base_summary import BaseSummary
from hed.tools.visualization import tag_word_cloud


class SummarizeHedTagsOp(BaseOp):
    """ Summarize the HED tags in collection of tabular files.

    Required remodeling parameters:
        - **summary_name** (*str*): The name of the summary.
        - **summary_filename** (*str*): Base filename of the summary.
        - **tags** (*dict*): Specifies how to organize the tag output.

    Optional remodeling parameters:
       - **append_timecode** (*bool*): If True, the timecode is appended to the base filename when summary is saved.
       - **include_context** (*bool*): If True, context of events is included in summary.
       - **remove_types** (*list*): A list of type tags such as Condition-variable or Task to exclude from summary.
       - **replace_defs** (*bool*): If True, the def tag is replaced by the contents of the definitions.
       - **word_cloud** (*bool*): If True, output a word cloud visualization.

    The purpose of this op is to produce a summary of the occurrences of HED tags organized in a specified manner.

    Notes: The tags template is a dictionary whose keys are the organization titles (not necessarily tags) for the
    output and whose values are the tags, which if they or their children appear, they will be listed under that
    title.

    """
    NAME = "summarize_hed_tags"

    PARAMS = {
        "type": "object",
        "properties": {
            "summary_name": {
                "type": "string",
                "description": "Name to use for the summary in titles."
            },
            "summary_filename": {
                "type": "string",
                "description": "Name to use for the summary file name base."
            },
            "tags": {
                "type": "object",
                "description": "A dictionary with the template for how output of tags should be organized.",
                "patternProperties": {
                    ".*": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1,
                        "uniqueItems": True
                    },
                    "minProperties": 1,
                    "additionalProperties": False
                }
            },
            "append_timecode": {
                "type": "boolean",
                "description": "If true, the timecode is appended to the base filename so each run has a unique name."
            },
            "include_context": {
                "type": "boolean",
                "description": "If true, tags for events that unfold over time are counted at each intermediate time."
            },
            "remove_types": {
                "type": "array",
                "description": "A list of special tags such as Condition-variable whose influence is to be removed.",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "uniqueItems": True
            },
            "replace_defs": {
                "type": "boolean",
                "description": "If true, then the Def tags are replaced with actual definitions for the count."
            },
            "word_cloud": {
                "type": "object",
                "properties": {
                    "height": {
                        "type": "integer",
                        "description": "Height of word cloud image in pixels."
                    },
                    "width": {
                        "type": "integer",
                        "description": "Width of word cloud image in pixels."
                    },
                    "prefer_horizontal": {
                        "type": "number",
                        "description": "Fraction of the words that are oriented horizontally."
                    },
                    "min_font_size": {
                        "type": "number",
                        "description": "Minimum font size in points for the word cloud words."
                    },
                    "max_font_size": {
                        "type": "number",
                        "description": "Maximum font size in point for the word cloud words."
                    },
                    "set_font": {
                        "type": "boolean",
                        "description": "If true, set the font to a system font (provided by font_path)."

                    },
                    "font_path": {
                        "type": "string",
                        "description": "Path to system font to use for word cloud display (system-specific)."
                    },
                    "scale_adjustment": {
                        "type": "number",
                        "description": "Constant to add to log-transformed frequencies of the words to get scale."
                    },
                    "contour_width": {
                        "type": "number",
                        "description": "Width in pixels of contour surrounding the words."
                    },
                    "contour_color": {
                        "type": "string",
                        "description": "Name of the contour color (uses MatPlotLib names for colors)."
                    },
                    "background_color": {
                        "type": "string",
                        "description": "Name of the background color (uses MatPlotLib names for colors)."
                    },
                    "use_mask": {
                        "type": "boolean",
                        "description": "If true then confine the word display to region within the provided mask."
                    },
                    "mask_path": {
                        "type": "string",
                        "description": "Path of the mask image used to surround the words."
                    }
                },
                "additionalProperties": False
            }
        },
        "required": [
            "summary_name",
            "summary_filename",
            "tags"
        ],
        "additionalProperties": False
    }

    SUMMARY_TYPE = "hed_tag_summary"

    def __init__(self, parameters):
        """ Constructor for the summarize_hed_tags operation.

        Parameters:
            parameters (dict): Dictionary with the parameter values for required and optional parameters.

        """
        super().__init__(parameters)
        self.summary_name = parameters['summary_name']
        self.summary_filename = parameters['summary_filename']
        self.tags = parameters['tags']
        self.append_timecode = parameters.get('append_timecode', False)
        self.include_context = parameters.get('include_context', True)
        self.replace_defs = parameters.get("replace_defs", True)
        self.remove_types = parameters.get("remove_types", [])
        if "word_cloud" not in parameters:
            self.word_cloud = None
        else:
            wc_params = parameters["word_cloud"]
            self.word_cloud = {
                "height": wc_params.get("height", 300),
                "width": wc_params.get("width", 400),
                "prefer_horizontal": wc_params.get("prefer_horizontal", 0.75),
                "min_font_size": wc_params.get("min_font_size", 8),
                "max_font_size": wc_params.get("max_font_size", 15),
                "font_path": wc_params.get("font_path", None),
                "scale_adjustment": wc_params.get("scale_adjustment", 7),
                "contour_width": wc_params.get("contour_width", 3),
                "contour_color": wc_params.get("contour_color", 'black'),
                "background_color": wc_params.get("background_color", None),
                "use_mask": wc_params.get("use_mask", False),
                "mask_path": wc_params.get("mask_path", None)
            }
            if self.word_cloud["use_mask"] and not self.word_cloud["mask_path"]:
                self.word_cloud["mask_path"] = os.path.realpath(
                    os.path.join(os.path.dirname(__file__), '../../../resources/word_cloud_brain_mask.png'))
            if self.word_cloud["font_path"]:
                self.word_cloud["font_path"] = os.path.realpath(self.word_cloud["font_path"])

    def do_op(self, dispatcher, df, name, sidecar=None) -> pd.DataFrame:
        """ Summarize the HED tags present in the dataset.

        Parameters:
            dispatcher (Dispatcher): Manages the operation I/O.
            df (DataFrame): The DataFrame to be remodeled.
            name (str): Unique identifier for the dataframe -- often the original file path.
            sidecar (Sidecar or file-like):  Only needed for HED operations.

        Returns:
            DataFrame: A copy of df.

        Side effect:
            Updates the context.

        """
        df_new = df.copy()
        summary = dispatcher.summary_dicts.get(self.summary_name, None)
        if not summary:
            summary = HedTagSummary(self)
            dispatcher.summary_dicts[self.summary_name] = summary
        summary.update_summary({'df': dispatcher.post_proc_data(df_new), 'name': name,
                                'schema': dispatcher.hed_schema, 'sidecar': sidecar})
        return df_new

    @staticmethod
    def validate_input_data(parameters):
        """ Additional validation required of operation parameters not performed by JSON schema validator. """
        return []


class HedTagSummary(BaseSummary):
    """ Manager of the HED tag summaries. """

    def __init__(self, sum_op):
        """ Constructor for HED tag summary manager.

        Parameters:
            sum_op (SummarizeHedTagsOp): Operation associated with this summary.

        """

        super().__init__(sum_op)
        self.sum_op = sum_op

    def update_summary(self, new_info):
        """ Update the summary for a given tabular input file.

        Parameters:
            new_info (dict):  A dictionary with the parameters needed to update a summary.

        Notes:
            - The summary needs a "name" str, a "schema", a "df, and a "Sidecar".

        """
        counts = HedTagCounts(
            new_info['name'], total_events=len(new_info['df']))
        input_data = TabularInput(
            new_info['df'], sidecar=new_info['sidecar'], name=new_info['name'])
        tag_man = HedTagManager(EventManager(input_data, new_info['schema']), remove_types=self.sum_op.remove_types)
        hed_objs = tag_man.get_hed_objs(include_context=self.sum_op.include_context,
                                        replace_defs=self.sum_op.replace_defs)
        for hed in hed_objs:
            counts.update_tag_counts(hed, new_info['name'])
        self.summary_dict[new_info["name"]] = counts

    def get_details_dict(self, tag_counts) -> dict:
        """ Return the summary-specific information in a dictionary.

        Parameters:
            tag_counts (HedTagCounts):  Contains the counts of tags in the dataset.

        Returns:
            dict: dictionary with the summary results.

        """
        template, unmatched = tag_counts.organize_tags(self.sum_op.tags)
        details = {}
        for key, key_list in self.sum_op.tags.items():
            details[key] = self._get_details(key_list, template, verbose=True)
        leftovers = [value.get_info(verbose=True) for value in unmatched]
        return {"Name": tag_counts.name, "Total events": tag_counts.total_events,
                "Total files": len(tag_counts.files.keys()),
                "Files": [name for name in tag_counts.files.keys()],
                "Specifics": {"Main tags": details, "Other tags": leftovers}}

    def _get_result_string(self, name, result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return a formatted string with the summary for the indicated name.

        Parameters:
            name (str):  Identifier (usually the filename) of the individual file.
            result (dict): The dictionary of the summary results indexed by name.
            indent (str): A string containing spaces used for indentation (usually 3 spaces).

        Returns:
            str: The results in a printable format ready to be saved to a text file.

        Notes:
            This calls _get_dataset_string to get the overall summary string and
            _get_individual_string to get an individual summary string.

        """
        if name == 'Dataset':
            return self._get_dataset_string(result, indent=indent)
        return self._get_individual_string(result, indent=indent)

    def merge_all_info(self) -> 'HedTagCounts':
        """ Create a HedTagCounts containing the overall dataset HED tag  summary.

        Returns:
            HedTagCounts: The overall dataset summary object for HED tag counts.

        """

        all_counts = HedTagCounts('Dataset')
        for key, counts in self.summary_dict.items():
            all_counts.merge_tag_dicts(counts.tag_dict)
            for file_name in counts.files.keys():
                all_counts.files[file_name] = ""
            all_counts.total_events = all_counts.total_events + counts.total_events
        return all_counts

    def save_visualizations(self, save_dir, file_formats=['.svg'], individual_summaries="separate", task_name=""):
        """ Save the summary visualizations if any.

        Parameters:
            save_dir (str):  Path to directory in which visualizations should be saved.
            file_formats (list):  List of file formats to use in saving.
            individual_summaries (str): One of "consolidated", "separate", or "none" indicating what to save.
            task_name (str): Name of task if segregated by task.

        """
        if not self.sum_op.word_cloud:
            return
        else:
            wc = self.sum_op.word_cloud
        # summary = self.get_summary(individual_summaries='none')
        summary = self.get_summary(individual_summaries='none')
        overall_summary = summary.get("Dataset", {})
        overall_summary = overall_summary.get("Overall summary", {})
        specifics = overall_summary.get("Specifics", {})
        word_dict = self.summary_to_dict(specifics, scale_adjustment=wc["scale_adjustment"])

        tag_wc = tag_word_cloud.create_wordcloud(word_dict, mask_path=wc["mask_path"],
                                                 width=wc["width"], height=wc["height"],
                                                 prefer_horizontal=wc["prefer_horizontal"],
                                                 background_color=wc["background_color"],
                                                 min_font_size=wc["min_font_size"], max_font_size=wc["max_font_size"],
                                                 contour_width=wc["contour_width"], contour_color=wc["contour_color"],
                                                 font_path=wc["font_path"])
        svg_data = tag_word_cloud.word_cloud_to_svg(tag_wc)
        cloud_filename = os.path.realpath(os.path.join(save_dir, self.sum_op.summary_name,
                                                       self.sum_op.summary_name + '_word_cloud.svg'))
        with open(cloud_filename, "w") as outfile:
            outfile.writelines(svg_data)

    @staticmethod
    def summary_to_dict(specifics, transform=np.log10, scale_adjustment=7) -> dict:
        """Convert a HedTagSummary json specifics dict into the word cloud input format.

        Parameters:
            specifics (dict): Dictionary with keys "Main tags" and "Other tags".
            transform (func): The function to transform the number of found tags.
                             Default log10
            scale_adjustment (int): Value added after transform.

        Returns:
            dict: A dict of the words and their occurrence count.

        Raises:
            KeyError: A malformed dictionary was passed.

        """
        if transform is None:
            def transform(x):
                return x
        word_dict = {}
        tag_dict = specifics.get("Main tags", {})
        for tag, tag_sub_list in tag_dict.items():
            if tag == "Exclude tags":
                continue
            for tag_sub_dict in tag_sub_list:
                word_dict[tag_sub_dict['tag']] = transform(tag_sub_dict['events']) + scale_adjustment
        other_dict = specifics.get("Other tags", [])
        for tag_sub_list in other_dict:
            word_dict[tag_sub_list['tag']] = transform(tag_sub_list['events']) + scale_adjustment
        return word_dict

    @staticmethod
    def _get_dataset_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the overall summary for all the tabular files.

        Parameters:
            result (dict): Dictionary of merged summary information.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Dataset: Total events={result.get('Total events', 0)} "
                    f"Total files={len(result.get('Files', []))}"]
        sum_list = sum_list + HedTagSummary._get_tag_list(result, indent=indent)
        return "\n".join(sum_list)

    @staticmethod
    def _get_individual_string(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return  a string with the summary for an individual tabular file.

        Parameters:
            result (dict): Dictionary of summary information for a particular tabular file.
            indent (str):  String of blanks used as the amount to indent for readability.

        Returns:
            str: Formatted string suitable for saving in a file or printing.

        """
        sum_list = [f"Total events={result.get('Total events', 0)}"]
        sum_list = sum_list + HedTagSummary._get_tag_list(result, indent=indent)
        return "\n".join(sum_list)

    @staticmethod
    def _tag_details(tags):
        """ Return a list of strings with the tag details.

        Parameters:
            tags (list): List of tags to summarize.

        Returns:
            list: Each entry has the summary details for a tag.

        """
        tag_list = []
        for tag in tags:
            tag_list.append(
                f"{tag['tag']}[{tag['events']},{len(tag['files'])}]")
        return tag_list

    @staticmethod
    def _get_tag_list(result, indent=BaseSummary.DISPLAY_INDENT):
        """ Return a list lines to be output to summarize the tags as organized in the result.

        Parameters:
            result (dict):  Dictionary with the results organized under key "Specifics".
            indent (str):  Spaces to indent each line.

        Returns:
            list:  Each entry is a string representing a line to be printed.

        """
        tag_info = result["Specifics"]
        sum_list = [f"\n{indent}Main tags[events,files]:"]
        for category, tags in tag_info['Main tags'].items():
            sum_list.append(f"{indent}{indent}{category}:")
            if tags:
                sum_list.append(
                    f"{indent}{indent}{indent}{' '.join(HedTagSummary._tag_details(tags))}")
        if tag_info['Other tags']:
            sum_list.append(f"{indent}Other tags[events,files]:")
            sum_list.append(
                f"{indent}{indent}{' '.join(HedTagSummary._tag_details(tag_info['Other tags']))}")
        return sum_list

    @staticmethod
    def _get_details(key_list, template, verbose=False):
        """ Organized a tag information from a list based on the template.

        Parameters:
            key_list (list): List of information to be organized based on the template.
            template (dict): An input template derived from the input parameters.
            verbose (bool): If False (the default) output minimal information about the summary.

        """
        key_details = []
        for item in key_list:
            for tag_cnt in template[item.casefold()]:
                key_details.append(tag_cnt.get_info(verbose=verbose))
        return key_details
