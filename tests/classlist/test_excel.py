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

"""Tests for per-entity Excel save and load functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from eagleclasslists.classlist import (
    ELA,
    Behavior,
    Classroom,
    Cluster,
    ExcelImportError,
    Gender,
    GradeList,
    Math,
    Student,
    Teacher,
)
from eagleclasslists.settings import ColumnMappingPreset


class TestTeachersExcel:
    """Test suite for teachers-only Excel save/load."""

    @pytest.fixture
    def sample_teachers(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", clusters=[Cluster.AC, Cluster.EL]),
            Teacher(name="Mr. Jones", clusters=[Cluster.GEM]),
        ]

    def test_roundtrip_teachers(self, sample_teachers: list[Teacher], tmp_path: Path) -> None:
        grade_list = GradeList(teachers=sample_teachers, students=[])
        filepath = tmp_path / "teachers.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)

        assert len(loaded) == 2
        names = {t.name for t in loaded}
        assert "Ms. Smith" in names
        assert "Mr. Jones" in names

        smith = next(t for t in loaded if t.name == "Ms. Smith")
        assert Cluster.AC in smith.clusters
        assert Cluster.EL in smith.clusters

    def test_empty_teachers(self, tmp_path: Path) -> None:
        grade_list = GradeList(teachers=[], students=[])
        filepath = tmp_path / "empty_teachers.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)
        assert len(loaded) == 0

    def test_teacher_without_clusters(self, tmp_path: Path) -> None:
        teacher = Teacher(name="No Clusters", clusters=[])
        grade_list = GradeList(teachers=[teacher], students=[])
        filepath = tmp_path / "no_clusters.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)
        assert len(loaded) == 1
        assert loaded[0].name == "No Clusters"
        assert len(loaded[0].clusters) == 0

    def test_multiple_clusters_per_teacher(self, tmp_path: Path) -> None:
        teacher = Teacher(name="Multi Cluster", clusters=[Cluster.AC, Cluster.GEM, Cluster.EL])
        grade_list = GradeList(teachers=[teacher], students=[])
        filepath = tmp_path / "multi_cluster.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)
        assert len(loaded[0].clusters) == 3
        assert all(c in loaded[0].clusters for c in [Cluster.AC, Cluster.GEM, Cluster.EL])

    def test_special_characters_in_teacher_names(self, tmp_path: Path) -> None:
        teacher = Teacher(name="O'Connor-Smith", clusters=[])
        grade_list = GradeList(teachers=[teacher], students=[])
        filepath = tmp_path / "special_names.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)
        assert loaded[0].name == "O'Connor-Smith"

    def test_invalid_teacher_data(self, tmp_path: Path) -> None:
        import pandas as pd

        filepath = tmp_path / "invalid.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            df = pd.DataFrame({"Clusters": ["AC"]})
            df.to_excel(writer, sheet_name="Teachers", index=False)

        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_teachers_from_excel(filepath)
        assert "validation failed" in str(exc_info.value).lower()


class TestStudentsExcel:
    """Test suite for students-only Excel save/load."""

    @pytest.fixture
    def sample_students(self) -> list[Student]:
        return [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
                cluster=Cluster.GEM,
                resource=True,
                speech=False,
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
                cluster=None,
                resource=False,
                speech=True,
            ),
            Student(
                first_name="Charlie",
                last_name="Clark",
                gender=Gender.MALE,
                math=Math.LOW,
                ela=ELA.LOW,
                behavior=Behavior.LOW,
                cluster=Cluster.EL,
                resource=True,
                speech=True,
            ),
        ]

    def test_roundtrip_students(self, sample_students: list[Student], tmp_path: Path) -> None:
        grade_list = GradeList(teachers=[], students=sample_students)
        filepath = tmp_path / "students.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        assert len(loaded) == 3

        alice = next(s for s in loaded if s.first_name == "Alice" and s.last_name == "Anderson")
        assert alice.gender == Gender.FEMALE
        assert alice.math == Math.HIGH
        assert alice.ela == ELA.HIGH
        assert alice.behavior == Behavior.HIGH
        assert alice.cluster == Cluster.GEM
        assert alice.resource is True
        assert alice.speech is False

    def test_empty_students(self, tmp_path: Path) -> None:
        grade_list = GradeList(teachers=[], students=[])
        filepath = tmp_path / "empty_students.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)
        assert len(loaded) == 0

    def test_student_without_cluster(self, tmp_path: Path) -> None:
        student = Student(
            first_name="No",
            last_name="Cluster",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=None,
        )
        grade_list = GradeList(teachers=[], students=[student])
        filepath = tmp_path / "no_cluster.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)
        assert loaded[0].cluster is None

    def test_boolean_fields_true(self, tmp_path: Path) -> None:
        student = Student(
            first_name="Both",
            last_name="Name",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
            resource=True,
            speech=True,
        )
        grade_list = GradeList(teachers=[], students=[student])
        filepath = tmp_path / "both_true.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)
        assert loaded[0].resource is True
        assert loaded[0].speech is True

    def test_boolean_fields_false(self, tmp_path: Path) -> None:
        student = Student(
            first_name="Both",
            last_name="Name",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
            resource=False,
            speech=False,
        )
        grade_list = GradeList(teachers=[], students=[student])
        filepath = tmp_path / "both_false.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)
        assert loaded[0].resource is False
        assert loaded[0].speech is False

    def test_all_enum_values(self, tmp_path: Path) -> None:
        students = []
        for gender in Gender:
            for math in Math:
                for ela in ELA:
                    for behavior in Behavior:
                        student = Student(
                            first_name=f"{gender.value}",
                            last_name=f"{math.value}_{ela.value}_{behavior.value}",
                            gender=gender,
                            math=math,
                            ela=ela,
                            behavior=behavior,
                        )
                        students.append(student)

        grade_list = GradeList(teachers=[], students=students)
        filepath = tmp_path / "enums.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        for student in loaded:
            expected_gender = Gender(student.first_name)
            math_str, ela_str, behavior_str = student.last_name.split("_")
            assert student.gender == expected_gender
            assert student.math == Math(math_str)
            assert student.ela == ELA(ela_str)
            assert student.behavior == Behavior(behavior_str)

    def test_special_characters_in_names(self, tmp_path: Path) -> None:
        student = Student(
            first_name="Jose",
            last_name="Garcia-Munoz",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
        )
        grade_list = GradeList(teachers=[], students=[student])
        filepath = tmp_path / "special_chars.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)
        assert loaded[0].first_name == "Jose"
        assert loaded[0].last_name == "Garcia-Munoz"

    def test_invalid_student_data(self, tmp_path: Path) -> None:
        import pandas as pd

        filepath = tmp_path / "invalid.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            df = pd.DataFrame({
                "First Name": ["Alice"],
                "Last Name": ["Anderson"],
                "Gender": ["InvalidValue"],
                "Math": ["High"],
                "ELA": ["High"],
                "Behavior": ["High"],
            })
            df.to_excel(writer, sheet_name="Students", index=False)

        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_students_from_excel(filepath)
        assert "validation failed" in str(exc_info.value).lower()


class TestClassroomsExcel:
    """Test suite for classrooms-only Excel save/load."""

    @pytest.fixture
    def sample_teachers(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", clusters=[Cluster.AC, Cluster.EL]),
            Teacher(name="Mr. Jones", clusters=[Cluster.GEM]),
        ]

    @pytest.fixture
    def sample_students(self) -> list[Student]:
        return [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            ),
            Student(
                first_name="Charlie",
                last_name="Clark",
                gender=Gender.MALE,
                math=Math.LOW,
                ela=ELA.LOW,
                behavior=Behavior.LOW,
            ),
        ]

    def test_roundtrip_classrooms(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        classroom1 = Classroom(
            teacher=sample_teachers[0],
            students=[sample_students[0], sample_students[1]],
        )
        classroom2 = Classroom(teacher=sample_teachers[1], students=[sample_students[2]])
        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=sample_teachers,
            students=sample_students,
        )

        filepath = tmp_path / "classrooms.xlsx"
        grade_list.save_classrooms_to_excel(filepath)
        loaded = GradeList.load_classrooms_from_excel(
            filepath, sample_teachers, sample_students
        )

        assert len(loaded) == 2

        smith_class = next(c for c in loaded if c.teacher.name == "Ms. Smith")
        names = {(s.first_name, s.last_name) for s in smith_class.students}
        assert ("Alice", "Anderson") in names
        assert ("Bob", "Brown") in names

    def test_empty_classrooms(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        grade_list = GradeList(teachers=sample_teachers, students=sample_students)
        filepath = tmp_path / "empty_classrooms.xlsx"
        grade_list.save_classrooms_to_excel(filepath)
        loaded = GradeList.load_classrooms_from_excel(
            filepath, sample_teachers, sample_students
        )
        assert len(loaded) == 0

    def test_single_classroom_single_student(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        classroom = Classroom(teacher=sample_teachers[0], students=[sample_students[0]])
        grade_list = GradeList(
            classes=[classroom],
            teachers=sample_teachers,
            students=sample_students,
        )
        filepath = tmp_path / "single.xlsx"
        grade_list.save_classrooms_to_excel(filepath)
        loaded = GradeList.load_classrooms_from_excel(
            filepath, sample_teachers, sample_students
        )
        assert len(loaded) == 1
        assert loaded[0].teacher.name == "Ms. Smith"
        assert len(loaded[0].students) == 1

    def test_missing_teacher_reference(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        import pandas as pd

        filepath = tmp_path / "bad_teacher.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            df = pd.DataFrame({
                "Teacher Name": ["Unknown Teacher"],
                "Student First Name": ["Alice"],
                "Student Last Name": ["Anderson"],
            })
            df.to_excel(writer, sheet_name="Classrooms", index=False)

        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_classrooms_from_excel(filepath, sample_teachers, sample_students)
        assert "not found" in str(exc_info.value).lower()

    def test_missing_student_reference(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        import pandas as pd

        filepath = tmp_path / "bad_student.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            df = pd.DataFrame({
                "Teacher Name": ["Ms. Smith"],
                "Student First Name": ["Unknown"],
                "Student Last Name": ["Student"],
            })
            df.to_excel(writer, sheet_name="Classrooms", index=False)

        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_classrooms_from_excel(filepath, sample_teachers, sample_students)
        assert "not found" in str(exc_info.value).lower()


class TestExclusionsExcel:
    """Test suite for exclusions field in Excel save/load."""

    def test_student_with_single_exclusion(self, tmp_path: Path) -> None:
        student_with_exclusion = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )
        other_student = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
        )
        grade_list = GradeList(
            teachers=[],
            students=[student_with_exclusion, other_student],
        )

        filepath = tmp_path / "single_exclusion.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        loaded_student = next(
            s for s in loaded if s.first_name == "Alice" and s.last_name == "Anderson"
        )
        assert len(loaded_student.exclusions) == 1
        assert "Bob Brown" in loaded_student.exclusions

    def test_student_with_multiple_exclusions(self, tmp_path: Path) -> None:
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown", "Charlie Clark", "David Davis"],
        )
        grade_list = GradeList(teachers=[], students=[student])

        filepath = tmp_path / "multiple_exclusions.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        assert len(loaded[0].exclusions) == 3
        assert "Bob Brown" in loaded[0].exclusions
        assert "Charlie Clark" in loaded[0].exclusions
        assert "David Davis" in loaded[0].exclusions

    def test_student_without_exclusions(self, tmp_path: Path) -> None:
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=[],
        )
        grade_list = GradeList(teachers=[], students=[student])

        filepath = tmp_path / "no_exclusions.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        assert len(loaded[0].exclusions) == 0

    def test_exclusions_with_special_characters(self, tmp_path: Path) -> None:
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Jose Garcia-Munoz", "O'Connor Smith"],
        )
        grade_list = GradeList(teachers=[], students=[student])

        filepath = tmp_path / "special_chars_exclusions.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        assert len(loaded[0].exclusions) == 2
        assert "Jose Garcia-Munoz" in loaded[0].exclusions
        assert "O'Connor Smith" in loaded[0].exclusions

    def test_exclusions_parsed_from_comma_string(self, tmp_path: Path) -> None:
        import pandas as pd

        filepath = tmp_path / "exclusions_string.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            students_df = pd.DataFrame(
                {
                    "First Name": ["Alice", "Bob"],
                    "Last Name": ["Anderson", "Brown"],
                    "Gender": ["Female", "Male"],
                    "Math": ["High", "Medium"],
                    "ELA": ["High", "Medium"],
                    "Behavior": ["High", "Medium"],
                    "Exclusions": ["Bob Brown, Charlie Clark", ""],
                }
            )
            students_df.to_excel(writer, sheet_name="Students", index=False)

        loaded = GradeList.load_students_from_excel(filepath)

        alice = next(
            s for s in loaded if s.first_name == "Alice" and s.last_name == "Anderson"
        )
        assert len(alice.exclusions) == 2
        assert "Bob Brown" in alice.exclusions
        assert "Charlie Clark" in alice.exclusions

        bob = next(s for s in loaded if s.first_name == "Bob" and s.last_name == "Brown")
        assert len(bob.exclusions) == 0


class TestExcelImportError:
    """Test suite for ExcelImportError exception."""

    def test_excel_import_error_attributes(self) -> None:
        error = ExcelImportError("Test message", "Test details")
        assert error.message == "Test message"
        assert error.details == "Test details"
        assert str(error) == "Test message"

    def test_excel_import_error_no_details(self) -> None:
        error = ExcelImportError("Test message")
        assert error.message == "Test message"
        assert error.details is None
        assert str(error) == "Test message"

    def test_file_not_found_teachers(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.xlsx"
        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_teachers_from_excel(missing)
        assert "not found" in str(exc_info.value).lower()

    def test_file_not_found_students(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.xlsx"
        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_students_from_excel(missing)
        assert "not found" in str(exc_info.value).lower()

    def test_file_not_found_classrooms(
        self,
        tmp_path: Path,
    ) -> None:
        missing = tmp_path / "does_not_exist.xlsx"
        with pytest.raises(ExcelImportError) as exc_info:
            GradeList.load_classrooms_from_excel(missing, [], [])
        assert "not found" in str(exc_info.value).lower()


ESTES_PRESET = ColumnMappingPreset(
    name="Estes Format",
    teachers_sheet="Teachers",
    students_sheet="Student Data",
    classrooms_sheet="Classes",
    teacher_columns={
        "name": "Teacher Name",
        "clusters": "Qualifications",
    },
    student_columns={
        "first_name": "FName",
        "last_name": "LName",
        "gender": "Sex",
        "math": "Math Level",
        "ela": "ELA Level",
        "behavior": "Behavior Level",
        "teacher": "Requested Teacher",
        "cluster": "Program",
        "resource": "Resource",
        "speech": "Speech",
        "exclusions": "Cannot Be With",
    },
    classroom_columns={
        "teacher_name": "Instructor",
        "student_first_name": "Stu First",
        "student_last_name": "Stu Last",
    },
)


class TestCustomPresetTeachers:
    """Test teachers roundtrip with a custom column mapping preset."""

    @pytest.fixture
    def sample_teachers(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", clusters=[Cluster.AC, Cluster.EL]),
            Teacher(name="Mr. Jones", clusters=[Cluster.GEM]),
        ]

    def test_roundtrip_teachers_custom_preset(
        self, sample_teachers: list[Teacher], tmp_path: Path
    ) -> None:
        grade_list = GradeList(teachers=sample_teachers, students=[])
        filepath = tmp_path / "teachers_custom.xlsx"
        grade_list.save_teachers_to_excel(filepath, preset=ESTES_PRESET)
        loaded = GradeList.load_teachers_from_excel(filepath, preset=ESTES_PRESET)

        assert len(loaded) == 2
        names = {t.name for t in loaded}
        assert "Ms. Smith" in names
        assert "Mr. Jones" in names

        smith = next(t for t in loaded if t.name == "Ms. Smith")
        assert Cluster.AC in smith.clusters
        assert Cluster.EL in smith.clusters

    def test_custom_preset_uses_custom_sheet_name(
        self, sample_teachers: list[Teacher], tmp_path: Path
    ) -> None:
        import pandas as pd

        grade_list = GradeList(teachers=sample_teachers, students=[])
        filepath = tmp_path / "teachers_custom.xlsx"
        grade_list.save_teachers_to_excel(filepath, preset=ESTES_PRESET)

        with pd.ExcelFile(filepath) as ef:
            assert "Teachers" in ef.sheet_names

    def test_custom_preset_uses_custom_column_headers(
        self, sample_teachers: list[Teacher], tmp_path: Path
    ) -> None:
        import pandas as pd

        grade_list = GradeList(teachers=sample_teachers, students=[])
        filepath = tmp_path / "teachers_custom.xlsx"
        grade_list.save_teachers_to_excel(filepath, preset=ESTES_PRESET)

        df = pd.read_excel(filepath, sheet_name="Teachers")
        assert "Teacher Name" in df.columns
        assert "Qualifications" in df.columns
        assert "Name" not in df.columns
        assert "Clusters" not in df.columns


class TestCustomPresetStudents:
    """Test students roundtrip with a custom column mapping preset."""

    @pytest.fixture
    def sample_students(self) -> list[Student]:
        return [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
                cluster=Cluster.GEM,
                resource=True,
                speech=False,
                exclusions=["Bob Brown"],
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            ),
        ]

    def test_roundtrip_students_custom_preset(
        self, sample_students: list[Student], tmp_path: Path
    ) -> None:
        grade_list = GradeList(teachers=[], students=sample_students)
        filepath = tmp_path / "students_custom.xlsx"
        grade_list.save_students_to_excel(filepath, preset=ESTES_PRESET)
        loaded = GradeList.load_students_from_excel(filepath, preset=ESTES_PRESET)

        assert len(loaded) == 2

        alice = next(s for s in loaded if s.first_name == "Alice")
        assert alice.gender == Gender.FEMALE
        assert alice.math == Math.HIGH
        assert alice.cluster == Cluster.GEM
        assert alice.resource is True
        assert "Bob Brown" in alice.exclusions

    def test_custom_preset_uses_custom_student_sheet_name(
        self, sample_students: list[Student], tmp_path: Path
    ) -> None:
        import pandas as pd

        grade_list = GradeList(teachers=[], students=sample_students)
        filepath = tmp_path / "students_custom.xlsx"
        grade_list.save_students_to_excel(filepath, preset=ESTES_PRESET)

        with pd.ExcelFile(filepath) as ef:
            assert "Student Data" in ef.sheet_names

    def test_custom_preset_uses_custom_student_column_headers(
        self, sample_students: list[Student], tmp_path: Path
    ) -> None:
        import pandas as pd

        grade_list = GradeList(teachers=[], students=sample_students)
        filepath = tmp_path / "students_custom.xlsx"
        grade_list.save_students_to_excel(filepath, preset=ESTES_PRESET)

        df = pd.read_excel(filepath, sheet_name="Student Data")
        assert "FName" in df.columns
        assert "LName" in df.columns
        assert "Sex" in df.columns
        assert "Math Level" in df.columns
        assert "ELA Level" in df.columns
        assert "Behavior Level" in df.columns
        assert "Program" in df.columns
        assert "Cannot Be With" in df.columns
        assert "First Name" not in df.columns
        assert "Last Name" not in df.columns
        assert "Gender" not in df.columns


class TestCustomPresetClassrooms:
    """Test classrooms roundtrip with a custom column mapping preset."""

    @pytest.fixture
    def sample_teachers(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", clusters=[Cluster.AC, Cluster.EL]),
            Teacher(name="Mr. Jones", clusters=[Cluster.GEM]),
        ]

    @pytest.fixture
    def sample_students(self) -> list[Student]:
        return [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            ),
        ]

    def test_roundtrip_classrooms_custom_preset(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        classroom = Classroom(
            teacher=sample_teachers[0],
            students=[sample_students[0], sample_students[1]],
        )
        grade_list = GradeList(
            classes=[classroom],
            teachers=sample_teachers,
            students=sample_students,
        )

        filepath = tmp_path / "classrooms_custom.xlsx"
        grade_list.save_classrooms_to_excel(filepath, preset=ESTES_PRESET)
        loaded = GradeList.load_classrooms_from_excel(
            filepath, sample_teachers, sample_students, preset=ESTES_PRESET
        )

        assert len(loaded) == 1

        smith_class = next(c for c in loaded if c.teacher.name == "Ms. Smith")
        names = {(s.first_name, s.last_name) for s in smith_class.students}
        assert ("Alice", "Anderson") in names
        assert ("Bob", "Brown") in names

    def test_custom_preset_uses_custom_classroom_sheet_and_headers(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
        tmp_path: Path,
    ) -> None:
        import pandas as pd

        classroom = Classroom(teacher=sample_teachers[0], students=[sample_students[0]])
        grade_list = GradeList(
            classes=[classroom],
            teachers=sample_teachers,
            students=sample_students,
        )

        filepath = tmp_path / "classrooms_custom.xlsx"
        grade_list.save_classrooms_to_excel(filepath, preset=ESTES_PRESET)

        with pd.ExcelFile(filepath) as ef:
            assert "Classes" in ef.sheet_names

        df = pd.read_excel(filepath, sheet_name="Classes")
        assert "Instructor" in df.columns
        assert "Stu First" in df.columns
        assert "Stu Last" in df.columns
        assert "Teacher Name" not in df.columns
