# This example shows how to use the python tools to analyze and event file
import os
from hed.tools import get_key_counts, get_file_list, make_dataframe

if __name__ == '__main__':
    # Traverse the directory tree
    bids_root_path = "G:/AttentionShift/AttentionShiftBids"
    file_list = get_file_list(bids_root_path, types=[".tsv"], suffix="_events")
    print(f"Bids dataset {bids_root_path} has {len(file_list)} event files")
    count_dicts = get_key_counts(bids_root_path, skip_cols=["onset", "duration", "sample", "HED"])

    for col_name, col_counts in count_dicts.items():
        print(f"\n{col_name}:")
        sorted_counts = sorted(col_counts.items())

        for key, value in sorted_counts:
            print(f"\t{key}: {value}")

    selected_col = 'value'
    df = make_dataframe(count_dicts, selected_col)
    save_path = os.path.join(bids_root_path, f"Attention_event_map.tsv")
    df.to_csv(save_path, sep='\t', na_rep='n/a', index=False)
