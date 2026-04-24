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
"""Module which contains low-level data types for the data in this package"""

from __future__ import annotations

import enum
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer, PlainValidator


class Gender(enum.StrEnum):
    """Enumeration of student gender options."""

    MALE = "Male"
    """Male gender."""

    FEMALE = "Female"
    """Female gender."""


Gender.MALE._add_value_alias_("male")
Gender.MALE._add_value_alias_("m")
Gender.FEMALE._add_value_alias_("female")
Gender.FEMALE._add_value_alias_("f")


class Academic(enum.StrEnum):
    """Enumeration of math performance levels."""

    HIGH = "High"
    """High math performance."""

    MEDIUM = "Medium"
    """Medium math performance."""

    LOW = "Low"
    """Low math performance."""


Academic.HIGH._add_value_alias_("high")
Academic.HIGH._add_value_alias_("h")
Academic.HIGH._add_value_alias_("above grade level")
Academic.MEDIUM._add_value_alias_("medium")
Academic.MEDIUM._add_value_alias_("m")
Academic.MEDIUM._add_value_alias_("on grade level")
Academic.LOW._add_value_alias_("low")
Academic.LOW._add_value_alias_("l")
Academic.LOW._add_value_alias_("below grade level")


class Behavior(enum.StrEnum):
    """Enumeration of behavior performance levels."""

    HIGH = "High"
    """High behavior rating (good behavior)."""

    MEDIUM = "Medium"
    """Medium behavior rating."""

    LOW = "Low"
    """Low behavior rating (needs improvement)."""


Behavior.HIGH._add_value_alias_("high")
Behavior.HIGH._add_value_alias_("h")
Behavior.HIGH._add_value_alias_("outstanding")
Behavior.MEDIUM._add_value_alias_("medium")
Behavior.MEDIUM._add_value_alias_("m")
Behavior.MEDIUM._add_value_alias_("satisfactory")
Behavior.LOW._add_value_alias_("low")
Behavior.LOW._add_value_alias_("l")
Behavior.LOW._add_value_alias_("needs support")


class Cluster(enum.StrEnum):
    """Enumeration of special program clusters."""

    AC = "AC"
    """Academically Challenged cluster."""

    GEM = "GEM"
    """Gifted Education Model cluster."""

    EL = "EL"
    """English Learner cluster."""


def _pydantic_bool_parser(val: Any) -> bool:
    """Parse boolean values from various input formats.

    Accepts:
    - Boolean values: True, False
    - Case-insensitive strings: "true", "false", "yes", "no", "y", "n"
    - Numeric strings: "1", "0"
    - Empty/whitespace strings: treated as False
    - None: treated as False

    Args:
        val: The value to parse as a boolean.

    Returns:
        The parsed boolean value.

    Raises:
        ValueError: If the value cannot be parsed as a boolean.
    """
    if isinstance(val, bool):
        return val

    if val is None:
        return False

    if isinstance(val, str):
        # Strip whitespace and convert to lowercase
        cleaned = val.strip().lower()

        # Empty string is treated as False
        if cleaned == "":
            return False

        # Accept various true/false representations
        if cleaned in ("true", "yes", "y", "1"):
            return True
        if cleaned in ("false", "no", "n", "0"):
            return False

    raise ValueError(f"Cannot parse {val!r} as a boolean")


BoolField = Annotated[bool, PlainValidator(_pydantic_bool_parser)]


def _pydantic_csv_pre_parser(val: Any) -> Any:
    if isinstance(val, str):
        return [item.strip() for item in val.strip().split(",")]
    return val


def _pydantic_csv_serializer(val: list) -> str:
    return ", ".join([str(item) for item in val])


type CSVList[T] = Annotated[
    list[T],
    BeforeValidator(_pydantic_csv_pre_parser),
    PlainSerializer(_pydantic_csv_serializer)
]
