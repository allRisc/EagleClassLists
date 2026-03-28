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
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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

    def save_to_excel(self, filepath: str | Path) -> None:
        """Save the grade list to an Excel file with three sheets.

        Creates an Excel file with "Teachers", "Students", and "Classrooms"
        sheets following the Option C structure.

        Args:
            filepath: Path to the Excel file to create.

        Raises:
            ImportError: If openpyxl is not installed.
        """
        try:
            from openpyxl import Workbook
        except ImportError as err:
            raise ImportError(
                "openpyxl is required for Excel support. Install it with: uv add openpyxl"
            ) from err

        wb = Workbook()

        # Remove default sheet and create our three sheets
        if wb.active is not None:
            wb.remove(wb.active)
        teachers_sheet = wb.create_sheet("Teachers")
        students_sheet = wb.create_sheet("Students")
        classrooms_sheet = wb.create_sheet("Classrooms")

        # Write Teachers sheet
        teachers_sheet.append(["name", "clusters"])
        for teacher in self.teachers:
            clusters_str = ", ".join(str(c) for c in teacher.clusters)
            teachers_sheet.append([teacher.name, clusters_str])

        # Write Students sheet
        students_sheet.append(
            [
                "first_name",
                "last_name",
                "gender",
                "academics",
                "behavior",
                "cluster",
                "resource",
                "speech",
            ]
        )
        for student in self.students:
            students_sheet.append(
                [
                    student.first_name,
                    student.last_name,
                    str(student.gender),
                    str(student.academics),
                    str(student.behavior),
                    str(student.cluster) if student.cluster else "",
                    "TRUE" if student.resource else "FALSE",
                    "TRUE" if student.speech else "FALSE",
                ]
            )

        # Write Classrooms sheet
        classrooms_sheet.append(["teacher_name", "student_first", "student_last"])
        for classroom in self.classes:
            for student in classroom.students:
                classrooms_sheet.append(
                    [classroom.teacher.name, student.first_name, student.last_name]
                )

        wb.save(filepath)

    @classmethod
    def from_excel(cls, filepath: str | Path) -> GradeList:
        """Load a grade list from an Excel file.

        Reads an Excel file with "Teachers", "Students", and "Classrooms"
        sheets and reconstructs the GradeList object.

        Args:
            filepath: Path to the Excel file to read.

        Returns:
            A GradeList object populated from the Excel data.

        Raises:
            ImportError: If openpyxl is not installed.
            ValueError: If the Excel file has invalid data.
        """
        try:
            from openpyxl import load_workbook
        except ImportError as err:
            raise ImportError(
                "openpyxl is required for Excel support. Install it with: uv add openpyxl"
            ) from err

        wb = load_workbook(filepath)

        # Read Teachers sheet
        teachers_sheet = wb["Teachers"]
        teachers: dict[str, Teacher] = {}
        for row in teachers_sheet.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            name = str(row[0])
            clusters_str = str(row[1]) if row[1] else ""
            cluster_list = [Cluster(c.strip()) for c in clusters_str.split(",") if c.strip()]
            teachers[name] = Teacher(name=name, clusters=cluster_list)

        # Read Students sheet
        students_sheet = wb["Students"]
        students: dict[tuple[str, str], Student] = {}
        for row in students_sheet.iter_rows(min_row=2, values_only=True):
            if not row[0] or not row[1]:
                continue
            first_name = str(row[0])
            last_name = str(row[1])
            gender = Gender(str(row[2])) if row[2] else Gender.MALE
            academics = Academics(str(row[3])) if row[3] else Academics.MEDIUM
            behavior = Behavior(str(row[4])) if row[4] else Behavior.MEDIUM
            cluster = Cluster(str(row[5])) if row[5] else None
            resource = str(row[6]).upper() == "TRUE" if row[6] else False
            speech = str(row[7]).upper() == "TRUE" if row[7] else False

            student = Student(
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                academics=academics,
                behavior=behavior,
                cluster=cluster,
                resource=resource,
                speech=speech,
            )
            students[(first_name, last_name)] = student

        # Read Classrooms sheet and build classroom structure
        classrooms_sheet = wb["Classrooms"]
        classroom_map: dict[str, list[Student]] = {}
        for row in classrooms_sheet.iter_rows(min_row=2, values_only=True):
            if not row[0] or not row[1] or not row[2]:
                continue
            teacher_name = str(row[0])
            student_first = str(row[1])
            student_last = str(row[2])

            student_key = (student_first, student_last)
            if student_key in students:
                if teacher_name not in classroom_map:
                    classroom_map[teacher_name] = []
                classroom_map[teacher_name].append(students[student_key])

        # Build Classroom objects
        classroom_list: list[Classroom] = []
        for teacher_name, student_list in classroom_map.items():
            if teacher_name in teachers:
                classroom_list.append(
                    Classroom(teacher=teachers[teacher_name], students=student_list)
                )

        # Update teacher references in students
        for classroom in classroom_list:
            for student in classroom.students:
                student.teacher = classroom.teacher

        return cls(
            classes=classroom_list,
            teachers=list(teachers.values()),
            students=list(students.values()),
        )


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
