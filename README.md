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

A version of the online tools corresponding to the `develop` branch can be found at:
[https://hedtools.ucsd.edu/hed_dev](https://hedtools.ucsd.edu/hed_dev).

### Installation
Use `pip` to install `hedtools` from PyPI:

   ```
       pip install hedtools
   ```

To install directly from the 
[GitHub](https://github.com/hed-standard/hed-python) repository `master` branch:

   ```
       pip install git+https://github.com/hed-standard/hed-python/@master
   ```

The HEDTools in this repository require Python 3.7 or greater.
**Note:** HED is continuing to support Python 3.7 until 2023, because
it is needed for MATLAB versions R2019a through R2020a.

**Note:** The final exported interface for Python tools has not been 
completely frozen in 0.1.0 and is expected to undergo minor changes
in interface until the release of version 1.0.0.

### Relationship to other repositories

The `hed-python` repository contains the Python infrastructure for validating
and analyzing HED. This repository has several companion repositories:
- [`hed-web`](https://github.com/hed-standard/hed-web) contains the web interface
for HED as well as a deployable docker module that supports web services for HED.  
- [`hed-examples`](https://github.com/hed-standard/hed-examples) contains examples of
using HED in Python and MATLAB. This repository also houses the HED resources.
See [https://www.hed-resources.org](https://www.hed-resources.org) for access to these.
- [`hed-specification`](https://github.com/hed-standard/hed-specification) contains
the HED specification documents. The `hed-python` validator is keyed to error codes
in this document.
- [`hed-schemas`](https://github.com/hed-standard/hed-schemas) contains
the official HED schemas. The tools access this repository to retrieve and cache schema versions
during execution. Starting with `hedtools 0.2.0` local copies of the most recent schema versions
are stored within the code modules for easy access.

#### Develop versus master versus stable branches

The `hed-python` repository

| Branch |  Meaning | Synchronized with |
| ------ | -------- | ------------------ |
| stable | Officially released on PyPI as a tagged version. | `stable@hed-web`<br/>`stable@hed-specification`<br/>`stable@hed-examples` |
| latest | Most recent usable version. | `latest@hed-web`<br/>`latest@hed-specification`<br/>`latest@hed-examples` |
| develop | Experimental and evolving. | `develop@hed-web`<br/>`develop@hed-specification`<br/>`develop@hed-examples` |

As features are integrated, they first appear in the `develop` branches of the
repositories.
The `develop` branches of the repositories will be kept in sync as much as possible
If an interface change in `hed-python` triggers a change in `hed-web` or `hed-examples`,
every effort will be made to get the three types of branches
(`develop`, `latest`, `stable`) of the respective repositories in
sync.

API documentation is generated on ReadTheDocs when a new version is
pushed on any of the three branches. For example, the API documentation for the
`latest` branch can be found on [hed-python.readthedocs.io/en/latest/](hed-python.readthedocs.io/en/latest/).

#### To contribute

Contributions are welcome.
Please use the [Github issues](https://github.com/hed-standard/hed-python/issues)
for suggestions or bug reports.
The [Github pull request](https://github.com/hed-standard/hed-python/pulls)
may also be used for contributions.
These PRs should be made to the `develop` branch, not the `master` branch.

#### Local Settings Storage
Cached Schemas by default are stored in "home/.hedtools/" 
Location of "home" directory varies by OS.

Use `hed.schema.set_cache_directory` to change the location.
The HED cache can be shared across processes.

Starting with `hedtools 0.2.0` local copies of the most recent schema versions
are stored within the code modules for easy access.

### Other links of interest

Code climate reports: [https://codeclimate.com/github/hed-standard/hed-python](https://codeclimate.com/github/hed-standard/hed-python).
