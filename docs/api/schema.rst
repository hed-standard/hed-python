Schema
======

HED schema management and validation tools.

Core schema classes
-------------------

HedSchema
~~~~~~~~~

.. autoclass:: hed.schema.hed_schema.HedSchema
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaEntry
~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_entry.HedSchemaEntry
   :members:
   :undoc-members:
   :show-inheritance:

HedTagEntry
~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_entry.HedTagEntry
   :members:
   :undoc-members:
   :show-inheritance:

UnitClassEntry
~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_entry.UnitClassEntry
   :members:
   :undoc-members:
   :show-inheritance:

UnitEntry
~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_entry.UnitEntry
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaGroup
~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_group.HedSchemaGroup
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaSection
~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_section.HedSchemaSection
   :members:
   :undoc-members:
   :show-inheritance:

Schema IO and caching
---------------------

Schema loading functions
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: hed.schema.hed_schema_io
   :members: load_schema, load_schema_version, from_string, get_hed_xml_version, from_dataframes
   :undoc-members:

Cache management
~~~~~~~~~~~~~~~~

.. automodule:: hed.schema.hed_cache
   :members: cache_xml_versions, get_hed_versions, set_cache_directory, get_cache_directory
   :undoc-members:

Schema constants
----------------

HedKey
~~~~~~

.. autoclass:: hed.schema.hed_schema_constants.HedKey
   :members:
   :undoc-members:
   :show-inheritance:

HedSectionKey
~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_constants.HedSectionKey
   :members:
   :undoc-members:
   :show-inheritance:
