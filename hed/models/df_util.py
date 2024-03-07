""" Utilities for assembly and conversion of HED strings to different forms. """
import re
from functools import partial
import pandas as pd
from hed.models.hed_string import HedString


def get_assembled(tabular_file, hed_schema, extra_def_dicts=None, defs_expanded=True, return_filtered=False):
    """ Create an array of assembled HedString objects (or list of these) of the same length as tabular file input.

    Parameters:
        tabular_file (TabularInput): Represents the tabular input file.
        hed_schema (HedSchema): If str, will attempt to load as a version if it doesn't have a valid extension.
        extra_def_dicts: list of DefinitionDict, optional
            Any extra DefinitionDict objects to use when parsing the HED tags.
        defs_expanded (bool): (Default True) Expands definitions if True, otherwise shrinks them.
        return_filtered (bool): If true, combines lines with the same onset.
            Further lines with that onset are marked n/a
    Returns:
        tuple:
            hed_strings(list of HedStrings): A list of HedStrings
            def_dict(DefinitionDict): The definitions from this Sidecar.
    """

    def_dict = tabular_file.get_def_dict(hed_schema, extra_def_dicts=extra_def_dicts)
    series_a = tabular_file.series_a if not return_filtered else tabular_file.series_filtered
    if defs_expanded:
        return [HedString(x, hed_schema, def_dict).expand_defs() for x in series_a], def_dict
    else:
        return [HedString(x, hed_schema, def_dict).shrink_defs() for x in series_a], def_dict


def convert_to_form(df, hed_schema, tag_form, columns=None):
    """ Convert all tags in underlying dataframe to the specified form (in place).

    Parameters:
        df (pd.Dataframe or pd.Series): The dataframe or series to modify.
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
        df (pd.Dataframe or pd.Series): The dataframe or series to modify.
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
        df (pd.Dataframe or pd.Series): The dataframe or series to modify.
        hed_schema (HedSchema or None): The schema to use to identify defs.
        def_dict (DefinitionDict): The definitions to expand.
        columns (list or None): The columns to modify on the dataframe.
    """
    if isinstance(df, pd.Series):
        mask = df.str.contains('Def/', case=False)
        df[mask] = df[mask].apply(partial(_expand_defs, hed_schema=hed_schema, def_dict=def_dict))
    else:
        if columns is None:
            columns = df.columns

        for column in columns:
            mask = df[column].str.contains('Def/', case=False)
            df.loc[mask, column] = df.loc[mask, column].apply(partial(_expand_defs,
                                                                      hed_schema=hed_schema, def_dict=def_dict))


def _convert_to_form(hed_string, hed_schema, tag_form):
    return str(HedString(hed_string, hed_schema).get_as_form(tag_form))


def _shrink_defs(hed_string, hed_schema):
    return str(HedString(hed_string, hed_schema).shrink_defs())


def _expand_defs(hed_string, hed_schema, def_dict):
    return str(HedString(hed_string, hed_schema, def_dict).expand_defs())


def process_def_expands(hed_strings, hed_schema, known_defs=None, ambiguous_defs=None):
    """ Gather def-expand tags in the strings/compare with known definitions to find any differences.

    Parameters:
        hed_strings (list or pd.Series): A list of HED strings to process.
        hed_schema (HedSchema): The schema to use.
        known_defs (DefinitionDict or list or str or None):
            A DefinitionDict or anything its constructor takes.  These are the known definitions going in, that must
            match perfectly.
        ambiguous_defs (dict): A dictionary containing ambiguous definitions.
            format TBD.  Currently def name key: list of lists of HED tags values

    Returns:
        tuple: A tuple containing the DefinitionDict, ambiguous definitions, and errors.
    """
    from hed.models.def_expand_gather import DefExpandGatherer
    def_gatherer = DefExpandGatherer(hed_schema, known_defs, ambiguous_defs)
    return def_gatherer.process_def_expands(hed_strings)


def sort_dataframe_by_onsets(df):
    """ Gather def-expand tags in the strings/compare with known definitions to find any differences.

    Parameters:
        df(pd.Dataframe): Dataframe to sort.

    Returns:
        The sorted dataframe, or the original dataframe if it didn't have an onset column.
    """
    if "onset" in df.columns:
        # Create a copy and sort by onsets as floats(if needed), but continue to keep the string version.
        df_copy = df.copy()
        df_copy['_temp_onset_sort'] = df_copy['onset'].astype(float)
        df_copy.sort_values(by='_temp_onset_sort', inplace=True)
        df_copy.drop(columns=['_temp_onset_sort'], inplace=True)

        return df_copy
    return df


def replace_ref(text, newvalue, column_ref):
    """ Replace column ref in x with y.  If it's n/a, delete extra commas/parentheses.

    Parameters:
        text (str): The input string containing the ref enclosed in curly braces.
        newvalue (str): The replacement value for the ref.
        column_ref (str): The ref to be replaced, without curly braces.

    Returns:
        str: The modified string with the ref replaced or removed.
    """
    # Note: This function could easily be updated to handle non-curly brace values, but it seemed faster this way

    # If it's not n/a, we can just replace directly.
    if newvalue != "n/a":
        return text.replace(f"{{{column_ref}}}", newvalue)

    def _remover(match):
        p1 = match.group("p1").count("(")
        p2 = match.group("p2").count(")")
        if p1 > p2:  # We have more starting parens than ending.  Make sure we don't remove comma before
            output = match.group("c1") + "(" * (p1 - p2)
        elif p2 > p1:  # We have more ending parens.  Make sure we don't remove comma after
            output = ")" * (p2 - p1) + match.group("c2")
        else:
            c1 = match.group("c1")
            c2 = match.group("c2")
            if c1:
                c1 = ""
            elif c2:
                c2 = ""
            output = c1 + c2

        return output

    # this finds all surrounding commas and parentheses to a reference.
    # c1/c2 contain the comma(and possibly spaces) separating this ref from other tags
    # p1/p2 contain the parentheses directly surrounding the tag
    # All four groups can have spaces.
    pattern = r'(?P<c1>[\s,]*)(?P<p1>[(\s]*)\{' + column_ref + r'\}(?P<p2>[\s)]*)(?P<c2>[\s,]*)'
    return re.sub(pattern, _remover, text)


def _handle_curly_braces_refs(df, refs, column_names):
    """ Fills in the refs in the dataframe

        You probably shouldn't call this function directly, but rather use base input.

    Parameters:
        df(pd.DataFrame): The dataframe to modify
        refs(list or pd.Series): a list of column refs to replace(without {})
        column_names(list): the columns we are interested in(should include all ref columns)

    Returns:
        modified_df(pd.DataFrame): The modified dataframe with refs replaced
    """
    # Filter out columns and refs that don't exist.
    refs = [ref for ref in refs if ref in column_names]
    remaining_columns = [column for column in column_names if column not in refs]

    new_df = df.copy()
    # Replace references in the columns we are saving out.
    saved_columns = new_df[refs]
    for column_name in remaining_columns:
        for replacing_name in refs:
            # If the data has no n/a values, this version is MUCH faster.
            # column_name_brackets = f"{{{replacing_name}}}"
            # df[column_name] = pd.Series(x.replace(column_name_brackets, y) for x, y
            #                             in zip(df[column_name], saved_columns[replacing_name]))
            new_df[column_name] = pd.Series(replace_ref(x, y, replacing_name) for x, y
                                        in zip(new_df[column_name], saved_columns[replacing_name]))
    new_df = new_df[remaining_columns]

    return new_df
