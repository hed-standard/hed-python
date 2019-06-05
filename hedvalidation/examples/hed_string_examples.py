from hedvalidation.hed_input_reader import HedInputReader

if __name__ == '__main__':
    # Example 1: Valid HED string
    hed_string_1 = 'Event/Label/ButtonPuskDeny, Event/Description/Button push to deny access to the ID holder,' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger)';
    hed_input_reader = HedInputReader(hed_string_1);
    print('HED string 1 abc issues:\n' + hed_input_reader.get_validation_issues());

    # Example 2: Invalid HED string
    hed_string_2 = 'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger),' \
                   'dskfjkf/dskjdfkj/sdkjdsfkjdf/sdlfdjdsjklj';

    hed_input_reader = HedInputReader(hed_string_2);
    print('HED string 2 abc issues:\n' + hed_input_reader.get_validation_issues());

    # Example 3: Invalid HED string
    hed_string_3 = 'Event/Description/The start of increasing the size of sector, Event/Label/Sector start, ' \
    'Event/Category/Experimental stimulus/Instruction/Attend, (Item/2D shape/Sector, Attribute/Visual/Color/Red) f' \
    '(Item/2D shape/Ellipse/Circle, Attribute/Visual/Color / Red), Sensory presentation/Visual, ' \
    'Participant/Efffectt/Visual, Participant/Effect/Cognitive/Target';
    hed_input_reader = HedInputReader(hed_string_3);
    print('HED string 3 abc issues:\n' + hed_input_reader.get_validation_issues());