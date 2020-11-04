# hedvalidation
Python project to implement validation of HED (Hierarchical Event Descriptors). 

### What is HED?
HED (Hierarchical Event Descriptors) is a semi-structured vocabulary and
framework for annotating events in a machine-friendly and uniform way. The HED
framework is being developed and maintained by the
[hed-standard organization](https://github.com/hed-standard).  

For more information on HED visit: <https://github.com/hed-standard/hed-specification> or
[hedtags.org](http://hedtags.org) for an html schema viewer.

### What does it do?
The HED validator python module, hed.validator, contains code to validate HED tags presented
in either string form or as spreadsheets.  See the examples directory for code examples of
how to call the validator in either form.

### HED online validator
Most people who just want to validate HED tags in their data will prefer to use the
[HED online validator](http://visual.cs.utsa.edu/hed).

### HED in MATLAB and with EEGLAB
HED tagging is integrated into [EEGLAB](https://sccn.ucsd.edu/eeglab/index.php) as a plugin.
HED tagging support using a graphical user interface with integrated validation is available at
<https://github.com/hed-standard/hed-matlab>.

### HED validating in Python
You can also incorporate HED validation into your own Python tools or validate HED strings or tagged
files using Python: 

> `examples/hed_string_examples.py` illsutrates how to call the HED validator on HED tag strings.  

> `examples/hed_files_examples.py` illustrates how to call the HED validator on spreadsheets of tags.




# hedschema

hedschema is a Python 3 package that converts representations of the HED specification to
different representations. 

### What is HED?
HED (Hierarchical Event Descriptors) is a structured vocabulary and framework for annotating
events in data in a standardized, algorithm friendly manner. 

For the HED schema please visit: <https://github.com/hed-standard/hed-specification>

### Dependencies
* [Python 3](https://www.python.org/downloads/)
