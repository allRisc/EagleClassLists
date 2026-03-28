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

"""Data models for class lists, teachers, and students.

This module defines the core data structures used throughout EagleClassLists
for representing grade levels, classrooms, teachers, and students with their
attributes.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Gender(enum.StrEnum):
    """Enumeration of student gender options."""

    MALE = enum.auto()
    """Male gender."""

    FEMALE = enum.auto()
    """Female gender."""


class Academics(enum.StrEnum):
    """Enumeration of academic performance levels."""

    HIGH = enum.auto()
    """High academic performance."""

    MEDIUM = enum.auto()
    """Medium academic performance."""

    LOW = enum.auto()
    """Low academic performance."""


class Behavior(enum.StrEnum):
    """Enumeration of behavior performance levels."""

    HIGH = enum.auto()
    """High behavior rating (good behavior)."""

    MEDIUM = enum.auto()
    """Medium behavior rating."""

    LOW = enum.auto()
    """Low behavior rating (needs improvement)."""


class Cluster(enum.StrEnum):
    """Enumeration of special program clusters."""

    AC = enum.auto()
    """Academically Challenged cluster."""

    GEM = enum.auto()
    """Gifted Education Model cluster."""

    EL = enum.auto()
    """English Learner cluster."""


@dataclass
class GradeList:
    """Represents a grade level with its classrooms, teachers, and students.

    This class holds all the data for a single grade level, including the
    list of classrooms, all teachers, and all students at that grade.
    """

    classes: list[Classroom]
    """List of Classroom objects in this grade."""

    teachers: list[Teacher]
    """List of Teacher objects for this grade."""

    students: list[Student]
    """List of Student objects in this grade."""


@dataclass
class Classroom:
    """Represents a single classroom with a teacher and assigned students."""

    teacher: Teacher
    """The Teacher assigned to this classroom."""

    students: list[Student]
    """List of Student objects assigned to this classroom."""


@dataclass
class Teacher:
    """Represents a teacher with their name and cluster qualifications."""

    name: str
    """The teacher's full name."""

    clusters: list[Cluster] = field(default_factory=list)
    """List of Cluster types this teacher is qualified to teach."""


@dataclass
class Student:
    """Represents a student with their personal and academic attributes."""

    first_name: str
    """The student's first name."""

    last_name: str
    """The student's last name."""

    gender: Gender
    """The student's gender (Gender enum)."""

    academics: Academics
    """The student's academic performance level (Academics enum)."""

    behavior: Behavior
    """The student's behavior rating (Behavior enum)."""

    teacher: Teacher | None = None
    """The assigned Teacher, or None if unassigned."""

    cluster: Cluster | None = None
    """The student's Cluster assignment, or None."""

    resource: bool = False
    """Whether the student receives resource services."""

    speech: bool = False
    """Whether the student receives speech services."""
