""" The valid operations for the remodeling tools. """

from hed.tools.remodeling.operations.factor_column_op import FactorColumnOp
from hed.tools.remodeling.operations.factor_hed_tags_op import FactorHedTagsOp
from hed.tools.remodeling.operations.factor_hed_type_op import FactorHedTypeOp
from hed.tools.remodeling.operations.merge_consecutive_op import MergeConsecutiveOp
from hed.tools.remodeling.operations.number_rows_op import NumberRowsOp
from hed.tools.remodeling.operations.number_groups_op import NumberGroupsOp
from hed.tools.remodeling.operations.remove_columns_op import RemoveColumnsOp
from hed.tools.remodeling.operations.reorder_columns_op import ReorderColumnsOp
from hed.tools.remodeling.operations.remap_columns_op import RemapColumnsOp
from hed.tools.remodeling.operations.remove_rows_op import RemoveRowsOp
from hed.tools.remodeling.operations.rename_columns_op import RenameColumnsOp
from hed.tools.remodeling.operations.split_rows_op import SplitRowsOp
from hed.tools.remodeling.operations.summarize_column_names_op import SummarizeColumnNamesOp
from hed.tools.remodeling.operations.summarize_column_values_op import SummarizeColumnValuesOp
from hed.tools.remodeling.operations.summarize_definitions_op import SummarizeDefinitionsOp
from hed.tools.remodeling.operations.summarize_sidecar_from_events_op import SummarizeSidecarFromEventsOp
from hed.tools.remodeling.operations.summarize_hed_type_op import SummarizeHedTypeOp
from hed.tools.remodeling.operations.summarize_hed_tags_op import SummarizeHedTagsOp
from hed.tools.remodeling.operations.summarize_hed_validation_op import SummarizeHedValidationOp

valid_operations = {
    # 'convert_columns': ConvertColumnsOp,
    'factor_column': FactorColumnOp,
    'factor_hed_tags': FactorHedTagsOp,
    'factor_hed_type': FactorHedTypeOp,
    'merge_consecutive': MergeConsecutiveOp,
    'number_groups': NumberGroupsOp,
    'number_rows': NumberRowsOp,
    'remap_columns': RemapColumnsOp,
    'remove_columns': RemoveColumnsOp,
    'remove_rows': RemoveRowsOp,
    'rename_columns': RenameColumnsOp,
    'reorder_columns': ReorderColumnsOp,
    'split_rows': SplitRowsOp,
    'summarize_column_names': SummarizeColumnNamesOp,
    'summarize_column_values': SummarizeColumnValuesOp,
    'summarize_definitions': SummarizeDefinitionsOp,
    'summarize_hed_tags': SummarizeHedTagsOp,
    'summarize_hed_type': SummarizeHedTypeOp,
    'summarize_hed_validation': SummarizeHedValidationOp,
    'summarize_sidecar_from_events': SummarizeSidecarFromEventsOp
}
