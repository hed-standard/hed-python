HED API reference
========================

.. currentmodule:: hed

.. _base_ref:


HED models
----------------

.. autosummary:: hed.models
   :toctree: generated/

   hed.models.BaseInput
   hed.models.ColumnMapper
   hed.models.ColumnMetadata
   hed.models.DefinitionDict
   hed.models.DefinitionEntry
   hed.models.DefMapper
   hed.models.HedGroup
   hed.models.HedGroupBase
   hed.models.HedGroupFrozen
   hed.models.HedOps
   hed.models.HedString
   hed.models.HedStringGroup
   hed.models.HedTag
   hed.models.OnsetMapper
   hed.models.Sidecar
   hed.models.SpreadsheetInput
   hed.models.TabularInput

.. currentmodule:: hed

.. _calibration_ref1:


HED schema handling
--------------------

.. autosummary:: hed.schema
   :toctree: generated/

   hed.schema.HedSchema
   hed.schema.HedSchemaEntry
   hed.schema.UnitClassEntry
   hed.schema.UnitEntry
   hed.schema.HedTagEntry
   hed.schema.HedSchemaGroup
   hed.schema.HedSchemaSection
   hed.schema.hed_cache
   hed.schema.hed_schema_io
   hed.schema.schema_compliance
   hed.schema.schema_validation_util


.. currentmodule:: hed.tools

.. _calibration_ref2:


HED tools
----------

.. autosummary:: hed.tools.analysis
   :toctree: generated/

   hed.tools.analysis.file_dictionary
   hed.tools.analysis.hed_context_manager
   hed.tools.analysis.hed_definition_manager
   hed.tools.analysis.hed_type_factors
   hed.tools.analysis.hed_type_variable
   hed.tools.analysis.hed_variable_manager
   hed.tools.analysis.hed_variable_summary
   hed.tools.analysis.key_map
   hed.tools.analysis.tabular_summary
   hed.tools.analysis.tag_summary
   hed.tools.analysis.analysis_util
   hed.tools.analysis.annotation_util
   hed.tools.analysis.summary_util


.. currentmodule:: hed

.. _calibration_ref3:


HED tools bids
---------------

.. autosummary:: hed.tools.bids
   :toctree: generated/

   hed.tools.bids.bids_dataset
   hed.tools.bids.bids_dataset_summary
   hed.tools.bids.bids_file
   hed.tools.bids.bids_file_dictionary
   hed.tools.bids.bids_file_group
   hed.tools.bids.bids_sidecar_file
   hed.tools.bids.bids_tabular_dictionary
   hed.tools.bids.bids_tabular_file

.. currentmodule:: hed

.. _calibration_ref4:


HED remodel
---------------

.. autosummary:: hed.tools.remodeling
   :toctree: generated/

   hed.tools.remodeling.BackupManager
   hed.tools.remodeling.Dispatcher
   hed.tools.remodeling.operations.BaseContext
   hed.tools.remodeling.operations.BaseOp
   hed.tools.remodeling.operations.FactorColumnOp
   hed.tools.remodeling.operations.FactorHedTagsOp
   hed.tools.remodeling.operations.FactorHedTypeOp



.. currentmodule:: hed

.. _calibration_ref5:


HED validators
---------------

.. autosummary:: hed.validator
   :toctree: generated/

   hed.validator.HedValidator
   hed.validator.TagValidator
   hed.validator.tag_validator_util

.. currentmodule:: hed
