



def get_info_in_columns(dataframe):
    col_info = dict()

    for col_name, col_values in dataframe.iteritems():
        col_info[col_name] = col_values.value_counts(ascending=True).to_dict()
    return col_info