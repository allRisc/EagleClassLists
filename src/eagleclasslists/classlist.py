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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd
import pydantic


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
            ExcelImportError: If the Excel file has invalid data or format.
        """
        try:
            with pd.ExcelFile(filepath) as ef:
                # Check for required sheets
                required_sheets = {"Teachers", "Students"}
                available_sheets: set[str] = {str(s) for s in ef.sheet_names}
                missing_sheets = required_sheets - available_sheets

                if missing_sheets:
                    sheet_list = ", ".join(f'"{s}"' for s in sorted(missing_sheets))
                    available_list = ", ".join(f'"{s}"' for s in sorted(available_sheets))
                    raise ExcelImportError(
                        f"Missing required sheet(s): {sheet_list}",
                        f"The Excel file must contain 'Teachers' and 'Students' sheets. "
                        f"Available sheets: {available_list}. "
                        f"Please check that your file was exported correctly.",
                    )

                # Parse each sheet
                data: dict[str, list[dict]] = {}
                for sheet in ef.sheet_names:
                    sheet_name = str(sheet)
                    try:
                        data[sheet_name] = cls._sheet_to_clean_records(ef, sheet_name)
                    except Exception as e:
                        raise ExcelImportError(
                            f"Error reading '{sheet_name}' sheet",
                            f"Could not parse the '{sheet_name}' sheet. "
                            f"Make sure it contains valid table data with headers. "
                            f"Technical error: {e}",
                        ) from e

                # Validate the data
                try:
                    return cls.model_validate(data)
                except pydantic.ValidationError as e:
                    # Build user-friendly error messages from validation errors
                    errors = []
                    for err in e.errors():
                        loc = " -> ".join(str(x) for x in err["loc"])
                        msg = err["msg"]
                        errors.append(f"  • {loc}: {msg}")

                    error_details = "\n".join(errors)
                    raise ExcelImportError(
                        "Data validation failed. Please check your Excel file format.",
                        f"The following fields have errors:\n{error_details}\n\n"
                        f"Common issues:\n"
                        f"  • Make sure required columns are present: "
                        f"Name (Teachers), First Name, Last Name, Gender, Math, ELA, "
                        f"Behavior (Students)\n"
                        f"  • Gender must be: Male, Female, M, or F\n"
                        f"  • Math/ELA/Behavior must be: High, Medium, Low, H, M, or L\n"
                        f"  • Cluster must be: AC, GEM, EL, or blank\n"
                        f"  • Resource and Speech must be: TRUE/FALSE, Yes/No, or 1/0",
                    ) from e

        except pd.errors.EmptyDataError as e:
            raise ExcelImportError(
                "The Excel file is empty",
                "The uploaded file contains no data. Please check the file and try again.",
            ) from e
        except pd.errors.ParserError as e:
            raise ExcelImportError(
                "Could not parse the Excel file",
                f"The file appears to be corrupted or is not a valid Excel file. "
                f"Technical error: {e}",
            ) from e
        except FileNotFoundError as e:
            raise ExcelImportError(
                "Excel file not found",
                "The specified file could not be found. Please check the path.",
            ) from e
        except Exception as e:
            # Re-raise ExcelImportError as-is
            if isinstance(e, ExcelImportError):
                raise
            # Convert unexpected errors
            raise ExcelImportError(
                "Unexpected error loading Excel file",
                f"An unexpected error occurred: {type(e).__name__}: {e}. "
                f"Please check that your file is a valid Excel file (.xlsx).",
            ) from e

    @staticmethod
    def _sheet_to_clean_records(file: pd.ExcelFile, sheet_name: str) -> list[dict]:
        df = file.parse(sheet_name=sheet_name)
        records = []
        for _, row in df.iterrows():
            # Drop NaN values and convert to dict
            clean_row = row.dropna().to_dict()
            # Skip empty rows (all values were NaN/blank)
            if clean_row:
                records.append(clean_row)
        return records


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

    @pydantic.model_validator(mode="before")
    @classmethod
    def set_ac_cluster_defaults(cls, data: Any) -> Any:
        """Set default math, ELA, and behavior to Low for AC cluster students.

        If a student is in the AC (Academically Challenged) cluster and no
        math, ELA, or behavior values are provided, they default to Low.

        Args:
            data: The raw input data being validated.

        Returns:
            The data with defaults applied for AC cluster students.
        """
        if not isinstance(data, dict):
            return data

        # Check if student is in AC cluster (handle both enum and string values)
        cluster = data.get("cluster") or data.get("Cluster")
        if cluster is None:
            return data

        # Normalize cluster value to check for AC
        cluster_value = cluster
        if isinstance(cluster, Cluster):
            cluster_value = cluster.value
        elif isinstance(cluster, str):
            cluster_value = cluster.strip().upper()

        if cluster_value != "AC":
            return data

        # Set defaults for AC cluster students if fields are not provided
        # Check both alias and field names
        math_fields = ("math", "Math")
        ela_fields = ("ela", "ELA")
        behavior_fields = ("behavior", "Behavior")

        if not any(field in data and data[field] is not None for field in math_fields):
            data["math"] = Math.LOW

        if not any(field in data and data[field] is not None for field in ela_fields):
            data["ela"] = ELA.LOW

        if not any(field in data and data[field] is not None for field in behavior_fields):
            data["behavior"] = Behavior.LOW

        return data

    @pydantic.field_validator("gender", mode="before")
    @classmethod
    def parse_gender(cls, val: Any) -> Any:
        """Parse gender values from various input formats.

        Accepts:
        - Gender enum values directly
        - Case-insensitive strings: "male", "female"
        - Abbreviations: "m", "f" (case-insensitive)

        Args:
            val: The value to parse as a gender.

        Returns:
            The parsed Gender enum value or the original value for further processing.
        """
        if isinstance(val, Gender):
            return val

        if isinstance(val, str):
            cleaned = val.strip().lower()

            # Map abbreviations and variations to enum values
            if cleaned in ("male", "m"):
                return Gender.MALE
            if cleaned in ("female", "f"):
                return Gender.FEMALE

        return val

    @pydantic.field_validator("math", "ela", "behavior", mode="before")
    @classmethod
    def parse_level_enum(cls, val: Any, info: pydantic.ValidationInfo) -> Any:
        """Parse level enum values (High/Medium/Low) from various input formats.

        Accepts:
        - Enum values directly (Math, ELA, or Behavior)
        - Case-insensitive strings: "high", "medium", "low"
        - Abbreviations: "h", "m", "l" (case-insensitive)

        Args:
            val: The value to parse.
            info: Validation info containing the field name.

        Returns:
            The parsed enum value or the original value for further processing.
        """
        field_name = info.field_name

        # Get the expected enum type based on field name
        enum_type: type[Math] | type[ELA] | type[Behavior]
        if field_name == "math":
            enum_type = Math
        elif field_name == "ela":
            enum_type = ELA
        elif field_name == "behavior":
            enum_type = Behavior
        else:
            return val

        # If already the correct enum type, return it
        if isinstance(val, enum_type):
            return val

        if isinstance(val, str):
            cleaned = val.strip().lower()

            # Map abbreviations and variations to enum values
            if cleaned in ("high", "h"):
                return enum_type.HIGH
            if cleaned in ("medium", "m"):
                return enum_type.MEDIUM
            if cleaned in ("low", "l"):
                return enum_type.LOW

        return val

    @pydantic.field_validator("resource", "speech", mode="before")
    @classmethod
    def parse_boolean(cls, val: Any) -> bool:
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
