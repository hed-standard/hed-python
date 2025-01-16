from hed.errors.error_reporter import ErrorHandler
from hed.models.hed_tag import HedTag
from hed.errors.error_types import ValidationErrors


class DuplicateChecker:

    def __init__(self, hed_schema):
        """ Constructor for GroupValidator

        Parameters:
            hed_schema (HedSchema): A HedSchema object.
        """
        if hed_schema is None:
            raise ValueError("HedSchema required for validation")
        self._hed_schema = hed_schema
        self.issues = []

    def check_for_duplicates(self, original_group):
        self.issues = []
        self._get_recursive_hash(original_group)
        return self.issues

    def get_hash(self, original_group):
        self.issues = []
        duplication_hash = self._get_recursive_hash(original_group)
        return duplication_hash

    def _get_recursive_hash(self, group):
        if len(self.issues) > 0:
            return None
        group_hashes = set()
        for child in group.children:
            if isinstance(child, HedTag):
                this_hash = hash(child)
            else:
                this_hash = self._get_recursive_hash(child)
            if len(self.issues) > 0 or this_hash is None:
                return None
            if this_hash in group_hashes:
                self.issues += self._get_duplication_error(child)
                return None
            group_hashes.add(this_hash)
        return hash(frozenset(group_hashes))

    @staticmethod
    def _get_duplication_error(child):
        if isinstance(child, HedTag):
            return ErrorHandler.format_error(ValidationErrors.HED_TAG_REPEATED, child)
        else:
            found_group = child
            base_steps_up = 0
            while isinstance(found_group, list):
                found_group = found_group[0]
                base_steps_up += 1
            for _ in range(base_steps_up):
                found_group = found_group._parent
            return ErrorHandler.format_error(ValidationErrors.HED_TAG_REPEATED_GROUP, found_group)
