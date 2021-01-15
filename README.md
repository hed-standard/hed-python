# HEDTools - Python
HED (Hierarchical Event Descriptors) is a framework for systematically describing both laboratory and real-world events. HED tags are comma-separated path strings. The goal of HED is to describe precisely the nature of the events of interest occurring in an experiment using a common language. HED, itself, is platform-independent and data-neutral. 

Most people will simply annotate their events by creating a spreadsheet that associates HED tags with event codes or the events themselves. If you have such a spreadsheet, you can use the HED Online Validator currently available at [https://hedtags.ucsd.edu/hed](https://hedtags.ucsd.edu/hed) to validate your spreadsheet without downloading any tools.

### Python modules
 - hedtools        contains all of the validation and translation tools for hed tags and hed schema.
 - hedweb          contains the code to deploy the validators and other HED tools as a web application running in a docker module.
 
The HEDTools require python 3.7 or greater.

### Calling HED tools directly from a python program

The `examples` directory in hedtools gives runnable examples illustrating how to call various HED tools directly from python.
