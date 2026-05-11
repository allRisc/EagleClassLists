####################################################################################################
# EagleClassLists is a tool used to aid in the creation of class lists for schools.
# Copyright (C) 2026, Benjamin Davis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
####################################################################################################
"""Error classes for data operations."""


class ExcelImportError(Exception):
    """Custom exception for Excel import errors with user-friendly messages."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize the error with a message and optional details.

        Args:
            message: User-friendly error message.
            details: Additional technical details or suggestions.
        """
        self.message = message
        self.details = details
        super().__init__(message)
