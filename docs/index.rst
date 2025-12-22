Python HEDTools
===============


.. sidebar:: Quick links
   
   * `HED homepage <https://www.hedtags.org/>`_ 

   * `HED vocabularies <https://www.hedtags.org/hed-schema-browser>`_

   * `HED online tools <https://hedtools.org/hed/>`_

   * `HED browser tools <https://www.hedtags.org/hed-javascript>`_

   * `HED organization  <https://github.com/hed-standard/>`_  

   * `HED specification <https://www.hedtags.org/hed-specification>`_ 

Welcome to the Python HEDTools documentation! This package provides comprehensive tools for working with **Hierarchical Event Descriptors (HED)** - a standardized framework for annotating events and experimental metadata in neuroscience and beyond.

What is HED?
------------

HED is a standardized vocabulary and annotation framework designed to systematically describe events experimental data, particularly neuroimaging and behavioral data. It's integrated into major neuroimaging standards:

* `BIDS <https://bids.neuroimaging.io/>`_ (Brain Imaging Data Structure)
* `NWB <https://www.nwb.org/>`_ (Neurodata Without Borders)

Key features
------------

* **Validation**: Verify HED annotations against official schemas
* **Analysis**: Search, filter, and summarize HED-annotated data
* **BIDS integration**: Full support for BIDS dataset validation and processing
* **NWB support**: Read and write HED annotations in NWB files using `ndx-hed <https://www.hedtags.org/ndx-hed>`_
* **Multiple formats**: Work with JSON sidecars, TSV files, Excel spreadsheets

Getting started
---------------

.. toctree::
   :maxdepth: 2

   Introduction <introduction>

Programming with HEDTools
-------------------------

.. toctree::
   :maxdepth: 2

   User guide <user_guide>

API documentation
-----------------

.. toctree::
   :maxdepth: 2

   API reference <api/index>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
