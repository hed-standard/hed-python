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
   :maxdepth: 3

   hed.tools.FileDictionary
   hed.tools.HedContextManager
   hed.tools.HedDefinitionManager
   hed.tools.HedQueryManager
   hed.tools.HedTypeFactors
   hed.tools.HedTypeVariable
   hed.tools.HedVariableManager
   hed.tools.HedVariableCounts
   hed.tools.HedVariableSummary
   hed.tools.KeyMap
   hed.tools.TabularSummary
   hed.tools.TagSummary


.. currentmodule:: hed.tools

.. _calibration_ref6:


HED tools bids
---------------

.. autosummary:: hed.tools.bids
   :toctree: generated/
   :maxdepth: 3

   hed.tools.BidsDataset
   hed.tools.BidsDatasetSummary
   hed.tools.BidsFile
   hed.tools.BidsFileDictionary
   hed.tools.BidsFileGroup
   hed.tools.BidsSidecarFile
   hed.tools.BidsTabularDictionary
   hed.tools.BidsTabularFile
   hed.tools.BidsTabularSummary




.. currentmodule:: hed.tools

.. _calibration_ref2:


HED remodel
---------------

.. autosummary:: hed.tools.remodeling
   :toctree: generated/

   hed.tools.BackupManager
   hed.tools.Dispatcher
   hed.tools.BaseContext
   hed.tools.BaseOp
   hed.tools.FactorColumnOp
   hed.tools.FactorHedTagsOp
   hed.tools.FactorHedTypeOp
   hed.tools.analysis_util
   hed.tools.annotation_util
   hed.tools.summary_util


.. currentmodule:: hed

.. _calibration_ref2:


HED validators
---------------

.. autosummary:: hed.validator
   :toctree: generated/

   hed.validator.HedValidator
   hed.validator.TagValidator
   hed.validator.tag_validator_util

.. currentmodule:: hed
