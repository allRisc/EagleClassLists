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

"""Column mapping presets for configuring Excel import/export formats.

This module defines the data model for column mapping presets, which allow
users to map Excel column headers and sheet names to the internal attributes
used by EagleClassLists. Presets can be saved, loaded, and switched at runtime.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pydantic

_DEFAULT_TEACHER_COLUMNS: dict[str, str] = {
    "name": "Name",
    "grade": "Grade",
    "clusters": "Clusters",
}

_DEFAULT_STUDENT_COLUMNS: dict[str, str] = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "gender": "Gender",
    "math": "Math",
    "ela": "ELA",
    "behavior": "Behavior",
    "grade": "Grade",
    "teacher": "Teacher",
    "cluster": "Cluster",
    "resource": "Resource",
    "speech": "Speech",
    "exclusions": "Exclusions",
}

_DEFAULT_CLASSROOM_COLUMNS: dict[str, str] = {
    "teacher_name": "Teacher Name",
    "teacher_grade": "Teacher Grade",
    "student_first_name": "Student First Name",
    "student_last_name": "Student Last Name",
    "student_grade": "Student Grade",
}

TEACHER_FIELDS: list[str] = list(_DEFAULT_TEACHER_COLUMNS.keys())
"""Ordered list of teacher attribute names for UI presentation."""

STUDENT_FIELDS: list[str] = list(_DEFAULT_STUDENT_COLUMNS.keys())
"""Ordered list of student attribute names for UI presentation."""

CLASSROOM_FIELDS: list[str] = list(_DEFAULT_CLASSROOM_COLUMNS.keys())
"""Ordered list of classroom attribute names for UI presentation."""

REQUIRED_STUDENT_FIELDS: set[str] = {
    "first_name",
    "last_name",
    "gender",
    "math",
    "ela",
    "behavior",
}
"""Student fields that must be mapped for import to succeed."""

REQUIRED_TEACHER_FIELDS: set[str] = {"name"}
"""Teacher fields that must be mapped for import to succeed."""

REQUIRED_CLASSROOM_FIELDS: set[str] = {
    "teacher_name",
    "student_first_name",
    "student_last_name",
}
"""Classroom fields that must be mapped for import to succeed."""


class ColumnMappingPreset(pydantic.BaseModel):
    """A named preset mapping Excel columns and sheet names to internal attributes.

    Attributes:
        name: Display name for this preset (e.g. "Default", "Estes Format").
        teachers_sheet: Sheet name to read/write teachers from.
        students_sheet: Sheet name to read/write students from.
        classrooms_sheet: Sheet name to read/write classrooms from.
        teacher_columns: Mapping from Python attribute name to Excel column header.
        student_columns: Mapping from Python attribute name to Excel column header.
        classroom_columns: Mapping from Python attribute name to Excel column header.
    """

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str
    teachers_sheet: str = "Teachers"
    students_sheet: str = "Students"
    classrooms_sheet: str = "Classrooms"
    teacher_columns: dict[str, str] = pydantic.Field(
        default_factory=lambda: dict(_DEFAULT_TEACHER_COLUMNS)
    )
    student_columns: dict[str, str] = pydantic.Field(
        default_factory=lambda: dict(_DEFAULT_STUDENT_COLUMNS)
    )
    classroom_columns: dict[str, str] = pydantic.Field(
        default_factory=lambda: dict(_DEFAULT_CLASSROOM_COLUMNS)
    )

    def reverse_teacher_columns(self) -> dict[str, str]:
        """Return a reverse mapping from Excel column headers to attribute names."""
        return {v: k for k, v in self.teacher_columns.items()}

    def reverse_student_columns(self) -> dict[str, str]:
        """Return a reverse mapping from Excel column headers to attribute names."""
        return {v: k for k, v in self.student_columns.items()}

    def reverse_classroom_columns(self) -> dict[str, str]:
        """Return a reverse mapping from Excel column headers to attribute names."""
        return {v: k for k, v in self.classroom_columns.items()}


DEFAULT_PRESET = ColumnMappingPreset(name="Default")
"""The built-in default column mapping preset matching the original format."""

DEFAULT_PRESET_NAME = "Default"
"""The name of the built-in default preset (cannot be deleted)."""


def _config_dir() -> Path:
    """Return the platform-specific config directory for EagleClassLists.

    - Windows: %APPDATA%\\eagleclasslists
    - macOS: ~/Library/Application Support/eagleclasslists
    - Linux/other: ~/.config/eagleclasslists
    """
    import sys

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "eagleclasslists"
        return Path.home() / "AppData" / "Roaming" / "eagleclasslists"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "eagleclasslists"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "eagleclasslists"
        return Path.home() / ".config" / "eagleclasslists"


class ColumnMappingStore:
    """Manages persisted column mapping presets.

    Presets are stored as JSON in ``~/.config/eagleclasslists/column_mappings.json``.
    The default preset is always available and cannot be deleted.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or _config_dir()
        self._presets: dict[str, ColumnMappingPreset] = {}
        self._active_preset_name: str = DEFAULT_PRESET_NAME
        self._loaded = False

    @property
    def active_preset(self) -> ColumnMappingPreset:
        """Return the currently active preset, loading from disk if needed."""
        if not self._loaded:
            self.load()
        return self._presets.get(
            self._active_preset_name, DEFAULT_PRESET
        )

    @active_preset.setter
    def active_preset(self, preset: ColumnMappingPreset) -> None:
        if not self._loaded:
            self.load()
        if preset.name not in self._presets:
            self.add_preset(preset)
        self._active_preset_name = preset.name
        self._save_active_name()

    @property
    def active_preset_name(self) -> str:
        return self._active_preset_name

    def set_active_by_name(self, name: str) -> None:
        """Set the active preset by name.

        Raises:
            KeyError: If no preset with the given name exists.
        """
        if not self._loaded:
            self.load()
        if name not in self._presets:
            raise KeyError(f"Preset '{name}' not found")
        self._active_preset_name = name
        self._save_active_name()

    def list_presets(self) -> list[ColumnMappingPreset]:
        """Return all available presets, always including the default."""
        if not self._loaded:
            self.load()
        return list(self._presets.values())

    def get_preset(self, name: str) -> ColumnMappingPreset:
        """Return a preset by name.

        Raises:
            KeyError: If no preset with the given name exists.
        """
        if not self._loaded:
            self.load()
        return self._presets[name]

    def add_preset(self, preset: ColumnMappingPreset) -> None:
        """Add a new preset or update an existing one.

        The default preset cannot be overwritten.

        Raises:
            ValueError: If trying to overwrite the default preset.
        """
        if not self._loaded:
            self.load()
        if preset.name == DEFAULT_PRESET_NAME and DEFAULT_PRESET_NAME in self._presets:
            raise ValueError(f"Cannot overwrite the '{DEFAULT_PRESET_NAME}' preset")
        self._presets[preset.name] = preset
        self._save_presets()

    def delete_preset(self, name: str) -> None:
        """Delete a preset by name.

        The default preset cannot be deleted. If the active preset is deleted,
        the active preset reverts to the default.

        Raises:
            ValueError: If trying to delete the default preset.
            KeyError: If no preset with the given name exists.
        """
        if not self._loaded:
            self.load()
        if name == DEFAULT_PRESET_NAME:
            raise ValueError(f"Cannot delete the '{DEFAULT_PRESET_NAME}' preset")
        if name not in self._presets:
            raise KeyError(f"Preset '{name}' not found")
        del self._presets[name]
        if self._active_preset_name == name:
            self._active_preset_name = DEFAULT_PRESET_NAME
            self._save_active_name()
        self._save_presets()

    def load(self) -> None:
        """Load presets from disk, always ensuring the default is present."""
        if self._loaded:
            return

        self._presets = {DEFAULT_PRESET_NAME: DEFAULT_PRESET.model_copy()}

        presets_file = self._config_dir / "column_mappings.json"
        if presets_file.exists():
            try:
                data = json.loads(presets_file.read_text(encoding="utf-8"))
                for item in data.get("presets", []):
                    preset = ColumnMappingPreset.model_validate(item)
                    self._presets[preset.name] = preset
                self._active_preset_name = data.get("active_preset", DEFAULT_PRESET_NAME)
            except (json.JSONDecodeError, pydantic.ValidationError):
                pass

        if self._active_preset_name not in self._presets:
            self._active_preset_name = DEFAULT_PRESET_NAME

        self._loaded = True

    def _save_presets(self) -> None:
        """Persist custom presets (not the default) to disk."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        presets_file = self._config_dir / "column_mappings.json"
        custom_presets = [
            p.model_dump()
            for name, p in self._presets.items()
            if name != DEFAULT_PRESET_NAME
        ]
        data = {
            "active_preset": self._active_preset_name,
            "presets": custom_presets,
        }
        presets_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _save_active_name(self) -> None:
        """Persist just the active preset selection."""
        self._save_presets()


def rename_records_for_reading(
    records: list[dict[str, Any]],
    column_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Rename dict keys from Excel column headers to Python attribute names.

    Args:
        records: Raw records read from Excel (keys are Excel column headers).
        column_map: Mapping from attribute name to Excel column header.

    Returns:
        Records with keys renamed to Python attribute names.
    """
    reverse_map = {v: k for k, v in column_map.items()}
    return [
        {reverse_map.get(key, key): value for key, value in record.items()}
        for record in records
    ]


def rename_records_for_writing(
    records: list[dict[str, Any]],
    column_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Rename dict keys from Python attribute names to Excel column headers.

    Args:
        records: Records with Python attribute name keys (from model_dump).
        column_map: Mapping from attribute name to Excel column header.

    Returns:
        Records with keys renamed to Excel column headers.
    """
    return [
        {column_map.get(key, key): value for key, value in record.items()}
        for record in records
    ]


def alias_to_attr_map(model_class: type[pydantic.BaseModel]) -> dict[str, str]:
    """Build a mapping from Pydantic field alias to Python attribute name.

    Args:
        model_class: A Pydantic BaseModel class with aliased fields.

    Returns:
        Dict mapping alias strings to attribute name strings.
    """
    result: dict[str, str] = {}
    for attr_name, field_info in model_class.model_fields.items():
        alias = field_info.alias or attr_name
        result[alias] = attr_name
    return result
