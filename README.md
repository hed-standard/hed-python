# HEDTools - Python
HED (Hierarchical Event Descriptors) is a framework for systematically describing
both laboratory and real-world events as well as other experimental metadata.
HED tags are comma-separated path strings.
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
Use `pip` to install `hedtools` from PyPI:

   ```
       pip install hedtools
   ```

To install directly from the 
[GitHub](https://github.com/hed-standard/hed-python) repository:

   ```
       pip install git+https://github.com/hed-standard/hed-python/@master
   ```

The HEDTools in this repository require python 3.7 or greater.

### Relationship to other repositories

The `hed-python` repository contains the Python infrastructure for validating
and analyzing HED. This repository has two companion repositories:
- [`hed-web`](https://github.com/hed-standard/hed-web) contains the web interface
for HED as well as a deployable docker module that supports web services for HED.
- [`hed-examples`](https://github.com/hed-standard/hed-examples) contains examples of
using HED in Python and MATLAB.
The site also contains many Jupyter notes illustrating
various aspect of data curation and analysis using HED.
The site hosts HED test datasets and the HED user manuals.

#### Develop versus master branches

Because the three repositories are interrelated, the following conventions are followed.
The latest stable version is on the master branches of `hed-python` and `hed-web` and the
`main` branch of `hed-examples`.
The documentation link on `readthedocs` will describe the stable versions.

As features are integrated, they first appear in the `develop` branches of the
three repositories.
The `develop` branches of the three repositories will be kept in sync.
If an interface change in `hed-python` triggers a change in `hed-web` or `hed-examples`,
every effort will be made to get the stable branches of the respective repositories in
sync.

#### To contribute

Contributions are welcome.
Please use the [Github issues](https://github.com/hed-standard/hed-python/issues)
for suggestions or bug reports.
The [Github pull request](https://github.com/hed-standard/hed-python/pulls)
may also be used for contributions.
Usually these updates should be made to the `develop` branch, not the `master`.


### Other links of interest

HED specification documentation: [https://hed-specification.readthedocs.io/en/latest/](https://hed-specification.readthedocs.io/en/latest/).

Examples: [https://hed-examples.readthedocs.io/en/latest/](https://hed-examples.readthedocs.io/en/latest/).

Documentation: [https://hed-python.readthedocs.io/en/latest/](https://hed-python.readthedocs.io/en/latest/).

Code climate reports: [https://codeclimate.com/github/hed-standard/hed-python](https://codeclimate.com/github/hed-standard/hed-python).
