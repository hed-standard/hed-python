""" Utilities for assembly and conversion of HED strings to different forms. """
import re
import math
from collections import defaultdict
from functools import partial
import pandas as pd
from hed.models.hed_string import HedString
from hed.models.model_constants import DefTagNames
from hed.models.definition_dict import DefinitionDict


def convert_to_form(df, hed_schema, tag_form, columns=None):
    """ Convert all tags in underlying dataframe to the specified form (in place).

    Parameters:
        df (pd.Dataframe or pd.Series): The dataframe or series to modify.
        hed_schema (HedSchema): The schema to use to convert tags.
        tag_form (str): HedTag property to convert tags to.
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


def process_def_expands(hed_strings, hed_schema, known_defs=None, ambiguous_defs=None) -> tuple ['DefinitionDict', dict, dict]:
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
        tuple [DefinitionDict, dict, dict]: A tuple containing the DefinitionDict, ambiguous definitions, and a
                                            dictionary of error lists keyed by definition name
    """
    from hed.models.def_expand_gather import DefExpandGatherer
    def_gatherer = DefExpandGatherer(hed_schema, known_defs, ambiguous_defs)
    return def_gatherer.process_def_expands(hed_strings)


def sort_dataframe_by_onsets(df):
    """ Gather def-expand tags in the strings/compare with known definitions to find any differences.

    Parameters:
        df(pd.Dataframe): Dataframe to sort.

    Returns:
        pd.DataFrame: The sorted dataframe, or the original dataframe if it didn't have an onset column.
    """
    if "onset" in df.columns:
        # Create a copy and sort by onsets as floats(if needed), but continue to keep the string version.
        df_copy = df.copy()
        df_copy['_temp_onset_sort'] = pd.to_numeric(df_copy['onset'], errors='coerce')
        df_copy.sort_values(by='_temp_onset_sort', inplace=True)
        df_copy.drop(columns=['_temp_onset_sort'], inplace=True)

        return df_copy
    return df


def replace_ref(text, old_value, new_value="n/a"):
    """ Replace column ref in x with y.  If it's n/a, delete extra commas/parentheses.

    Parameters:
        text (str): The input string containing the ref enclosed in curly braces.
        old_value (str): The full tag or ref to replace
        new_value (str): The replacement value for the ref.

    Returns:
        str: The modified string with the ref replaced or removed.
    """
    # If it's not n/a, we can just replace directly.
    if new_value != "n/a" and new_value != "":
        return text.replace(old_value, new_value)

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
    pattern = r'(?P<c1>[\s,]*)(?P<p1>[(\s]*)' + old_value + r'(?P<p2>[\s)]*)(?P<c2>[\s,]*)'
    return re.sub(pattern, _remover, text)


def _handle_curly_braces_refs(df, refs, column_names):
    """ Fills in the refs in the dataframe

        You probably shouldn't call this function directly, but rather use base input.

    Parameters:
        df(pd.DataFrame): The dataframe to modify
        refs(list or pd.Series): a list of column refs to replace(without {})
        column_names(list): the columns we are interested in(should include all ref columns)

    Returns:
        pd.DataFrame: The modified dataframe with refs replaced
    """
    # Filter out columns and refs that don't exist.
    refs_new = [ref for ref in refs if ref in column_names]
    remaining_columns = [column for column in column_names if column not in refs_new]
    other_refs = [ref for ref in refs if ref not in column_names]

    new_df = df.copy()
    # Replace references in the columns we are saving out.
    saved_columns = new_df[refs_new]
    for column_name in remaining_columns:
        for replacing_name in refs_new:
            # If the data has no n/a values, this version is MUCH faster.
            # column_name_brackets = f"{{{replacing_name}}}"
            # df[column_name] = pd.Series(x.replace(column_name_brackets, y) for x, y
            #                             in zip(df[column_name], saved_columns[replacing_name]))
            new_df[column_name] = pd.Series(replace_ref(x, f"{{{replacing_name}}}", y) for x, y
                                            in zip(new_df[column_name], saved_columns[replacing_name]))
    # Handle the special case of {HED} when the tsv file has no {HED} column
    if 'HED' in refs and 'HED' not in column_names:
        for column_name in remaining_columns:
            new_df[column_name] = \
                pd.Series(replace_ref(x, "{HED}", "n/a") for x in new_df[column_name])

    # Handle any other refs that aren't in the dataframe.
    for ref in other_refs:
        for column_name in remaining_columns:
            new_df[column_name] = \
                pd.Series(replace_ref(x, "{" + ref + "}", "n/a") for x in new_df[column_name])
    new_df = new_df[remaining_columns]

    return new_df


