from hed.validator.hed_input_reader import HedInputReader


def print_issues(title, issues):
    if not issues:
        output_string = title + ": []"
    elif isinstance(issues, str):
        output_string = title  + ":" + issues
    else:
        output_string = title + ":"
        for el in issues:
            output_string = output_string + "\n" + el

    print(output_string)


if __name__ == '__main__':
    # Example 1: Valid HED string for HED <= v7.1.1
    hed_string_1 = 'Event/Label/ButtonPuskDeny, Event/Description/Button push to deny access to the ID holder,' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger)'
    hed_input_reader = HedInputReader(hed_string_1)
    x = hed_input_reader.get_validation_issues()
    #print_issues('Example 1 should have no issues', hed_input_reader.get_validation_issues())

    # Example 2: Invalid HED string (junk in last tag)
    hed_string_2 = 'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger),' \
                   'dskfjkf/dskjdfkj/sdkjdsfkjdf/sdlfdjdsjklj'

    hed_input_reader = HedInputReader(hed_string_2)
    y = hed_input_reader.get_validation_issues()
    #print_issues('Example 2 has junk in the last tag', hed_input_reader.get_validation_issues())

    # Example 3: However HED string of example 2 has valid syntax
    hed_input_reader = HedInputReader(hed_string_2, run_semantic_validation = False)
    z = hed_input_reader.get_validation_issues()
    #print_issues('Example 2 is syntactically correct', hed_input_reader.get_validation_issues())

    # Example 4: Invalid HED string
    hed_string_4 = 'Event/Description/The start of increasing the size of sector, Event/Label/Sector start, ' \
    'Event/Category/Experimental stimulus/Instruction/Attend, (Item/2D shape/Sector, Attribute/Visual/Color/Red) ' \
    '(Item/2D shape/Ellipse/Circle, Attribute/Visual/Color / Red), Sensory presentation/Visual, ' \
    'Participant/Efffectt/Visual, Participant/Effect/Cognitive/Target'
    hed_input_reader = HedInputReader(hed_string_4)
    w = hed_input_reader.get_validation_issues()
    print("We're done")
    #print_issues('Example 4 has a missing comma so fails before Efffectt typo', hed_input_reader.get_validation_issues())