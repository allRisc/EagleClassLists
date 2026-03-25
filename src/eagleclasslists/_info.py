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
"""Package metadata for EagleClassLists.

This module provides package-level metadata including version and author
information. The version is dynamically retrieved from the installed
package metadata.

Attributes:
    __version__: The current version of the package.
    __author__: The primary author of the package.
"""

from __future__ import annotations

import importlib.metadata

__version__: str = importlib.metadata.version("eagleclasslists")
__author__: str = "Benjamin Davis"
