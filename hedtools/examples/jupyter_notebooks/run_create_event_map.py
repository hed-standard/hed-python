# This example shows how to use the python tools to analyze and event file
import os
from hed.tools import get_key_counts, get_file_list, make_dataframe

if __name__ == '__main__':
    bids_path = "G:/AttentionShift"
    file_list = get_file_list(bids_path, types=[".tsv"], suffix="_events")
    print(f"Bids dataset {bids_path} has {len(file_list)} event files")
    count_dicts = get_key_counts(bids_path, skip_cols=["onset", "duration", "sample", "HED"])

    for col_name, col_counts in count_dicts.items():
        print(f"\n{col_name}:")
        sorted_counts = sorted(col_counts.items())

        for key, value in sorted_counts:
            print(f"\t{key}: {value}")

    selected_col = 'value'
    df = make_dataframe(count_dicts, selected_col)
    save_path = os.path.join(bids_path, f"event_map.tsv")
    df.to_csv(save_path, sep='\t', na_rep='n/a', index=False)