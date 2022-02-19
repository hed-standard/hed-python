# HEDTools - Python
HED (Hierarchical Event Descriptors) is a framework for systematically describing
both laboratory and real-world events.
HED tags are comma-separated path strings.
 
The goal of HED is to describe precisely the nature of the events of interest
occurring in an experiment using a common language.
HED, itself, is platform-independent, extendable, and data-neutral. 

This repository contains the underlying python tools that support validation,
summarization, and analysis of datasets using HED tags.
Most people will simply annotate their events by creating a spreadsheet
or a BIDS JSON sidecar that associates HED tags with event codes or the events themselves.
If you have such a spreadsheet or a JSON, 
you can use the HED Online Validator currently available at 
[https://hedtools.ucsd.edu/hed](https://hedtools.ucsd.edu/hed) to validate or transform
your files without downloading any tools.

### Installation
Use `pip` to install `hedtool` from the 
[GitHub](https://github.com/hed-standard/hed-python) repository,
since the `hedtools` in this repository are not yet available on PyPI:

   ```
       pip install git+https://github.com/hed-standard/hed-python/@master
   ```

The HEDTools in this repository require python 3.7 or greater.

### Support for earlier versions of HED (HED-2G)

**Note:** As of January 1, 2022, the `hed-python` repository will no longer support HED-2G. 
The existing support continues to be available in the `hed2-python` repository.
An on online version of the tools in this repository are available at 
[https://hedtools.ucsd.edu/hed2](https://hedtools.ucsd.edu/hed2)


### Other links of interest

HED specification documentation: [https://hed-specification.readthedocs.io/en/latest/](https://hed-specification.readthedocs.io/en/latest/)

Documentation: [https://hed-python.readthedocs.io/en/latest/](https://hed-python.readthedocs.io/en/latest/)

Code climate reports: [https://codeclimate.com/github/hed-standard/hed-python](https://codeclimate.com/github/hed-standard/hed-python)