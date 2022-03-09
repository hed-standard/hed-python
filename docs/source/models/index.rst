.. _reports:

=====================================================
HED data models
=====================================================

.. contents:: **Contents**
    :local:
    :depth: 1

|

.. currentmodule:: hed.models

.. _loading_datasets:

HED datasets
===========================================

**This section is a placeholder and will be updated soon.**

The :obj:`hed.models.BaseInput` class requires the path to a valid BIDS dataset::

    >>> from os.path import join
    >>> from bids import BIDSLayout
    >>> from bids.tests import get_test_data_path
    >>> layout = BIDSLayout(join(get_test_data_path(), 'synthetic'))

The ``BaseInput`` instance is a lightweight container for all of the files in the
BIDS project directory. It automatically detects any BIDS entities found in the
file paths, and allows us to perform simple but relatively powerful queries over
the file tree. By default, defined BIDS entities include things like "subject",
"session", "run", and "type".

.. _querying_datasets:

Querying datasets
===========================================

**Coming***