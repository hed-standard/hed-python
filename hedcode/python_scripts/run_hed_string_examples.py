"""
TODO: Examples need to be updated to current HED version
Examples of creating a HedValidator and validating various Hed Strings with it.

Classes Demonstrated:
HedValidator - Validates a given input string or file
"""

from hed.errors.error_reporter import get_printable_issue_string
from hed.models.hed_string import HedString
from hed.schema.hed_schema_file import load_schema, load_schema_version
from hed.validator.hed_validator import HedValidator


if __name__ == '__main__':
    # Create three versions of the HedValidator based on different schema
    local_hed_file_old = '../data/schema_data/HED7.2.0.xml'  # path HED v7.2.0 stored locally
    hed_schema_old = load_schema(local_hed_file_old)
    hed_validator_old = HedValidator(hed_schema_old)
    hed_schema_current = load_schema_version()
    hed_validator_current = HedValidator(hed_schema_current)
    hed_validator_no_semantic = HedValidator(run_semantic_validation=False)

    hed_string_1 = \
        "Sensory-event,Visual-presentation,Experimental-stimulus,Green,Non-target," + \
        "(Letter/D, (Center-of, Computer-screen))"
    string_obj_1 = HedString(hed_string_1)
    validation_issues = string_obj_1.validate(hed_validator_current)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 1] hed_string_1 should have no issues with HEDv8.0.0'))

    string_1_long_obj = string_obj_1.convert_to_short(hed_schema_current)
    validation_issues = string_obj_1.validate(hed_validator_current)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 2] hed_string_1 should validate after conversion to long'))

    validation_issues = string_obj_1.validate(hed_validator_old)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 3] hed_string_1 should not validate with HEDv7.2.0'))

    hed_string_2 = "Sensory-event,Visual-presentation,BlankBlank,Experimental-stimulus,Blech"
    string_obj_2 = HedString(hed_string_2)
    validation_issues = string_obj_2.validate(hed_validator_current)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 4] hed_string_2 has 2 invalid tags HEDv8.0.0'))

    hed_string_3 = "Sensory-event,Visual-presentation,Experimental-stimulus,Red/Dog"
    string_obj_3 = HedString(hed_string_3)
    validation_issues = string_obj_3.validate(hed_validator_current)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 5] hed_string_3 extended tag does not flag error unless warnings'))

    validation_issues = string_obj_3.validate(hed_validator_current, check_for_warnings=True)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 6] hed_string_3 extended tag flags error with warnings'))

    hed_string_4 = 'Event/Label/ButtonPushDeny, Event/Description/Button push to deny access to the ID holder,' \
                   'Event/Category/Participant response, ' \
                   '(Participant ~ Action/Button press/Keyboard ~ Participant/Effect/Body part/Arm/Hand/Finger)'
    string_obj_4 = HedString(hed_string_4)
    validation_issues = string_obj_4.validate(hed_validator_current)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 7] hed_string_4 has issues with the latest HED version'))

    validation_issues = string_obj_4.validate(hed_validator_old)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 8] hed_string_4 has issues tildes no longer supported'))

    hed_string_5 = 'Event,dskfjkf/dskjdfkj/sdkjdsfkjdf/sdlfdjdsjklj'
    string_obj_5 = HedString(hed_string_5)
    validation_issues = string_obj_5.validate(hed_validator_current)
    print(get_printable_issue_string(validation_issues,
                                     title='[Example 9] hed_string_5 does not validate with current HED schema'))

    validation_issues = string_obj_5.validate(hed_validator_no_semantic)
    print(get_printable_issue_string(validation_issues, title='[Example 10] hed_string_5 is syntactically correct'))
