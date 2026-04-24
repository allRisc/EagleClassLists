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

"""Excel import/export functions for classlist data.

This module provides standalone functions for reading and writing teachers,
students, and classroom data to/from Excel files, decoupled from the data models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pydantic

from eagleclasslists.data.classlist import Classroom, Student, Teacher
from eagleclasslists.data.errors import ExcelImportError
from eagleclasslists.data.settings import (
    DEFAULT_PRESET,
    ColumnMappingPreset,
    rename_records_for_reading,
    rename_records_for_writing,
)


def save_teachers_to_excel(
    teachers: list[Teacher],
    filepath: str | Path,
    preset: ColumnMappingPreset = DEFAULT_PRESET,
) -> None:
    """Save teachers to a single-sheet Excel file.

    Args:
        teachers: List of Teacher objects to save.
        filepath: Path to the Excel file to create.
        preset: Column mapping preset defining sheet name and column headers.
    """
    records = [t.model_dump(by_alias=False) for t in teachers]
    renamed = rename_records_for_writing(records, preset.teacher_columns)
    df = pd.DataFrame(renamed) if renamed else pd.DataFrame()
    df.to_excel(filepath, sheet_name=preset.teachers_sheet, index=False)


def save_students_to_excel(
    students: list[Student],
    filepath: str | Path,
    preset: ColumnMappingPreset = DEFAULT_PRESET,
) -> None:
    """Save students to a single-sheet Excel file.

    Args:
        students: List of Student objects to save.
        filepath: Path to the Excel file to create.
        preset: Column mapping preset defining sheet name and column headers.
    """
    records = [s.model_dump(by_alias=False) for s in students]
    renamed = rename_records_for_writing(records, preset.student_columns)
    df = pd.DataFrame(renamed) if renamed else pd.DataFrame()
    df.to_excel(filepath, sheet_name=preset.students_sheet, index=False)


def save_classrooms_to_excel(
    classes: list[Classroom],
    filepath: str | Path,
    preset: ColumnMappingPreset = DEFAULT_PRESET,
) -> None:
    """Save classroom assignments to a single-sheet Excel file.

    The file contains only assignment mappings (teacher name,
    student first name, student last name).

    Args:
        classes: List of Classroom objects to save.
        filepath: Path to the Excel file to create.
        preset: Column mapping preset defining sheet name and column headers.
    """
    records: list[dict[str, str | None]] = []
    for classroom in classes:
        for student in classroom.students:
            records.append(
                {
                    "teacher_name": classroom.teacher.name,
                    "teacher_grade": classroom.teacher.grade,
                    "student_first_name": student.first_name,
                    "student_last_name": student.last_name,
                    "student_grade": student.grade,
                }
            )
    renamed = rename_records_for_writing(records, preset.classroom_columns)
    df = pd.DataFrame(renamed) if renamed else pd.DataFrame()
    df.to_excel(filepath, sheet_name=preset.classrooms_sheet, index=False)


def load_teachers_from_excel(
    filepath: str | Path,
    preset: ColumnMappingPreset = DEFAULT_PRESET,
) -> list[Teacher]:
    """Load teachers from a single-sheet Excel file.

    Args:
        filepath: Path to the Excel file to read.
        preset: Column mapping preset defining sheet name and column headers.

    Returns:
        A list of Teacher objects.

    Raises:
        ExcelImportError: If the Excel file has invalid data or format.
    """
    try:
        with pd.ExcelFile(filepath) as ef:
            records = _sheet_to_clean_records(ef, preset.teachers_sheet)
            renamed = rename_records_for_reading(records, preset.teacher_columns)
            return [Teacher.model_validate(r) for r in renamed]
    except FileNotFoundError as e:
        raise ExcelImportError(
            "Excel file not found",
            "The specified file could not be found. Please check the path.",
        ) from e
    except pd.errors.ParserError as e:
        raise ExcelImportError(
            "Could not parse the Excel file",
            f"The file appears to be corrupted or is not a valid Excel file. "
            f"Technical error: {e}",
        ) from e
    except pydantic.ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            msg = err["msg"]
            errors.append(f"  - {loc}: {msg}")
        error_details = "\n".join(errors)
        raise ExcelImportError(
            "Teacher data validation failed.",
            f"Errors:\n{error_details}\n\n"
            f"Required columns: Name, Clusters (optional).",
        ) from e
    except Exception as e:
        if isinstance(e, ExcelImportError):
            raise
        raise ExcelImportError(
            "Unexpected error loading teachers file",
            f"An unexpected error occurred: {type(e).__name__}: {e}",
        ) from e


def load_students_from_excel(
    filepath: str | Path,
    preset: ColumnMappingPreset = DEFAULT_PRESET,
) -> list[Student]:
    """Load students from a single-sheet Excel file.

    Args:
        filepath: Path to the Excel file to read.
        preset: Column mapping preset defining sheet name and column headers.

    Returns:
        A list of Student objects.

    Raises:
        ExcelImportError: If the Excel file has invalid data or format.
    """
    try:
        with pd.ExcelFile(filepath) as ef:
            records = _sheet_to_clean_records(ef, preset.students_sheet)
            renamed = rename_records_for_reading(records, preset.student_columns)
            return [Student.model_validate(r) for r in renamed]
    except FileNotFoundError as e:
        raise ExcelImportError(
            "Excel file not found",
            "The specified file could not be found. Please check the path.",
        ) from e
    except pd.errors.ParserError as e:
        raise ExcelImportError(
            "Could not parse the Excel file",
            f"The file appears to be corrupted or is not a valid Excel file. "
            f"Technical error: {e}",
        ) from e
    except pydantic.ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            msg = err["msg"]
            errors.append(f"  - {loc}: {msg}")
        error_details = "\n".join(errors)
        raise ExcelImportError(
            "Student data validation failed.",
            f"Errors:\n{error_details}\n\n"
            f"Required columns: First Name, Last Name, Gender, Math, ELA, Behavior.\n"
            f"Optional columns: Cluster, Resource, Speech, Teacher, Exclusions.",
        ) from e
    except Exception as e:
        if isinstance(e, ExcelImportError):
            raise
        raise ExcelImportError(
            "Unexpected error loading students file",
            f"An unexpected error occurred: {type(e).__name__}: {e}",
        ) from e


def load_classrooms_from_excel(
    filepath: str | Path,
    teachers: list[Teacher],
    students: list[Student],
    preset: ColumnMappingPreset = DEFAULT_PRESET,
) -> list[Classroom]:
    """Load classroom assignments from a single-sheet Excel file.

    Requires teachers and students lists to resolve references.

    Args:
        filepath: Path to the Excel file to read.
        teachers: List of Teacher objects for name resolution.
        students: List of Student objects for name resolution.
        preset: Column mapping preset defining sheet name and column headers.

    Returns:
        A list of Classroom objects.

    Raises:
        ExcelImportError: If references cannot be resolved.
    """
    teacher_dict: dict[str, Teacher] = {t.name: t for t in teachers}
    student_dict: dict[str, Student] = {
        f"{s.first_name}_{s.last_name}": s for s in students
    }

    try:
        with pd.ExcelFile(filepath) as ef:
            raw_records = _sheet_to_clean_records(ef, preset.classrooms_sheet)
            records = rename_records_for_reading(
                raw_records, preset.classroom_columns
            )
    except FileNotFoundError as e:
        raise ExcelImportError(
            "Excel file not found",
            "The specified file could not be found. Please check the path.",
        ) from e
    except pd.errors.ParserError as e:
        raise ExcelImportError(
            "Could not parse the Excel file",
            f"The file appears to be corrupted or is not a valid Excel file. "
            f"Technical error: {e}",
        ) from e
    except Exception as e:
        if isinstance(e, ExcelImportError):
            raise
        raise ExcelImportError(
            "Unexpected error loading classrooms file",
            f"An unexpected error occurred: {type(e).__name__}: {e}",
        ) from e

    classrooms: dict[str, Classroom] = {}
    for rec in records:
        teacher_name = rec.get("teacher_name")
        first_name = rec.get("student_first_name")
        last_name = rec.get("student_last_name")

        if not teacher_name:
            raise ExcelImportError(
                "Missing Teacher Name in classroom data",
                "Each row must have a 'teacher_name' column.",
            )
        if not first_name or not last_name:
            raise ExcelImportError(
                "Missing student name in classroom data",
                "Each row must have 'student_first_name' and 'student_last_name' columns.",
            )

        if teacher_name not in teacher_dict:
            raise ExcelImportError(
                f"Teacher '{teacher_name}' not found",
                "Load the teachers file before loading classrooms.",
            )

        student_key = f"{first_name}_{last_name}"
        if student_key not in student_dict:
            raise ExcelImportError(
                f"Student '{first_name} {last_name}' not found",
                "Load the students file before loading classrooms.",
            )

        teacher = teacher_dict[teacher_name]
        student = student_dict[student_key]

        if teacher.name in classrooms:
            classrooms[teacher.name].students.append(student)
        else:
            classrooms[teacher.name] = Classroom(teacher, [student])

    return list(classrooms.values())


def _sheet_to_clean_records(file: pd.ExcelFile, sheet_name: str) -> list[dict[str, Any]]:
    """Parse an Excel sheet into a list of clean dicts.

    Drops rows with all NaN values and converts each row to a dict.

    Args:
        file: Open ExcelFile object.
        sheet_name: Name of the sheet to read.

    Returns:
        List of dicts, one per non-empty row.

    Raises:
        ExcelImportError: If no sheet can be found.
    """
    if sheet_name in file.sheet_names:
        df = file.parse(sheet_name=sheet_name)
    elif len(file.sheet_names):
        df = file.parse(sheet_name=0)
    else:
        raise ExcelImportError("Could not find a sheet in the provided excel file")

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        clean_row: dict[str, Any] = {str(k): v for k, v in row.dropna().to_dict().items()}
        if clean_row:
            records.append(clean_row)
    return records
