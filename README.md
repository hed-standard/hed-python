# HEDTools - Python
HED (Hierarchical Event Descriptors) is a framework for systematically describing both laboratory
 and real-world events. HED tags are comma-separated path strings. 
 
The goal of HED is to describe precisely the nature of the events of interest occurring in an 
experiment using a common language. HED, itself, is platform-independent and data-neutral. 

Most people will simply annotate their events by creating a spreadsheet that associates 
HED tags with event codes or the events themselves. If you have such a spreadsheet, 
you can use the HED Online Validator currently available at 
[https://hedtools.ucsd.edu/hed](https://hedtools.ucsd.edu/hed) to validate or transform
your files without downloading any tools.

### Python subprojects
 - hedtools        contains all of the validation and translation tools for HED tags and HED schema.
 - webtools        contains the code to deploy the validators and other HED tools as a web application running in a docker module.
 
The HEDTools require python 3.7 or greater.

### Support for earlier versions of HED (HED-2G)

**Note:** As of January 1, 2022, the `hed-python` repository will no longer support HED-2G. 
The existing support continues to be available in the `hed2-python` repository. On online 
version of the tools in this repository are available at 
[https://hedtools.ucsd.edu/hed2](https://hedtools.ucsd.edu/hed2)


### Other links of interest

HED specification documentation: [https://hed-specification.readthedocs.io/en/latest/](https://hed-specification.readthedocs.io/en/latest/)

Documentation: [https://hed-python.readthedocs.io/en/latest/](https://hed-python.readthedocs.io/en/latest/)

Code climate reports: [https://codeclimate.com/github/hed-standard/hed-python](https://codeclimate.com/github/hed-standard/hed-python)