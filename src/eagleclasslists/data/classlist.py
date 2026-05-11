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

from dataclasses import dataclass
from typing import Any

import pydantic

from eagleclasslists.data.types import Academic, Behavior, BoolField, Cluster, CSVList, Gender


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

        # Handle both lowercase field names and capitalized aliases (from Excel)
        teachers_data = info.data.get("teachers") or info.data.get("Teachers", [])
        students_data = info.data.get("students") or info.data.get("Students", [])

        teacher_dict: dict[str, Teacher] = {
            teacher.name: teacher for teacher in list(teachers_data)
        }
        student_dict: dict[str, Student] = {
            f"{student.first_name}_{student.last_name}": student for student in list(students_data)
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
    def serialize_classes(self, value: list[Classroom]) -> list[dict[str, str | None]]:
        serial_classes: list[dict[str, str | None]] = []
        for classroom in value:
            for student in classroom.students:
                serial_classes.append(
                    {
                        "Teacher Name": classroom.teacher.name,
                        "Teacher Grade": classroom.teacher.grade,
                        "Student First Name": student.first_name,
                        "Student Last Name": student.last_name,
                        "Student Grade": student.grade,
                    }
                )
        return serial_classes


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

    name: str
    """The teacher's full name."""

    grade: str | None = pydantic.Field(alias="Grade", default=None)
    """The grade level this teacher belongs to."""

    clusters: CSVList[Cluster] = pydantic.Field(alias="Clusters", default_factory=list)
    """List of Cluster types this teacher is qualified to teach."""

    @pydantic.field_validator("grade", mode="before")
    @classmethod
    def convert_grade_to_str(cls, val: Any) -> Any:
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return None
        return str(val)


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

    cluster: Cluster | None = pydantic.Field(alias="Cluster", default=None)
    """The student's Cluster assignment, or None."""

    math: Academic = pydantic.Field(alias="Math")
    """The student's math performance level (Math enum)."""

    ela: Academic = pydantic.Field(alias="ELA")
    """The student's ELA performance level (ELA enum)."""

    behavior: Behavior = pydantic.Field(alias="Behavior")
    """The student's behavior rating (Behavior enum)."""

    grade: str | None = pydantic.Field(alias="Grade", default=None)
    """The grade level this student belongs to."""

    teacher: str | None = pydantic.Field(alias="Teacher", default=None)
    """The assigned Teacher, or None if unassigned."""

    resource: BoolField = pydantic.Field(alias="Resource", default=False)
    """Whether the student receives resource services."""

    speech: BoolField = pydantic.Field(alias="Speech", default=False)
    """Whether the student receives speech services."""

    exclusions: CSVList[str] = pydantic.Field(alias="Exclusions", default_factory=list)
    """List of student names (FirstName LastName) this student cannot be with."""

    @pydantic.field_validator("first_name", "last_name", "teacher", "grade", mode="before")
    @classmethod
    def _clean_simple_str(cls, val: Any) -> Any:
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return None
        return str(val.strip())

    @pydantic.field_validator("gender", "math", "ela", "behavior", "grade", mode="before")
    @classmethod
    def _clean_simple_alias(cls, val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, str):
            if val.strip() == "":
                return None
            return val.strip().lower()
        return str(val).strip().lower()

    @pydantic.field_validator("ela", "math", mode="before")
    @classmethod
    def _default_ac_academics(cls, val: Any, info: pydantic.ValidationInfo) -> Any:
        if val is None and "cluster" in info.data and info.data["cluster"] == Cluster.AC:
            return Academic.LOW
        return val

    @pydantic.field_validator("behavior", mode="before")
    @classmethod
    def _default_ac_behavior(cls, val: Any, info: pydantic.ValidationInfo) -> Any:
        if val is None and "cluster" in info.data and info.data["cluster"] == Cluster.AC:
            return Behavior.LOW
        return val

    def summary_string(self, all_students: list[Student] | None = None) -> str:
        """Generate a summary string for display in UI components.

        Args:
            all_students: Optional list of all students for orphaned exclusion detection.

        Returns:
            Formatted summary string with student attributes.
        """
        attrs = [
            self.gender.value,
            f"🔢 {self.math.value}",
            f"📚 {self.ela.value}",
            f"😊 {self.behavior.value}",
        ]
        if self.cluster:
            attrs.append(f"🎯 {self.cluster.value}")
        if self.resource:
            attrs.append("🔧 Resource")
        if self.speech:
            attrs.append("🗣️ Speech")
        if self.teacher:
            attrs.append(f"👨‍🏫 {self.teacher}")
        if self.exclusions:
            if all_students is not None:
                valid_exclusions = self._get_valid_exclusions(all_students)
                orphaned_count = len(self.exclusions) - len(valid_exclusions)
                if orphaned_count > 0:
                    attrs.append(f"🚫 {len(self.exclusions)} ({orphaned_count} orphaned)")
                else:
                    attrs.append(f"🚫 {len(self.exclusions)}")
            else:
                attrs.append(f"🚫 {len(self.exclusions)}")
        return " • ".join(attrs)

    def _get_valid_exclusions(self, all_students: list[Student]) -> list[str]:
        """Get list of valid exclusions (students that actually exist).

        Args:
            all_students: List of all students in the grade.

        Returns:
            List of exclusion names that correspond to existing students.
        """
        existing_names = {f"{s.first_name} {s.last_name}" for s in all_students}
        return [ex for ex in self.exclusions if ex in existing_names]
