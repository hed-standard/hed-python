from hed.schema.hed_schema_io import load_schema_version
from hed.tools.bids.bids_event_files import BidsEventFiles
from hed.tools.summaries.hed_group_summary import HedGroupSummary


def extract_definitions(bids):
    print("this")


# def test_stuff():
#     hed_version = "8.0.0"
#     hed_str = "Sensory-event, Visual-presentation, Condition-variable/Blah, ((Square, Red)," + \
#               "(Center-of, Computer-screen))"
#     schemas = load_schema_version(xml_version_number=hed_version)
#     obj = HedString(hed_str)
#     obj.convert_to_canonical_forms(schemas)
#     a = obj.get_all_groups()
#     print("Tag groups:")
#     for group in a:
#         print(f"\t{str(group)}")
#
#     b = obj.get_all_tags()
#     print(f"Overall:\n\t{hed_str}")
#     print("Individual tags:")
#     for tag in b:
#         print(f"\t{tag.short_tag}")


if __name__ == '__main__':
    path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
    # path = 'G:\\WH_working3'
    bids = BidsEventFiles(path)
    hed_version = "8.0.0"
    hed_schema = load_schema_version(xml_version_number=hed_version)

    for bids_sidecar in bids.sidecar_dict.values():
        sidecar = bids_sidecar.contents
        def_dicts = [column_entry.def_dict for column_entry in sidecar]
        for a_def in def_dicts:
            defs = a_def._defs
            if not defs:
                continue
            for name, entry in defs.items():
                x = entry.contents
                y = HedGroupSummary(x, hed_schema, name=name)
                w = y.to_json(with_values=True, as_json=False)
                print(w)

        #         y = x.get_all_tags()
        #         for tag in y:
        #             tag.convert_to_canonical_forms(schemas)
        #             print(f"{tag.short_base_tag}: {tag.extension_or_value_portion}")
        #         print("to here")
        # print(f"{sidecar}")
        # break
