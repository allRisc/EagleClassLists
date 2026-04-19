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

"""Tests for column mapping presets and persistence."""

from __future__ import annotations

from pathlib import Path

import pydantic
import pytest

from eagleclasslists.settings import (
    DEFAULT_PRESET,
    DEFAULT_PRESET_NAME,
    REQUIRED_CLASSROOM_FIELDS,
    REQUIRED_STUDENT_FIELDS,
    REQUIRED_TEACHER_FIELDS,
    ColumnMappingPreset,
    ColumnMappingStore,
    rename_records_for_reading,
    rename_records_for_writing,
)


class TestColumnMappingPreset:
    """Test suite for ColumnMappingPreset model."""

    def test_default_preset_has_correct_name(self) -> None:
        assert DEFAULT_PRESET.name == "Default"

    def test_default_preset_teacher_columns(self) -> None:
        assert DEFAULT_PRESET.teacher_columns == {
            "name": "Name",
            "clusters": "Clusters",
        }

    def test_default_preset_student_columns(self) -> None:
        assert DEFAULT_PRESET.student_columns == {
            "first_name": "First Name",
            "last_name": "Last Name",
            "gender": "Gender",
            "math": "Math",
            "ela": "ELA",
            "behavior": "Behavior",
            "teacher": "Teacher",
            "cluster": "Cluster",
            "resource": "Resource",
            "speech": "Speech",
            "exclusions": "Exclusions",
        }

    def test_default_preset_classroom_columns(self) -> None:
        assert DEFAULT_PRESET.classroom_columns == {
            "teacher_name": "Teacher Name",
            "student_first_name": "Student First Name",
            "student_last_name": "Student Last Name",
        }

    def test_default_preset_sheet_names(self) -> None:
        assert DEFAULT_PRESET.teachers_sheet == "Teachers"
        assert DEFAULT_PRESET.students_sheet == "Students"
        assert DEFAULT_PRESET.classrooms_sheet == "Classrooms"

    def test_custom_preset_creation(self) -> None:
        preset = ColumnMappingPreset(
            name="Estes Format",
            students_sheet="Student Data",
            student_columns={
                "first_name": "Student First",
                "last_name": "Student Last",
                "gender": "G",
                "math": "Math Level",
                "ela": "ELA Level",
                "behavior": "Behavior Level",
            },
        )
        assert preset.name == "Estes Format"
        assert preset.students_sheet == "Student Data"
        assert preset.student_columns["first_name"] == "Student First"
        assert preset.student_columns["gender"] == "G"
        assert len(preset.student_columns) == 6

    def test_custom_preset_preserves_defaults(self) -> None:
        preset = ColumnMappingPreset(name="Test")
        assert preset.teachers_sheet == "Teachers"
        assert preset.teacher_columns == DEFAULT_PRESET.teacher_columns
        assert preset.classroom_columns == DEFAULT_PRESET.classroom_columns

    def test_reverse_teacher_columns(self) -> None:
        reverse = DEFAULT_PRESET.reverse_teacher_columns()
        assert reverse == {"Name": "name", "Clusters": "clusters"}

    def test_reverse_student_columns(self) -> None:
        reverse = DEFAULT_PRESET.reverse_student_columns()
        assert reverse["First Name"] == "first_name"
        assert reverse["Last Name"] == "last_name"
        assert reverse["Gender"] == "gender"

    def test_reverse_classroom_columns(self) -> None:
        reverse = DEFAULT_PRESET.reverse_classroom_columns()
        assert reverse == {
            "Teacher Name": "teacher_name",
            "Student First Name": "student_first_name",
            "Student Last Name": "student_last_name",
        }

    def test_model_serialization_roundtrip(self) -> None:
        preset = ColumnMappingPreset(
            name="Estes",
            student_columns={
                "first_name": "FName",
                "last_name": "LName",
                "gender": "Sex",
                "math": "M",
                "ela": "E",
                "behavior": "B",
            },
        )
        data = preset.model_dump()
        restored = ColumnMappingPreset.model_validate(data)
        assert restored == preset

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            ColumnMappingPreset(name="Test", unknown_field="value")  # type: ignore[call-arg]


