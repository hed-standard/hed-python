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


.. currentmodule:: hed

.. _calibration_ref2:


HED tools
----------

.. autosummary:: hed.tools.analysis
   :toctree: generated/

   hed.tools.analysis.file_dictionary.FileDictionary
   hed.tools.analysis.hed_context_manager.HedContextManager
   hed.tools.analysis.hed_definition_manager.HedDefinitionManager
   hed.tools.analysis.hed_type_factors.HedTypeFactors
   hed.tools.analysis.hed_type_variable.HedTypeVariable
   hed.tools.analysis.hed_variable_manager.HedVariableManager
   hed.tools.analysis.hed_variable_summary.HedVariableSummary
   hed.tools.analysis.key_map.KeyMap
   hed.tools.analysis.tabular_summary.TabularSummary
   hed.tools.analysis.tag_summary.TagSummary
   hed.tools.analysis.analysis_util
   hed.tools.analysis.annotation_util
   hed.tools.analysis.summary_util


.. currentmodule:: hed

.. _calibration_ref3:


HED tools bids
---------------

.. autosummary:: hed.tools.bids
   :toctree: generated/

   hed.tools.bids.bids_dataset.BidsDataset
   hed.tools.bids.bids_dataset_summary.BidsDatasetSummary
   hed.tools.bids.bids_file.BidsFile
   hed.tools.bids.bids_file_dictionary.BidsFileDictionary
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

   hed.tools.remodeling.backup_manager.BackupManager
   hed.tools.remodeling.dispatcher.Dispatcher
   hed.tools.remodeling.operations.base_context.BaseContext
   hed.tools.remodeling.operations.base_op.BaseOp
   hed.tools.remodeling.operations.factor_column_op.FactorColumnOp
   hed.tools.remodeling.operations.factor_hed_tags_op.FactorHedTagsOp
   hed.tools.remodeling.operations.factor_hed_type_op.FactorHedTypeOp
   hed.tools.remodeling.cli.run_remodel
   hed.tools.remodeling.cli.run_remodel_backup
   hed.tools.remodeling.cli.run_remodel_restore



.. currentmodule:: hed

.. _calibration_ref6:


HED tools util
---------------

.. autosummary:: hed.tools.util
   :toctree: generated/

   hed.tools.util.io_util
   hed.tools.util.data_util
   hed.tools.hed_logger.HedLogger



.. currentmodule:: hed

.. _calibration_ref7:


HED validators
---------------

.. autosummary:: hed.validator
   :toctree: generated/

   hed.validator.HedValidator
   hed.validator.TagValidator
   hed.validator.tag_validator_util

.. currentmodule:: hed
