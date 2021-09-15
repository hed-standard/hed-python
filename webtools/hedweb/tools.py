
def get_key_value(key, column_values, categorical=True):
    """  Creates the sidecar value dictionary for a given column name in an events.tsv file
        :param key: Name of the column in the events file
        :type key: str
        :param column_values: A list of the unique values in the column if it is a categorical column otherwise ignored.
        :type column_values: list
        :param categorical: If true the column contains categorical values and the result will be a dictionary,
            defaults to True
        :return: A dictionary representing the extracted values for a given column name.
        :rtype: dict
    """

    key_value = {"Description":  f"Description for {key}", "HED": ''}
    if not column_values:
        return key_value
    elif categorical:
        levels = {}
        hed = {}
        for val_key in column_values.keys():
            levels[val_key] = f"Level for {val_key}"
            hed[val_key] = f"Description/Tags for {val_key}"
        key_value["Levels"] = levels
    else:
        hed = "Label/#"
    key_value["HED"] = hed
    return key_value


def get_sidecar_dict(columns_info, columns_selected):
    """  Extracts a sidecar dictionary suitable for direct conversion to JSON sidecar.
        :param columns_info: A dict with column names of an events file as keys and values that are dictionaries
            of unique column entries.
        :type columns_info: dict
        :param columns_selected: A dict with keys that are names of columns that should be documented
            in the JSON sidecar.
        :type columns_selected: list
        :return: A dictionary suitable for conversion to JSON sidecar.
        :rtype: dict
        :return: A list of issues if errors, otherwise empty.
        :rtype: list
    """

    hed_dict = {}
    issues = []
    if not columns_selected:
        return hed_dict, [{'code': 'HED_EMPTY_COLUMN_SELECTION', 'severity': 1,
                          'message': "Must select at least one column"}]
    elif not columns_info:
        return hed_dict, [{'code': 'HED_NO_COLUMNS', 'severity': 1,
                          'message': "Must have columns to do extraction"}]
    for key in columns_selected:
        if key not in columns_info:
            issues += [{'code': 'HED_INVALID_COLUMN_NAME', 'severity': 1,
                       'message': f"{key} is not a valid column name to select"}]
        else:
            hed_dict[key] = get_key_value(key, columns_info[key], columns_selected[key])
    return hed_dict, issues
