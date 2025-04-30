import os
from hed import load_schema_version
from hed.tools.analysis.event_manager import EventManager
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.hed_tag_manager import HedTagManager

# Excluding tags for condition-variables and task -- these can be done separately if we want to.
REMOVE_TYPES = ['Condition-variable', 'Task']

# Tags organized by whether they are found with either of these
MATCH_TYPES = ['Experimental-stimulus', 'Participant-response', 'Incidental', 'Instructional', 'Mishap',
               'Task-activity', 'Warning', 'Sensory-event', 'Agent-action']

# If a tag has any of these as a parent, it is excluded
EXCLUDED_PARENTS = {'data-marker', 'data-resolution', 'quantitative-value', 'spatiotemporal-value',
                    'statistical-value', 'informational-property', 'organizational-property',
                    'grayscale', 'hsv-color', 'rgb-color', 'luminance', 'luminance-contrast', 'opacity',
                    'task-effect-evidence', 'task-relationship', 'relation'}

# If a tag has any of these as a parent, it is replaced by this parent only
CUTOFF_TAGS = {'blue-color', 'brown-color', 'cyan-color', 'gray-color', 'green-color', 'orange-color',
               'pink-color', 'purple-color', 'red-color', 'white-color', 'yellow-color',
               'visual-presentation'}

# These tags are removed at the end as non-informational
FILTERED_TAGS = {'event', 'agent', 'action', 'move-body-part', 'item', 'biological-item', 'anatomical-item', 'body-part',
                 'lower-extremity-part', 'upper-extremity-part', 'head-part', 'torso-part', 'face-part',
                 'language-item', 'object', 'geometric-object',
                 'man-made-object', 'device', 'computing-device', 'io-device', 'input-device', 'output-device',
                 'auditory-device', 'display-device',
                 'recording-device', 'natural-object', 'document', 'media', 'media-clip', 'visualization',
                 'property', 'agent-property', 'agent-state',
                 'agent-cognitive-state', 'agent-emotional-state', 'agent-physiological-state', 'agent-postural-state',
                 'agent-task-role', 'agent-trait',
                 'data-property', 'biological-artifact', 'nonbiological-artifact',
                 'spatial-property', 'temporal-property', 'spectral-property', 'dara-source-type', 'data-value',
                 'categorical-value', 'categorical-class-value', 'categorical-judgment-value',
                 'categorical-level-value', 'categorical-location-value', 'categorical-orientation-value',
                 'physical-value', 'data-variability-attribute', 'environmental-property', 'sensory-property',
                 'sensory-attribute', 'auditory-attribute', 'gustatory-attribute', 'olfactory-attribute',
                 'tactile-attribute', 'visual-attribute', 'sensory-presentation', 'task-property', 'task-action-type',
                 'task-attentional-demand', 'task-event-role', 'task-stimulus-role'}

def extract_tag_summary(hed_schema, tsv_file, sidecar_file=None, name=None):
    """ Extract a summary of the tags in a given tabular input file.
    Parameters:
        hed_schema (HedSchema): The HedSchema object to use for the summary.
        tsv_file(str): The path of the tsv file
        sidecar_file (str): The sidecar file to use for the summary.
        name (str): The name of the summary.

    Returns:
        dict: A dictionary with the summary information.
    """

    group_dict = {key: set() for key in MATCH_TYPES}
    other = set()
    input_data = TabularInput(tsv_file, sidecar=sidecar_file, name=name)
    event_manager = EventManager(input_data, hed_schema)
    tag_man = HedTagManager(event_manager, remove_types=REMOVE_TYPES)
    hed_objs = tag_man.get_hed_objs(include_context=False, replace_defs=True)
    for hed in hed_objs:
        if not hed:
            continue
        all_tags = hed.get_all_tags()
        found = False
        for key, tags in group_dict.items():
            if match_tags(all_tags, key):
                group_dict[key] = update_tags(group_dict[key], all_tags)
                found = True
                break
        if not found:
           other = update_tags(other, all_tags)

    for key, tags in group_dict.items():
        group_dict[key] = tags - FILTERED_TAGS
    other = other - FILTERED_TAGS
    return group_dict, other


def match_tags(all_tags, key):
    return any(tag.short_base_tag == key for tag in all_tags)


def update_tags(tag_set, all_tags):
    for tag in all_tags:
        terms = tag.tag_terms
        if any(item in EXCLUDED_PARENTS for item in terms):
            continue
        match = next((item for item in terms if item in CUTOFF_TAGS), None)
        if match:
            tag_set.add(match)
        else:
            tag_set.update(tag.tag_terms)
    return tag_set


if __name__ == '__main__':
    schema = load_schema_version('8.4.0')
    root_dir = 'g:/HEDExamples/hed-examples/datasets/eeg_ds003645s_hed'
    sidecar_path = os.path.join(root_dir, 'task-FacePerception_events.json')
    tsv_path = os.path.join(root_dir, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')

    tag_dict, others = extract_tag_summary(schema, tsv_path, sidecar_file=sidecar_path, name='eeg_ds003645s_hed')

    for the_key, the_item in tag_dict.items():
        if not the_item:
            continue
        print(f"{the_key}:")
        for tag in the_item:
            print(f"  {tag}")

    print("Other:")
    for tag in others:
        print(f"  {tag}")