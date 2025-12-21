Errors
======

Error handling and reporting classes for HED validation and processing.

Error types and constants
-------------------------

HedExceptions
~~~~~~~~~~~~~

.. autoclass:: hed.errors.exceptions.HedExceptions
   :members:
   :undoc-members:
   :show-inheritance:

HedFileError
~~~~~~~~~~~~

.. autoclass:: hed.errors.exceptions.HedFileError
   :members:
   :undoc-members:
   :show-inheritance:

Error reporting
---------------

ErrorHandler
~~~~~~~~~~~~

.. autoclass:: hed.errors.error_reporter.ErrorHandler
   :members:
   :undoc-members:
   :show-inheritance:

Error functions
~~~~~~~~~~~~~~~

.. autofunction:: hed.errors.error_reporter.get_printable_issue_string

.. autofunction:: hed.errors.error_reporter.sort_issues

.. autofunction:: hed.errors.error_reporter.replace_tag_references

Error types
-----------

ValidationErrors
~~~~~~~~~~~~~~~~

.. autoclass:: hed.errors.error_types.ValidationErrors
   :members:
   :undoc-members:
   :show-inheritance:

SchemaErrors
~~~~~~~~~~~~

.. autoclass:: hed.errors.error_types.SchemaErrors
   :members:
   :undoc-members:
   :show-inheritance:

SidecarErrors
~~~~~~~~~~~~~

.. autoclass:: hed.errors.error_types.SidecarErrors
   :members:
   :undoc-members:
   :show-inheritance:

ErrorContext
~~~~~~~~~~~~

.. autoclass:: hed.errors.error_types.ErrorContext
   :members:
   :undoc-members:
   :show-inheritance:

ErrorSeverity
~~~~~~~~~~~~~

.. autoclass:: hed.errors.error_types.ErrorSeverity
   :members:
   :undoc-members:
   :show-inheritance:
