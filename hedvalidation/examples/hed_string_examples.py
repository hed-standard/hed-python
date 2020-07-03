"""
Examples of HED validation of a tag string
"""


from hed.validator.hed_input_reader import HedInputReader

if __name__ == '__main__':
    local_hed_file = '../tests/data/HED.xml'   # path HED v7.1.1 stored locally

    # Example 1: Valid HED string for HED <= v7.1.1
    hed_string_1 = 'Event/Label/ButtonPuskDeny, Event/Description/Button push to deny access to the ID holder,' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger)'
    hed_input_reader = HedInputReader(hed_string_1, hed_xml_file=local_hed_file)
    print(hed_input_reader.get_printable_issue_string('Example 1 should have no issues with HEDv7.1.1'))

    # Example 1a: Try with the latest version of HED.xml
    hed_input_reader = HedInputReader(hed_string_1)
    print(hed_input_reader.get_printable_issue_string('Example 1 issues with the latest HED version'))

    # Example 2: Invalid HED string (junk in last tag)
    hed_string_2 = 'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger),' \
                   'dskfjkf/dskjdfkj/sdkjdsfkjdf/sdlfdjdsjklj'
    hed_input_reader = HedInputReader(hed_string_2)
    print(hed_input_reader.get_printable_issue_string('Example 2 has junk in the last tag'))

    # Example 2a: However HED string of Example 2 has valid syntax so syntactic validation works
    hed_input_reader = HedInputReader(hed_string_2, run_semantic_validation=False)
    print(hed_input_reader.get_printable_issue_string('Example 2 is syntactically correct'))

    # Example 3: Invalid HED string
    hed_string_3 = 'Event/Description/The start of increasing the size of sector, Event/Label/Sector start, ' \
                   'Event/Category/Experimental stimulus/Instruction/Attend, ' \
                   '(Item/2D shape/Sector, Attribute/Visual/Color/Red) ' \
                   '(Item/2D shape/Ellipse/Circle, Attribute/Visual/Color / Red), Sensory presentation/Visual, ' \
                   'Participant/Efffectt/Visual, Participant/Effect/Cognitive/Target'
    hed_input_reader = HedInputReader(hed_string_3)
    print(hed_input_reader.get_printable_issue_string('Example 3 has missing comma so fails before Efffectt typo'))

    # Example 3a: Using issue list directly - issues are returned as a list of dictionaries
    issues = hed_input_reader.get_validation_issues()
    print('hed_string_4 has ', len(issues), ' issues\n')

    # Example 4: Example using the ~ notation
    hed_string_4 = 'Event/Label/ButtonDeny, Event/Description/Button push to deny access to the ID holder, ' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger), ' \
                   '(Participant ~ Action/Deny/Access ~ Item/Object/Person/IDHolder)'
    hed_input_reader = HedInputReader(hed_string_4, hed_xml_file=local_hed_file)
    print(hed_input_reader.get_printable_issue_string('Example 4 the ~ notation works in v7.1.1'))
