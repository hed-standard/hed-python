import os.path
from hed.validator.hed_validator import HedValidator
from hed.util.error_reporter import get_printable_issue_string


if __name__ == '__main__':

    dir_path = os.path.dirname(os.path.realpath(__file__))
    local_hed_file1 = os.path.join(dir_path, 'data/HED7.1.2.xml')
    local_hed_file2 = os.path.join(dir_path, 'data/HED8.0.0-alpha.1.xml')

    hed_validator_current = HedValidator(hed_xml_file=local_hed_file2)

    # Example 1a: Valid HED string for HED <= v7.1.1
    hed_string_1 = 'Event/Label/ButtonPuskDeny, Event/Description/Button push to deny access to the ID holder,' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger)'

    validation_issues = hed_validator_current.validate_input(hed_string_1)
    print(get_printable_issue_string(validation_issues, title='[Example 1b] hed_string_1 has issues with the latest HED version'))

    hed_list = [hed_string_1, hed_string_1]

    validation_issues = hed_validator_current.validate_input(hed_list)
    print(get_printable_issue_string(validation_issues,
                                                  title='[Example 1b] hed_string_1 has issues with the latest HED version'))