class TestRenameRecords:
    """Test suite for record renaming utilities."""

    def test_rename_for_reading_identity(self) -> None:
        records = [{"First Name": "Alice", "Last Name": "Anderson"}]
        column_map = {"first_name": "First Name", "last_name": "Last Name"}
        result = rename_records_for_reading(records, column_map)
        assert result == [{"first_name": "Alice", "last_name": "Anderson"}]

    def test_rename_for_reading_custom_mapping(self) -> None:
        records = [{"FName": "Alice", "LName": "Anderson"}]
        column_map = {"first_name": "FName", "last_name": "LName"}
        result = rename_records_for_reading(records, column_map)
        assert result == [{"first_name": "Alice", "last_name": "Anderson"}]

    def test_rename_for_reading_preserves_unknown_keys(self) -> None:
        records = [{"First Name": "Alice", "Extra Col": "extra value"}]
        column_map = {"first_name": "First Name", "last_name": "Last Name"}
        result = rename_records_for_reading(records, column_map)
        assert result == [{"first_name": "Alice", "Extra Col": "extra value"}]

    def test_rename_for_reading_empty_records(self) -> None:
        result = rename_records_for_reading([], {"first_name": "First Name"})
        assert result == []

    def test_rename_for_writing_identity(self) -> None:
        records = [{"first_name": "Alice", "last_name": "Anderson"}]
        column_map = {"first_name": "First Name", "last_name": "Last Name"}
        result = rename_records_for_writing(records, column_map)
        assert result == [{"First Name": "Alice", "Last Name": "Anderson"}]

    def test_rename_for_writing_custom_mapping(self) -> None:
        records = [{"first_name": "Alice", "last_name": "Anderson"}]
        column_map = {"first_name": "FName", "last_name": "LName"}
        result = rename_records_for_writing(records, column_map)
        assert result == [{"FName": "Alice", "LName": "Anderson"}]

    def test_rename_for_writing_preserves_unknown_keys(self) -> None:
        records = [{"first_name": "Alice", "extra_field": "extra value"}]
        column_map = {"first_name": "First Name", "last_name": "Last Name"}
        result = rename_records_for_writing(records, column_map)
        assert result == [{"First Name": "Alice", "extra_field": "extra value"}]

    def test_rename_for_writing_empty_records(self) -> None:
        result = rename_records_for_writing([], {"first_name": "First Name"})
        assert result == []

    def test_roundtrip_reading_then_writing(self) -> None:
        column_map = {"first_name": "FName", "last_name": "LName"}
        original = [{"first_name": "Alice", "last_name": "Anderson"}]
        written = rename_records_for_writing(original, column_map)
        read_back = rename_records_for_reading(written, column_map)
        assert read_back == original


class TestColumnMappingStore:
    """Test suite for ColumnMappingStore persistence."""

    def test_load_creates_default_preset(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        presets = store.list_presets()
        assert len(presets) == 1
        assert presets[0].name == DEFAULT_PRESET_NAME

    def test_active_preset_defaults_to_default(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        assert store.active_preset.name == DEFAULT_PRESET_NAME

    def test_add_custom_preset(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        custom = ColumnMappingPreset(
            name="Estes",
            student_columns={
                "first_name": "FName",
                "last_name": "LName",
                "gender": "Sex",
                "math": "M",
                "ela": "E",
                "behavior": "B",
            },
        )
        store.add_preset(custom)
        assert len(store.list_presets()) == 2
        assert store.get_preset("Estes").student_columns["first_name"] == "FName"

    def test_set_active_by_name(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        custom = ColumnMappingPreset(name="Estes")
        store.add_preset(custom)
        store.set_active_by_name("Estes")
        assert store.active_preset_name == "Estes"
        assert store.active_preset.name == "Estes"

    def test_set_active_nonexistent_raises(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        with pytest.raises(KeyError):
            store.set_active_by_name("Nonexistent")

    def test_delete_custom_preset(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        custom = ColumnMappingPreset(name="Estes")
        store.add_preset(custom)
        assert len(store.list_presets()) == 2
        store.delete_preset("Estes")
        assert len(store.list_presets()) == 1

    def test_delete_default_preset_raises(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        with pytest.raises(ValueError):
            store.delete_preset(DEFAULT_PRESET_NAME)

    def test_delete_nonexistent_raises(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        with pytest.raises(KeyError):
            store.delete_preset("Nonexistent")

    def test_overwrite_default_raises(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        new_default = ColumnMappingPreset(name="Default", students_sheet="Custom")
        with pytest.raises(ValueError):
            store.add_preset(new_default)

    def test_persistence_to_disk(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        custom = ColumnMappingPreset(name="Estes", students_sheet="Students Sheet")
        store.add_preset(custom)
        store.set_active_by_name("Estes")

        store2 = ColumnMappingStore(config_dir=tmp_path)
        assert store2.active_preset.name == "Estes"
        assert store2.active_preset.students_sheet == "Students Sheet"
        assert len(store2.list_presets()) == 2

    def test_active_reverts_on_delete(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        custom = ColumnMappingPreset(name="Estes")
        store.add_preset(custom)
        store.set_active_by_name("Estes")
        assert store.active_preset_name == "Estes"

        store.delete_preset("Estes")
        assert store.active_preset_name == DEFAULT_PRESET_NAME

    def test_corrupted_json_falls_back(self, tmp_path: Path) -> None:
        config_dir = tmp_path
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "column_mappings.json").write_text("{invalid json", encoding="utf-8")

        store = ColumnMappingStore(config_dir=config_dir)
        assert store.active_preset.name == DEFAULT_PRESET_NAME
        assert len(store.list_presets()) == 1

    def test_active_preset_setter(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        custom = ColumnMappingPreset(name="Estes")
        store.active_preset = custom
        assert store.active_preset_name == "Estes"
        assert store.active_preset.name == "Estes"

    def test_get_preset_by_name(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        assert store.get_preset(DEFAULT_PRESET_NAME).name == DEFAULT_PRESET_NAME

    def test_get_nonexistent_preset_raises(self, tmp_path: Path) -> None:
        store = ColumnMappingStore(config_dir=tmp_path)
        with pytest.raises(KeyError):
            store.get_preset("Nonexistent")


class TestRequiredFields:
    """Test that required field constants are defined correctly."""

    def test_required_student_fields(self) -> None:
        assert REQUIRED_STUDENT_FIELDS == {
            "first_name", "last_name", "gender", "math", "ela", "behavior"
        }

    def test_required_teacher_fields(self) -> None:
        assert REQUIRED_TEACHER_FIELDS == {"name"}

    def test_required_classroom_fields(self) -> None:
        assert REQUIRED_CLASSROOM_FIELDS == {
            "teacher_name", "student_first_name", "student_last_name"
        }
