from hed.models.hed_string import HedString
from hed.models.hed_tag import HedTag
from hed.models.definition_dict import DefinitionDict
from hed.models.model_constants import DefTagNames
from hed.errors.error_types import ValidationErrors, DefinitionErrors
from hed.errors.error_reporter import ErrorHandler
from hed.models.hed_ops import HedOps


class DemoToggleContextTag(HedOps):
    """ Handles converting Def/ and Def-expand/.

    Notes:
       - The class provides string funcs but no tag funcs when extending HedOps.
       - The class can expand or shrink definitions in hed strings via
         Def/XXX and (Def-expand/XXX ...).

    """

    def __init__(self):
        """ Initialize mapper for definitions in hed strings.

        Args:
            def_dicts (list or DefDict): DefDicts containing the definitions this mapper should initialize with.

        Notes:
            - More definitions can be added later.

        """
        super().__init__()
        self.found_toggle_context = False
        self.strings_processed = []

    def toggle_context_and_replace(self, hed_string_obj):
        """
            hed_string_obj(HedStringObj):
        """
        if self.found_toggle_context:
            tags_to_remove = hed_string_obj.find_tags(["context"], recursive=True, include_groups=0)
            if tags_to_remove:
                hed_string_obj.replace(tags_to_remove[0], HedTag("THISWASREPLACED"))

        tags_to_remove = hed_string_obj.find_tags(["togglecontext"], recursive=True, include_groups=0)
        if tags_to_remove:
            hed_string_obj.remove(tags_to_remove)
            self.found_toggle_context = not self.found_toggle_context
        self.strings_processed.append(hed_string_obj.get_original_hed_string())


        return []

    def __get_string_funcs__(self, **kwargs):
        """ String funcs for processing definitions. """
        string_funcs = []
        string_funcs.append(self.toggle_context_and_replace)
        return string_funcs

    def __get_tag_funcs__(self, **kwargs):
        return []

if __name__ == '__main__':
    from hed.models import hed_ops
    hed_op = DemoToggleContextTag()
    hed_string = "ToggleContext, Def/Hi"
    hed_string2 = hed_ops.apply_ops(hed_string, hed_op)
    print(hed_string2)

    hed_string = "Context, Taco"
    hed_string2 = hed_ops.apply_ops(hed_string, hed_op)
    print(hed_string2)

    # Note this is 3 strings in one call!!
    hed_string = ["Def/Hi, Context", "Taco, (ToggleContext, ThirdTag)", "Context"]
    hed_string2 = hed_ops.apply_ops(hed_string, hed_op)
    print(hed_string2)

    hed_string = "Context, Taco"
    hed_string2 = hed_ops.apply_ops(hed_string, hed_op)
    print(hed_string2)
    breakHEre = 3

