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
import pprint
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd
import pydantic


class Gender(enum.StrEnum):
    """Enumeration of student gender options."""

    MALE = "Male"
    """Male gender."""

    FEMALE = "Female"
    """Female gender."""


class Math(enum.StrEnum):
    """Enumeration of math performance levels."""

    HIGH = "High"
    """High math performance."""

    MEDIUM = "Medium"
    """Medium math performance."""

    LOW = "Low"
    """Low math performance."""


class ELA(enum.StrEnum):
    """Enumeration of ELA (English Language Arts) performance levels."""

    HIGH = "High"
    """High ELA performance."""

    MEDIUM = "Medium"
    """Medium ELA performance."""

    LOW = "Low"
    """Low ELA performance."""


class Behavior(enum.StrEnum):
    """Enumeration of behavior performance levels."""

    HIGH = "High"
    """High behavior rating (good behavior)."""

    MEDIUM = "Medium"
    """Medium behavior rating."""

    LOW = "Low"
    """Low behavior rating (needs improvement)."""


class Cluster(enum.StrEnum):
    """Enumeration of special program clusters."""

    AC = "AC"
    """Academically Challenged cluster."""

    GEM = "GEM"
    """Gifted Education Model cluster."""

    EL = "EL"
    """English Learner cluster."""


class GradeList(pydantic.BaseModel):
    """Represents a grade level with its classrooms, teachers, and students.

    This class holds all the data for a single grade level, including the
    list of classrooms, all teachers, and all students at that grade.
    """

    model_config = pydantic.ConfigDict(populate_by_name=True, serialize_by_alias=True)

    teachers: list[Teacher] = pydantic.Field(alias="Teachers")
    """List of Teacher objects for this grade."""

    students: list[Student] = pydantic.Field(alias="Students")
    """List of Student objects in this grade."""

    classes: list[Classroom] = pydantic.Field(alias="Classes", default_factory=list)
    """List of Classroom objects in this grade."""

    @pydantic.field_validator("classes", mode="plain")
    @classmethod
    def validate_classes(cls, value: Any, info: pydantic.ValidationInfo) -> list[Classroom]:
        if not isinstance(value, list):
            raise TypeError("GradeList.classes must be a list")

        classes: dict[str, Classroom] = {}

        teacher_dict: dict[str, Teacher] = {
            teacher.name: teacher for teacher in list(info.data["teachers"])
        }
        student_dict: dict[str, Student] = {
            f"{student.first_name}_{student.last_name}": student
            for student in list(info.data["students"])
        }

        for val in value:
            if isinstance(val, Classroom):
                classes[val.teacher.name] = val
                continue

            teacher_name = val["Teacher Name"]
            student_name = f"{val['Student First Name']}_{val['Student Last Name']}"

            if teacher_name not in teacher_dict:
                raise ValueError(f"Teacher ({teacher_name}) specified in classroom not found")
            if student_name not in student_dict:
                raise ValueError(
                    f"Student ({student_name.replace('_', ' ')}) specified in classroom not found"
                )

            teacher = teacher_dict[teacher_name]
            student = student_dict[student_name]

            if teacher.name in classes:
                classes[teacher.name].students.append(student)
            else:
                classes[teacher.name] = Classroom(teacher, [student])

        return list(classes.values())

    @pydantic.field_serializer("classes", mode="plain")
    def serialize_classes(self, value: list[Classroom]) -> list[dict[str, str]]:
        serial_classes: list[dict[str, str]] = []
        for classroom in value:
            for student in classroom.students:
                serial_classes.append(
                    {
                        "Teacher Name": classroom.teacher.name,
                        "Student First Name": student.first_name,
                        "Student Last Name": student.last_name,
                    }
                )
        return serial_classes

    def save_to_excel(self, filepath: str | Path | BinaryIO) -> None:
        """Save the grade list to an Excel file with three sheets.

        Creates an Excel file with "Teachers", "Students", and "Classrooms"
        sheets following the Option C structure.

        Args:
            filepath: Path to the Excel file to create, or a file-like object
                to write to.
        """
        pprint.pprint(self.model_dump())
        with pd.ExcelWriter(filepath) as ew:
            for sheet in self.model_dump():
                self._list_attr_to_sheet(ew, attr=sheet)

    def _list_attr_to_sheet(self, ew: pd.ExcelWriter, attr: str) -> None:
        """Save the list for the attrs to the attr's sheet in the provided excel file

        Args:
            ew: The excel writer to use
            attr: The name of the attr to write
        """
        pd.DataFrame(self.model_dump()[attr]).to_excel(ew, sheet_name=attr, index=False)

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
            ValueError: If the Excel file has invalid data.
        """
        with pd.ExcelFile(filepath) as ef:
            return cls.model_validate(
                {sheet: cls._sheet_to_clean_records(ef, str(sheet)) for sheet in ef.sheet_names}
            )

    @staticmethod
    def _sheet_to_clean_records(file: pd.ExcelFile, sheet_name: str) -> list[dict]:
        df = file.parse(sheet_name=sheet_name)
        return [row.dropna().to_dict() for _, row in df.iterrows()]


@dataclass
class Classroom:
    """Represents a single classroom with a teacher and assigned students."""

    teacher: Teacher
    """The Teacher assigned to this classroom."""

    students: list[Student]
    """List of Student objects assigned to this classroom."""


class Teacher(pydantic.BaseModel):
    """Represents a teacher with their name and cluster qualifications."""

    model_config = pydantic.ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str = pydantic.Field(alias="Name")
    """The teacher's full name."""

    clusters: list[Cluster] = pydantic.Field(alias="Clusters", default_factory=list)
    """List of Cluster types this teacher is qualified to teach."""

    @pydantic.field_validator("clusters", mode="before")
    @classmethod
    def convert_clusters_to_list(cls, val: Any) -> Any:
        if isinstance(val, str):
            return [item.strip() for item in val.strip().split(",")]
        return val

    @pydantic.field_serializer("clusters", mode="plain")
    def convert_clusters_list_to_str(self, val: list[Cluster]) -> str:
        return ", ".join([str(cluster) for cluster in val])


