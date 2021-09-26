# This example shows how to use the python tools to analyze and event file
from hed.tools import get_event_counts, get_file_list

if __name__ == '__main__':
    bids_path = "G:\AttentionShift"
    file_list = get_file_list(bids_path, types=[".tsv"], suffix="_events")
    print(f"Bids dataset {bids_path} has {len(file_list)} event files")
    count_dicts = get_event_counts(bids_path, skip_cols=["onset", "duration", "sample", "HED"])

    for col_name, col_counts in count_dicts.items():
        print(f"\n{col_name}:")
        sorted_counts = sorted(col_counts.items())

        for key, value in sorted_counts:
            print(f"\t{key}: {value}")

    print("to here")