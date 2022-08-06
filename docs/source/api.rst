HED API reference
========================

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
---------

.. autosummary:: hed.tools
   :toctree: generated/

   hed.tools.bids.bids_dataset.BidsDataset
   hed.tools.bids.bids_dataset_summary.BidsDatasetSummary
   hed.tools.bids.bids_file.BidsFile
   hed.tools.bids.bids_file_dictionary.BidsFileDictionary
   hed.tools.bids.bids_file_group.BidsFileGroup
   hed.tools.bids.bids_sidecar_file.BidsSidecarFile
   hed.tools.bids.bids_tabular_dictionary.BidsTabularDictionary
   hed.tools.bids.bids_tabular_file.BidsTabularFile
   hed.tools.bids.bids_tabular_summary.BidsTabularSummary
   hed.tools.analysis.definition_manager.DefinitionManager
   hed.tools.analysis.file_dictionary.FileDictionary
   hed.tools.analysis.key_map.KeyMap
   hed.tools.analysis.context_manager.ContextManager
   hed.tools.analysis.tag_summary.TagSummary
   hed.tools.analysis.hed_type_factors.HedTypeFactors
   hed.tools.analysis.hed_type_variable.HedTypeVariable
   hed.tools.analysis.hed_variable_manager.HedVariableManager
   hed.tools.analysis.hed_variable_summary.HedVariableCounts
   hed.tools.analysis.hed_variable_summary.HedVariableSummary
   hed.tools.analysis.analysis_util
   hed.tools.analysis.annotation_util
   hed.tools.analysis.summary_util
   hed.tools.hed_logger.HedLogger

.. currentmodule:: hed


HED utilities
-------------

.. autosummary:: hed.util
   :toctree: generated/

   hed.util.data_util
   hed.util.io_util

.. currentmodule:: hed


HED validators
--------------

.. autosummary:: hed.validator
   :toctree: generated/

   hed.validator.HedValidator
   hed.validator.TagValidator
   hed.validator.tag_validator_util

.. currentmodule:: hed
