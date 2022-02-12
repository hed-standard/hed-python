""" Utilities to facilitate annotation of events in BIDS. """
from pandas import DataFrame


def df_to_hed(dataframe):
    """ Creates a sidecar-like dictionary from a four-column dataframe.

    Args:
        dataframe (DataFrame): A four-column Pandas DataFrame with specific columns.

    Returns:
        dict compatible with BIDS JSON events.

    The DataFrame must have the columns with names: column_name, column_value,
        description, and HED.
    """

    hed_dict = {}

    for index, row in dataframe.iterrows():
        name = row['column_name']
        if name not in hed_dict:
            hed_dict[name] = {"HED": None}
        _update_dict(hed_dict[name], row)

    return hed_dict


def extract_tag(tag_string, tag):
    search_tag = tag.lower()
    pieces = tag_string.split(',')
    remainder = ''
    extracted = []
    separator = ''
    for piece in pieces:
        ind = piece.lower().find(search_tag)
        if ind==-1:
            remainder = remainder + separator + piece
            separator = ','
        else:
            extracted.append(piece[(ind + len(tag)):])
    return remainder, extracted


def generate_sidecar_entry(column_name, column_values):
    """  Creates the sidecar column dictionary for a given column name

    Args:
        column_name (str):       Name of the column
        column_values (list):    List of column values

     Returns:
         dict   A dictionary representing a template for a sidecar entry.
    """

    sidecar_entry = {"Description": f"Description for {column_name}", "HED": ""}
    print(f"column_name:{column_name}")
    if not column_values:
        sidecar_entry["HED"] = "Label/#"
    else:
        levels = {}
        hed = {}
        for column_value in column_values:
            print(f"column_value{column_value}")
            if column_value == "n/a":
                continue
            levels[column_value] = f"Level for {column_value}"
            hed[column_value] = f"Description/Tags for {column_value}"
        sidecar_entry["Levels"] = levels
        sidecar_entry["HED"] = hed
    return sidecar_entry


# def get_sidecar_dict(columns_info, selected_columns=None):
#     """  Extracts a sidecar dictionary suitable for direct conversion to JSON sidecar.
#
#     Args:
#         columns_info (dict): Dictionary with column names of an events file as keys and values that are dictionaries
#                              of unique column entries.
#
#         selected_columns (list): A list of column names that should be included
#
#
#     Returns:
#         dict suitable:return: A dictionary suitable for conversion to JSON sidecar.
#         :rtype: dict
#         :return: A list of issues if errors, otherwise empty.
#         :rtype: list
#     """
#
#     hed_dict = {}
#     issues = []
#     if not selected_columns:
#         return hed_dict, [{'code': 'HED_EMPTY_COLUMN_SELECTION', 'severity': 1,
#                            'message': "Must select at least one column"}]
#     elif not columns_info:
#         return hed_dict, [{'code': 'HED_NO_COLUMNS', 'severity': 1,
#                            'message': "Must have columns to do extraction"}]
#     for key in selected_columns:
#         if key not in columns_info:
#             issues += [{'code': 'HED_INVALID_COLUMN_NAME', 'severity': 1,
#                         'message': f"{key} is not a valid column name to select"}]
#         else:
#             hed_dict[key] = get_key_value(key, columns_info[key], selected_columns[key])
#     return hed_dict, issues


def hed_to_df(sidecar_dict, col_names=None, level_desc=True):
    """ Returns a four-column dataframe version of the HED portions of a JSON sidecar.

    Args:
        sidecar_dict (dict):     A dictionary conforming to BIDS JSON events sidecar format.
        col_names (list):   A list of the cols to include in the flattened side car.
        level_desc (bool):  If True, the contents of the Levels is used as description if available.

    Returns:
        dataframe containing four columns representing HED portion of sidecar.

    """

    if not col_names:
        col_names = sidecar_dict.keys()
    column_name = []
    column_value = []
    column_description = []
    hed_tags = []

    for col_key, col_dict in sidecar_dict.items():
        if col_key not in col_names or not isinstance(col_dict, dict):
            continue
        elif 'Levels' in col_dict or 'HED' in col_dict and isinstance(col_dict['HED'], dict):
            keys, values, descriptions, tags = _flatten_cat_col(col_key, col_dict, level_desc=level_desc)
        else:
            keys, values, descriptions, tags = _flatten_val_col(col_key, col_dict)
        column_name = column_name + keys
        column_value = column_value + values
        column_description = column_description + descriptions
        hed_tags = hed_tags + tags

    data = {"column_name": column_name, "column_value": column_value,
            "description": column_description, "HED": hed_tags}
    dataframe = DataFrame(data)
    return dataframe


