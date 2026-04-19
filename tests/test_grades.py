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

"""Tests for multi-grade support in Excel import/export and filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

from eagleclasslists.classlist import (
    ELA,
    Behavior,
    Cluster,
    Gender,
    GradeList,
    Math,
    Student,
    Teacher,
)
from eagleclasslists.settings import (
    ColumnMappingPreset,
)


class TestStudentGradeField:
    """Test the grade field on Student model."""

    def test_student_without_grade(self) -> None:
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.LOW,
        )
        assert student.grade is None

    def test_student_with_grade(self) -> None:
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.LOW,
            grade="3",
        )
        assert student.grade == "3"


class TestTeacherGradeField:
    """Test the grade field on Teacher model."""

    def test_teacher_without_grade(self) -> None:
        teacher = Teacher(name="Ms. Smith", clusters=[Cluster.AC])
        assert teacher.grade is None

    def test_teacher_with_grade(self) -> None:
        teacher = Teacher(name="Ms. Smith", grade="3", clusters=[Cluster.AC])
        assert teacher.grade == "3"


class TestExcelRoundtripWithGrades:
    """Test Excel save/load roundtrip with grade data."""

    @pytest.fixture
    def sample_teachers_with_grades(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", grade="2", clusters=[Cluster.AC, Cluster.EL]),
            Teacher(name="Mr. Jones", grade="3", clusters=[Cluster.GEM]),
            Teacher(name="Mrs. Lee", grade="2", clusters=[Cluster.AC]),
        ]

    @pytest.fixture
    def sample_students_with_grades(self) -> list[Student]:
        return [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.LOW,
                grade="2",
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.LOW,
                ela=ELA.MEDIUM,
                behavior=Behavior.HIGH,
                grade="3",
            ),
            Student(
                first_name="Charlie",
                last_name="Clark",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.LOW,
                behavior=Behavior.MEDIUM,
                grade="2",
            ),
        ]

    def test_teachers_roundtrip_with_grades(
        self,
        sample_teachers_with_grades: list[Teacher],
        tmp_path: Path,
    ) -> None:
        grade_list = GradeList(teachers=sample_teachers_with_grades, students=[])
        filepath = tmp_path / "teachers.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)

        assert len(loaded) == 3
        smith = next(t for t in loaded if t.name == "Ms. Smith")
        assert smith.grade == "2"
        jones = next(t for t in loaded if t.name == "Mr. Jones")
        assert jones.grade == "3"

    def test_students_roundtrip_with_grades(
        self,
        sample_students_with_grades: list[Student],
        tmp_path: Path,
    ) -> None:
        grade_list = GradeList(teachers=[], students=sample_students_with_grades)
        filepath = tmp_path / "students.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        assert len(loaded) == 3
        alice = next(s for s in loaded if s.first_name == "Alice")
        assert alice.grade == "2"
        bob = next(s for s in loaded if s.first_name == "Bob")
        assert bob.grade == "3"

    def test_teachers_roundtrip_without_grades(
        self,
        tmp_path: Path,
    ) -> None:
        teachers = [
            Teacher(name="Ms. Smith", clusters=[Cluster.AC]),
            Teacher(name="Mr. Jones", clusters=[Cluster.GEM]),
        ]
        grade_list = GradeList(teachers=teachers, students=[])
        filepath = tmp_path / "teachers.xlsx"
        grade_list.save_teachers_to_excel(filepath)
        loaded = GradeList.load_teachers_from_excel(filepath)

        assert all(t.grade is None for t in loaded)

    def test_students_roundtrip_without_grades(
        self,
        tmp_path: Path,
    ) -> None:
        students = [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.LOW,
            ),
        ]
        grade_list = GradeList(teachers=[], students=students)
        filepath = tmp_path / "students.xlsx"
        grade_list.save_students_to_excel(filepath)
        loaded = GradeList.load_students_from_excel(filepath)

        assert all(s.grade is None for s in loaded)


class TestCustomPresetWithGrades:
    """Test custom column mapping presets with grade columns."""

    def test_custom_preset_with_custom_grade_column(self) -> None:
        preset = ColumnMappingPreset(
            name="Custom",
            teacher_columns={
                "name": "Teacher",
                "grade": "Grade Level",
                "clusters": "Qualifications",
            },
            student_columns={
                "first_name": "First Name",
                "last_name": "Last Name",
                "gender": "Gender",
                "math": "Math",
                "ela": "ELA",
                "behavior": "Behavior",
                "grade": "Grade Level",
            },
        )
        assert preset.teacher_columns["grade"] == "Grade Level"
        assert preset.student_columns["grade"] == "Grade Level"


class TestGradeListModel:
    """Test grade filtering in GradeListModel."""

    @pytest.fixture
    def sample_teachers(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", grade="2", clusters=[Cluster.AC]),
            Teacher(name="Mr. Jones", grade="3", clusters=[Cluster.GEM]),
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
                behavior=Behavior.LOW,
                grade="2",
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.LOW,
                ela=ELA.MEDIUM,
                behavior=Behavior.HIGH,
                grade="3",
            ),
        ]

    def test_available_grades(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=sample_teachers, students=sample_students)
        model = GradeListModel(grade_list)
        model._all_teachers = sample_teachers
        model._all_students = sample_students

        assert model.available_grades == ["2", "3"]

    def test_has_grade_data(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=sample_teachers, students=sample_students)
        model = GradeListModel(grade_list)
        model._all_teachers = sample_teachers
        model._all_students = sample_students

        assert model.has_grade_data is True

    def test_no_grade_data(self) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        teachers = [Teacher(name="Ms. Smith", clusters=[Cluster.AC])]
        students = [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.LOW,
            ),
        ]
        grade_list = GradeList(teachers=teachers, students=students)
        model = GradeListModel(grade_list)
        model._all_teachers = teachers
        model._all_students = students

        assert model.has_grade_data is False

    def test_filter_by_grade(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=sample_teachers, students=sample_students)
        model = GradeListModel(grade_list)
        model._all_teachers = sample_teachers
        model._all_students = sample_students

        model.set_active_grade("2")

        assert len(model.grade_list.teachers) == 1
        assert model.grade_list.teachers[0].name == "Ms. Smith"
        assert len(model.grade_list.students) == 1
        assert model.grade_list.students[0].first_name == "Alice"

    def test_filter_by_grade_none_shows_all(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=sample_teachers, students=sample_students)
        model = GradeListModel(grade_list)
        model._all_teachers = sample_teachers
        model._all_students = sample_students

        model.set_active_grade(None)

        assert len(model.grade_list.teachers) == 2
        assert len(model.grade_list.students) == 2

    def test_auto_select_smallest_grade(
        self,
        sample_teachers: list[Teacher],
        sample_students: list[Student],
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=[], students=[])
        model = GradeListModel(grade_list)

        model._all_teachers = sample_teachers
        model._all_students = sample_students
        model._auto_select_grade()

        assert model.active_grade == "2"

    def test_auto_select_numeric_before_alpha(self) -> None:
        from eagleclasslists.app.grade_list_model import _sort_grades

        grades = _sort_grades({"K", "1", "2", "10", "A"})
        assert grades == ["1", "2", "10", "A", "K"]

    def test_set_grade_list_clears_all_data(self) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        teachers = [Teacher(name="Ms. Smith", grade="2", clusters=[Cluster.AC])]
        students = [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.LOW,
                grade="2",
            ),
        ]
        grade_list = GradeList(teachers=teachers, students=students)
        model = GradeListModel(grade_list)
        model._all_teachers = teachers
        model._all_students = students
        model._active_grade = "2"

        model.set_grade_list(GradeList(teachers=[], students=[]))

        assert model._all_teachers == []
        assert model._all_students == []
        assert model.active_grade is None
        assert model.has_grade_data is False
        assert model.available_grades == []


class TestGradeListModelWithExcel:
    """Test GradeListModel loading from Excel files with grades."""

    @pytest.fixture
    def sample_teachers_with_grades(self) -> list[Teacher]:
        return [
            Teacher(name="Ms. Smith", grade="2", clusters=[Cluster.AC]),
            Teacher(name="Mr. Jones", grade="3", clusters=[Cluster.GEM]),
        ]

    @pytest.fixture
    def sample_students_with_grades(self) -> list[Student]:
        return [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.LOW,
                grade="2",
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Math.LOW,
                ela=ELA.MEDIUM,
                behavior=Behavior.HIGH,
                grade="3",
            ),
        ]

    def test_load_teachers_from_excel_with_grades(
        self,
        sample_teachers_with_grades: list[Teacher],
        tmp_path: Path,
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=sample_teachers_with_grades, students=[])
        filepath = tmp_path / "teachers.xlsx"
        grade_list.save_teachers_to_excel(filepath)

        model = GradeListModel(GradeList(teachers=[], students=[]))
        model.load_teachers(filepath)

        assert model.has_grade_data is True
        assert model.available_grades == ["2", "3"]
        assert model.active_grade == "2"
        assert len(model.grade_list.teachers) == 1
        assert len(model._all_teachers) == 2

    def test_load_students_from_excel_with_grades(
        self,
        sample_students_with_grades: list[Student],
        tmp_path: Path,
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        grade_list = GradeList(teachers=[], students=sample_students_with_grades)
        filepath = tmp_path / "students.xlsx"
        grade_list.save_students_to_excel(filepath)

        model = GradeListModel(GradeList(teachers=[], students=[]))
        model.load_students(filepath)

        assert model.has_grade_data is True
        assert model.available_grades == ["2", "3"]
        assert model.active_grade == "2"
        assert len(model.grade_list.students) == 1
        assert len(model._all_students) == 2

    def test_switching_grade_updates_grade_list(
        self,
        sample_teachers_with_grades: list[Teacher],
        sample_students_with_grades: list[Student],
        tmp_path: Path,
    ) -> None:
        from eagleclasslists.app.grade_list_model import GradeListModel

        teachers_gl = GradeList(teachers=sample_teachers_with_grades, students=[])
        teachers_path = tmp_path / "teachers.xlsx"
        teachers_gl.save_teachers_to_excel(teachers_path)

        students_gl = GradeList(teachers=[], students=sample_students_with_grades)
        students_path = tmp_path / "students.xlsx"
        students_gl.save_students_to_excel(students_path)

        model = GradeListModel(GradeList(teachers=[], students=[]))
        model.load_teachers(teachers_path)
        model.load_students(students_path)

        assert model.active_grade == "2"
        assert len(model.grade_list.teachers) == 1
        assert len(model.grade_list.students) == 1

        model.set_active_grade("3")

        assert model.active_grade == "3"
        assert len(model.grade_list.teachers) == 1
        assert model.grade_list.teachers[0].name == "Mr. Jones"
        assert len(model.grade_list.students) == 1
        assert model.grade_list.students[0].first_name == "Bob"
