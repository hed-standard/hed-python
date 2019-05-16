Python tools used to validate spreadsheet tags against a HED schema. 


### Releases
Version 1.0.0 ????
* Initial release

Version 1.0.1 Released 4/30/19
* Fix issue where the required tag prefix could end up duplicated.  eg: Event/Description/Event/Description

Version 1.0.2 Released 5/10/19
* Fix issues with validating tags parenthesis in them. eg: (Paradigm/Rapid serial object transformation,Paradigm/Reading (Overt))

Version 1.0.3 Released 5/10/19
* Update error message for unmatched parenthesis
* Add error message for invalid characters.  Invalid characters are currently "[]{}"

Version 1.0.4 Released 5/12/19
* Further grouping fix.  Don't fail when two groups end at the same time.  eg: ((Item/ID/Description value,Item/ID/Local)~(Item/ID/Local,Item/Group ID/Description value))

Version 1.0.5 Released 5/16/19
* Fix unit type checking to actually check for units
* Also validate the number when given a unit tag(it was not validated before if a unit name was present)

Version 1.0.6 Released 5/16/19
* Update regular expression that validates unit numbers to check for scientific numbers, not just digits.