from typing import Union

from hed.errors.error_reporter import ErrorHandler
from hed.models.hed_tag import HedTag
from hed.errors.error_types import ValidationErrors


class DuplicateChecker:

    def __init__(self):
        """ Checker for duplications in HED groups.

        Notes:
            This checker has an early out strategy -- it returns when it finds an error.

        """
        self.issues = []

    def check_for_duplicates(self, group) -> list[dict]:
        """ Find duplicates in a HED group and return the errors found.

        Parameters:
             group (HedGroup): The HED group to be checked.

        Returns:
            list:   List of validation issues -- which might be empty if no duplicates detected.


        """
        self.issues = []
        self._get_recursive_hash(group)
        return self.issues

    def get_hash(self, group) -> Union[int, None]:
        """  Return the unique hash for the group as long as no duplicates.

        Parameters:
             group (HedGroup): The HED group to be checked.

        Returns:
            Union[int, None]: Unique hash or None if duplicates were detected within the group.

        Note: As a side effect, this method will clear the issues list if no duplicates are found.
        """
        self.issues = []
        duplication_hash = self._get_recursive_hash(group)
        return duplication_hash

    def _get_recursive_hash(self, group) -> Union[int, None]:
        """Get recursive hash for a group.

        Parameters:
            group: The HED group to process.

        Returns:
            int | None: Hash value or None if issues detected.
        """
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
    def _get_duplication_error(child) -> list[dict]:
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
