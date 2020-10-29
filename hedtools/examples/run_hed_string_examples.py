"""
Examples of HED validation of a tag string
"""


from hed.validator.hed_validator import HedValidator

if __name__ == '__main__':
    local_hed_file = 'data/HED7.1.1.xml'   # path HED v7.1.1 stored locally

    # Example 1a: Valid HED string for HED <= v7.1.1
    hed_string_1 = 'Event/Label/ButtonPuskDeny, Event/Description/Button push to deny access to the ID holder,' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger)'
    hed_input_reader = HedValidator(hed_string_1, hed_xml_file=local_hed_file)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 1a] hed_string_1 should have no issues with HEDv7.1.1'))

    # Example 1b: Try with the latest version of HED.xml
    hed_input_reader = HedValidator(hed_string_1)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 1b] hed_string_1 probably has no issues with the latest HED version'))

    # Example 2a: Invalid HED string (junk in last tag)
    hed_string_2 = 'Event/Category/Participant response,'  \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger),' \
                   'dskfjkf/dskjdfkj/sdkjdsfkjdf/sdlfdjdsjklj'
    hed_input_reader = HedValidator(hed_string_2)
    print(hed_input_reader.get_printable_issue_string('[Example 2a] hed_string_2 has junk in the last tag'))

    # Example 2b: However HED string of Example 2 has valid syntax so syntactic validation works
    hed_input_reader = HedValidator(hed_string_2, run_semantic_validation=False)
    print(hed_input_reader.get_printable_issue_string('[Example 2b] hed_string_2 is syntactically correct'))

    # Example 3a: Invalid HED string
    hed_string_3 = 'Event/Description/The start of increasing the size of sector, Event/Label/Sector start, ' \
                   'Event/Category/Experimental stimulus/Instruction/Attend, ' \
                   '(Item/2D shape/Sector, Attribute/Visual/Color/Red) ' \
                   '(Item/2D shape/Ellipse/Circle, Attribute/Visual/Color / Red), Sensory presentation/Visual, ' \
                   'Participant/Efffectt/Visual, Participant/Effect/Cognitive/Target'
    hed_input_reader = HedValidator(hed_string_3)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 3a] hed_string_3 has missing comma so fails before Efffectt typo'))

    # Example 3b: Using issue list directly - issues are returned as a list of dictionaries
    issues = hed_input_reader.get_validation_issues()
    print('[Example 3b] hed_string_3 has ', len(issues), ' issues\n')

    # Example 4a: Example using the ~ notation
    hed_string_4 = 'Event/Label/ButtonDeny, Event/Description/Button push to deny access to the ID holder, ' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger), ' \
                   '(Participant ~ Action/Deny/Access ~ Item/Object/Person/IDHolder)'
    hed_input_reader = HedValidator(hed_string_4, hed_xml_file=local_hed_file)
    print(hed_input_reader.get_printable_issue_string(
        '[Example 4a] the ~ notation in hed_string_4 works in v7.1.1'))