def merge_hed_dict(sidecar_dict, hed_dict):
    """Update a JSON sidecar based on the hed_dict values

    Args:
        sidecar_dict (dict):    Dictionary representation of a BIDS JSON sidecar.
        hed_dict(dict):         Dictionary derived from a dataframe representation of HED in sidecar.

    """
    for key, value in hed_dict.items():
        if key not in sidecar_dict:
            sidecar_dict[key] = value
        elif isinstance(value['HED'], str):
            sidecar_dict[key]['HED'] = value['HED']
        else:
            tag_dict = sidecar_dict[key]['HED']
            for hed_key, hed_value in value['HED'].items():
                tag_dict[hed_key] = hed_value
            sidecar_dict[key]['HED'] = tag_dict


def _extract_tag(description, tag):
    if description == 'n/a':
        return tag
    else:
        return f"{tag},Description/{description}"

def _flatten_cat_col(col_key, col_dict, level_desc=True):
    keys = []
    values = []
    descriptions = []
    tags = []
    level_dict = {}
    hed_dict = col_dict.get('HED', {})
    if level_desc:
        level_dict = col_dict.get('Levels', {})
    for col_value, entry_value in hed_dict.items():
        keys.append(col_key)
        values.append(col_value)
        if col_value in level_dict:
            descriptions.append(level_dict[col_value])
        else:
            descriptions.append('n/a')
        tags.append(entry_value)
    return keys, values, descriptions, tags


def _flatten_val_col(col_key, col_dict):
    key = col_key
    value = 'n/a'
    description = 'n/a'
    if 'HED' in col_dict:
        tags = col_dict['HED']
    else:
        tags = 'n/a'
    return [key], [value], [description], [tags]


def _update_dict(row_dict, row):
    """Update the dictionary based on the row"""
    if row['column_value'] == 'n/a':
        row_dict["HED"] = "b:" + _extract_tag(row["description"], row["HED"])
        return
    if not row_dict["HED"]:
        row_dict["HED"] = {}
    row_dict["HED"][row['column_value']] = "a:" + _extract_tag(row["description"], row["HED"])


if __name__ == '__main__':
    print("to here")
    # json_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                             '../../../tests/data/bids/eeg_ds003654s_hed/task-FacePerception_events.json'))
    #
    # with open(json_path) as fp:
    #     sidecar_dict = json.load(fp)
    # df = hed_to_df(sidecar_dict, col_names=None)
    # df.iloc[1]['description'] = 'my description1'
    # new_dict = df_to_hed(df)
    # # df.to_csv(, sep='\t', index=False)
    # merge_hed_dict(sidecar_dict, new_dict)

    # bids_root_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath('')),
    #                                  os.path.join('../../tests/data/bids/eeg_ds003654s_hed')))
    # print(f"Bids root path: {bids_root_path}")
    #
    # event_files = get_file_list(bids_root_path, extensions=[".tsv"], name_suffix="_events")
    # column_to_skip = ["onset", "duration", "sample", "stim_file", "trial"]
    # col_dict = ColumnSummary(skip_cols=column_to_skip, name=bids_root_path)
    # for file in event_files:
    #     col_dict.update(file)
    # col_dict.print()
    #
    # side_dict = {}
    # cat_col = col_dict.categorical_info
    # print("to here")
    #
    # for column_name, columns in cat_col.items():
    #     column_values = list(columns.keys())
    #     column_values.sort()
    #     side_dict[column_name] = generate_sidecar_entry(column_name, column_values)
    # str_json = json.dumps(side_dict, indent=4)
    # print(str_json)
    # print("to here 1")
    # print('here')
