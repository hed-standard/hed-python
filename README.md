[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8056010.svg)](https://doi.org/10.5281/zenodo.8056010)
[![Maintainability](https://qlty.sh/gh/hed-standard/projects/hed-python/maintainability.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python)
[![Code Coverage](https://qlty.sh/gh/hed-standard/projects/hed-python/coverage.svg)](https://qlty.sh/gh/hed-standard/projects/hed-python)
![Python3](https://img.shields.io/badge/python->=3.9-yellow.svg)
![PyPI - Status](https://img.shields.io/pypi/v/hedtools)
[![Documentation](https://img.shields.io/badge/docs-hedtags.org-blue.svg)](https://www.hedtags.org/hed-python)

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
[https://hedtools.org](https://hedtools.org) to validate or transform
your files without downloading any tools. 

A version of the online tools corresponding to the `develop` branch can be found at:
[https://hedtools.org/hed_dev](https://hedtools.org/hed_dev).

### Installation
Use `pip` to install `hedtools` from PyPI:

   ```
       pip install hedtools
   ```

To install directly from the 
[GitHub](https://github.com/hed-standard/hed-python) repository `main` branch:

   ```
       pip install git+https://github.com/hed-standard/hed-python/@main
   ```

The HEDTools in this repository require Python 3.8 or greater.

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

#### Develop versus main versus stable branches

The `hed-python` repository

| Branch  |  Meaning | Synchronized with |
|---------| -------- | ------------------ |
| stable  | Officially released on PyPI as a tagged version. | `stable@hed-web`<br/>`stable@hed-specification`<br/>`stable@hed-examples` |
| main    | Most recent usable version. | `latest@hed-web`<br/>`latest@hed-specification`<br/>`latest@hed-examples` |

#### To contribute

Contributions are welcome.
Please use the [Github issues](https://github.com/hed-standard/hed-python/issues)
for suggestions or bug reports.
The [Github pull request](https://github.com/hed-standard/hed-python/pulls)
may also be used for contributions.
These PRs should be made to the `main` branch but should have a branch name other than `main`.

#### Local Settings Storage
Cached Schemas by default are stored in "home/.hedtools/" 
Location of "home" directory varies by OS.

Use `hed.schema.set_cache_directory` to change the location.
The HED cache can be shared across processes.

Starting with `hedtools 0.2.0` local copies of the most recent schema versions
are stored within the code modules for easy access.  

### Building the docs locally

You can build the documentation locally by executing the following commands in the hed-python repository root directory:

```bash
# Build the documentation
mkdocs build

# Serve locally with live reload
mkdocs serve
```
The API documentation can be viewed at [ http://localhost:8000]( http://localhost:8000).