class Student(pydantic.BaseModel):
    """Represents a student with their personal and academic attributes."""

    model_config = pydantic.ConfigDict(
        validate_by_name=True, validate_by_alias=True, serialize_by_alias=True
    )

    first_name: str = pydantic.Field(alias="First Name")
    """The student's first name."""

    last_name: str = pydantic.Field(alias="Last Name")
    """The student's last name."""

    gender: Gender = pydantic.Field(alias="Gender")
    """The student's gender (Gender enum)."""

    math: Math = pydantic.Field(alias="Math")
    """The student's math performance level (Math enum)."""

    ela: ELA = pydantic.Field(alias="ELA")
    """The student's ELA performance level (ELA enum)."""

    behavior: Behavior = pydantic.Field(alias="Behavior")
    """The student's behavior rating (Behavior enum)."""

    teacher: str | None = pydantic.Field(alias="Teacher", default=None)
    """The assigned Teacher, or None if unassigned."""

    cluster: Cluster | None = pydantic.Field(alias="Cluster", default=None)
    """The student's Cluster assignment, or None."""

    resource: bool = pydantic.Field(alias="Resource", default=False)
    """Whether the student receives resource services."""

    speech: bool = pydantic.Field(alias="Speech", default=False)
    """Whether the student receives speech services."""


def _attr_to_save_str(obj: Any, attr: str) -> str:
    if attr != "" and not hasattr(obj, attr):
        raise ValueError(f"Object of type {type(obj).__name__} does not have attr '{attr}'")

    if attr == "":
        val = obj
    else:
        val = getattr(obj, attr)

    if val is None:
        return ""

    if isinstance(val, str):
        return val

    if isinstance(val, list):
        return ", ".join([_attr_to_save_str(item, "") for item in val])

    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"

    return str(val)
