Schema
======================

HED schema management and validation tools.

Core schema classes
-------------------

HedSchemaBase
~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_base.HedSchemaBase
   :members:
   :undoc-members:
   :show-inheritance:

HedSchema
~~~~~~~~~

.. autoclass:: hed.schema.hed_schema.HedSchema
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaGroup
~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_group.HedSchemaGroup
   :members:
   :undoc-members:
   :show-inheritance:

Schema entry classes
--------------------

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

Schema section classes
----------------------

HedSchemaSection
~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_section.HedSchemaSection
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaUnitSection
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_section.HedSchemaUnitSection
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaUnitClassSection
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_section.HedSchemaUnitClassSection
   :members:
   :undoc-members:
   :show-inheritance:

HedSchemaTagSection
~~~~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_section.HedSchemaTagSection
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

Schema loader base class
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.schema_io.base2schema.SchemaLoader
   :members:
   :undoc-members:
   :show-inheritance:

Schema serializers
~~~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.schema_io.schema2df.Schema2DF
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: hed.schema.schema_io.schema2wiki.Schema2Wiki
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: hed.schema.schema_io.schema2xml.Schema2XML
   :members:
   :undoc-members:
   :show-inheritance:

Schema comparison
-----------------

SchemaComparer
~~~~~~~~~~~~~~

.. autoclass:: hed.schema.schema_comparer.SchemaComparer
   :members:
   :undoc-members:
   :show-inheritance:

Comparison utilities
~~~~~~~~~~~~~~~~~~~~

.. automodule:: hed.schema.schema_comparer
   :members: compare_schemas, gather_schema_changes, pretty_print_change_dict, compare_differences
   :undoc-members:

Schema validation
-----------------

Compliance checking
~~~~~~~~~~~~~~~~~~~

.. autofunction:: hed.schema.schema_validation.compliance.check_compliance

.. autoclass:: hed.schema.schema_validation.compliance.SchemaValidator
   :members:
   :undoc-members:
   :show-inheritance:

Compliance summary
~~~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.schema_validation.compliance_summary.ComplianceSummary
   :members:
   :undoc-members:
   :show-inheritance:

HED ID validator
~~~~~~~~~~~~~~~~

.. autoclass:: hed.schema.schema_validation.hed_id_validator.HedIDValidator
   :members:
   :undoc-members:
   :show-inheritance:

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

HedKeyOld
~~~~~~~~~

.. autoclass:: hed.schema.hed_schema_constants.HedKeyOld
   :members:
   :undoc-members:
   :show-inheritance:
