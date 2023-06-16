from functools import partial
import pandas as pd

from hed.models.sidecar import Sidecar
from hed.models.tabular_input import TabularInput
from hed.models.hed_string import HedString
from hed.models.definition_dict import DefinitionDict


def get_assembled(tabular_file, sidecar, hed_schema, extra_def_dicts=None, join_columns=True,
                  shrink_defs=False, expand_defs=True):
    """Load a tabular file and its associated HED sidecar file.

    Args:
        tabular_file: str or TabularInput
            The path to the tabular file, or a TabularInput object representing it.
        sidecar: str or Sidecar
            The path to the sidecar file, or a Sidecar object representing it.
        hed_schema: HedSchema
            If str, will attempt to load as a version if it doesn't have a valid extension.
        extra_def_dicts: list of DefinitionDict, optional
            Any extra DefinitionDict objects to use when parsing the HED tags.
        join_columns: bool
            If true, join all hed columns into one.
        shrink_defs: bool
            Shrink any def-expand tags found
        expand_defs: bool
            Expand any def tags found
    Returns:
        tuple:
            hed_strings(list of HedStrings):A list of HedStrings or a list of lists of HedStrings
            def_dict(DefinitionDict): The definitions from this Sidecar
    """
    if isinstance(sidecar, str):
        sidecar = Sidecar(sidecar)

    if isinstance(tabular_file, str):
        tabular_file = TabularInput(tabular_file, sidecar)

    def_dict = None
    if sidecar:
        def_dict = sidecar.get_def_dict(hed_schema=hed_schema, extra_def_dicts=extra_def_dicts)

    if join_columns:
        if expand_defs:
            return [HedString(x, hed_schema, def_dict).expand_defs() for x in tabular_file.series_a], def_dict
        elif shrink_defs:
            return [HedString(x, hed_schema, def_dict).shrink_defs() for x in tabular_file.series_a], def_dict
        else:
            return [HedString(x, hed_schema, def_dict) for x in tabular_file.series_a], def_dict
    else:
        return [[HedString(x, hed_schema, def_dict).expand_defs() if expand_defs
                 else HedString(x, hed_schema, def_dict).shrink_defs() if shrink_defs
                 else HedString(x, hed_schema, def_dict)
                 for x in text_file_row] for text_file_row in tabular_file.dataframe_a.itertuples(index=False)], \
               def_dict


def convert_to_form(df, hed_schema, tag_form, columns=None):
    """ Convert all tags in underlying dataframe to the specified form (in place).

    Parameters:
        df (pd.Dataframe or pd.Series): The dataframe or series to modify
        hed_schema (HedSchema): The schema to use to convert tags.
        tag_form(str): HedTag property to convert tags to.
        columns (list): The columns to modify on the dataframe.

    """
    if isinstance(df, pd.Series):
        df[:] = df.apply(partial(_convert_to_form, hed_schema=hed_schema, tag_form=tag_form))
    else:
        if columns is None:
            columns = df.columns

        for column in columns:
            df[column] = df[column].apply(partial(_convert_to_form, hed_schema=hed_schema, tag_form=tag_form))


def shrink_defs(df, hed_schema, columns=None):
    """ Shrink (in place) any def-expand tags found in the specified columns in the dataframe.

    Parameters:
        df (pd.Dataframe or pd.Series): The dataframe or series to modify
        hed_schema (HedSchema or None): The schema to use to identify defs.
        columns (list or None): The columns to modify on the dataframe.

    """
    if isinstance(df, pd.Series):
        mask = df.str.contains('Def-expand/', case=False)
        df[mask] = df[mask].apply(partial(_shrink_defs, hed_schema=hed_schema))
    else:
        if columns is None:
            columns = df.columns

        for column in columns:
            mask = df[column].str.contains('Def-expand/', case=False)
            df[column][mask] = df[column][mask].apply(partial(_shrink_defs, hed_schema=hed_schema))


def expand_defs(df, hed_schema, def_dict, columns=None):
    """ Expands any def tags found in the dataframe.

        Converts in place

    Parameters:
        df (pd.Dataframe or pd.Series): The dataframe or series to modify
        hed_schema (HedSchema or None): The schema to use to identify defs
        def_dict (DefinitionDict): The definitions to expand
        columns (list or None): The columns to modify on the dataframe
    """
    if isinstance(df, pd.Series):
        mask = df.str.contains('Def/', case=False)
        df[mask] = df[mask].apply(partial(_expand_defs, hed_schema=hed_schema, def_dict=def_dict))
    else:
        if columns is None:
            columns = df.columns

        for column in columns:
            mask = df[column].str.contains('Def/', case=False)
            df.loc[mask, column] = df.loc[mask, column].apply(partial(_expand_defs, hed_schema=hed_schema, def_dict=def_dict))


def _convert_to_form(hed_string, hed_schema, tag_form):
    return str(HedString(hed_string, hed_schema).get_as_form(tag_form))


def _shrink_defs(hed_string, hed_schema):
    return str(HedString(hed_string, hed_schema).shrink_defs())


def _expand_defs(hed_string, hed_schema, def_dict):
    return str(HedString(hed_string, hed_schema, def_dict).expand_defs())


def process_def_expands(hed_strings, hed_schema, known_defs=None, ambiguous_defs=None):
    """ Processes a list of HED strings according to a given HED schema,
            using known definitions and ambiguous definitions.

    Parameters:
        hed_strings (list or pd.Series): A list of HED strings to process.
        hed_schema (HedSchema): The schema to use
        known_defs (DefinitionDict or list or str), optional):
            A DefinitionDict or anything its constructor takes.  These are the known definitions going in, that must
            match perfectly.
        ambiguous_defs (dict): A dictionary containing ambiguous definitions
            format TBD.  Currently def name key: list of lists of hed tags values
    """
    from hed.models.def_expand_gather import DefExpandGatherer
    def_gatherer = DefExpandGatherer(hed_schema, known_defs, ambiguous_defs)
    return def_gatherer.process_def_expands(hed_strings)
