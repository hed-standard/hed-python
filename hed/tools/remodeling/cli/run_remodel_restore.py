import argparse
from hed.tools.util.io_util import find_task_files, replace_new_with_old


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Converts event files based on a json file specifying operations.""")
    parser.add_argument("bids_dir", help="Dataset whose _orig_events.tsv become _events.tsv")
    parser.add_argument("-t", dest="task_name", help="")
    args = parser.parse_args()

    all_events_path = find_task_files(args.bids_dir)

    status = True
    for event_path in all_events_path:
        if not replace_new_with_old(event_path):
            print(f"Replacement of {event_path} failed.")
            status = False

    if status:
        print(f"The files were successfully replaced.")