# todo: Consider updating this to be a pure string function(or at least, only instantiating the Duration tags)
def split_delay_tags(series, hed_schema, onsets):
    """Sorts the series based on Delay tags, so that the onsets are in order after delay is applied.

    Parameters:
        series(pd.Series or None): the series of tags to split/sort
        hed_schema(HedSchema): The schema to use to identify tags
        onsets(pd.Series or None)

    Returns:
        Union[pd.Dataframe, None]: If we had onsets, a dataframe with 3 columns
            "HED": The HED strings(still str)
            "onset": the updated onsets
            "original_index": the original source line.  Multiple lines can have the same original source line.

    Note: This dataframe may be longer than the original series, but it will never be shorter.
    """
    if series is None or onsets is None:
        return None
    split_df = pd.DataFrame({"onset": onsets, "HED": series, "original_index": series.index})
    delay_strings = [(i, HedString(hed_string, hed_schema)) for (i, hed_string) in series.items() if
                     "delay/" in hed_string.casefold()]
    delay_groups = []
    for i, delay_string in delay_strings:
        duration_tags = delay_string.find_top_level_tags({DefTagNames.DELAY_KEY})
        to_remove = []
        for tag, group in duration_tags:
            onset_mod = tag.value_as_default_unit() + float(onsets[i])
            to_remove.append(group)
            insert_index = split_df['original_index'].index.max() + 1
            split_df.loc[insert_index] = {'HED': str(group), 'onset': onset_mod, 'original_index': i}
        delay_string.remove(to_remove)
        # update the old string with the removals done
        split_df.at[i, "HED"] = str(delay_string)

    for i, onset_mod, group in delay_groups:
        insert_index = split_df['original_index'].index.max() + 1
        split_df.loc[insert_index] = {'HED': str(group), 'onset': onset_mod, 'original_index': i}
    split_df = sort_dataframe_by_onsets(split_df)
    split_df.reset_index(drop=True, inplace=True)

    split_df = filter_series_by_onset(split_df, split_df.onset)
    return split_df


def filter_series_by_onset(series, onsets):
    """Return the series, with rows that have the same onset combined.

    Parameters:
        series(pd.Series or pd.Dataframe): The series to filter.  If dataframe, it filters the "HED" column.
        onsets(pd.Series): The onset column to filter by.

    Returns:
        Union[Series, Dataframe]: the series with rows filtered together.
    """

    indexed_dict = _indexed_dict_from_onsets(pd.to_numeric(onsets, errors='coerce'))
    y = _filter_by_index_list(series, indexed_dict=indexed_dict)
    return y


def _indexed_dict_from_onsets(onsets):
    """Finds series of consecutive lines with the same (or close enough) onset."""
    current_onset = -1000000.0
    tol = 1e-9
    indexed_dict = defaultdict(list)

    for i, onset in enumerate(onsets):
        if math.isnan(onset):  # Ignore NaNs
            continue
        if abs(onset - current_onset) > tol:
            current_onset = onset
        indexed_dict[current_onset].append(i)

    return indexed_dict


def _filter_by_index_list(original_data, indexed_dict):
    """Filters a series or dataframe by the indexed_dict, joining lines as indicated"""
    if isinstance(original_data, pd.Series):
        data_series = original_data
    elif isinstance(original_data, pd.DataFrame):
        data_series = original_data["HED"]
    else:
        raise TypeError("Input must be a pandas Series or DataFrame")

    new_series = pd.Series([""] * len(data_series), dtype=str)
    for onset, indices in indexed_dict.items():
        if indices:
            first_index = indices[0]
            new_series[first_index] = ",".join([str(data_series[i]) for i in indices])

    if isinstance(original_data, pd.Series):
        return new_series
    else:
        result_df = original_data.copy()
        result_df["HED"] = new_series
        return result_df
