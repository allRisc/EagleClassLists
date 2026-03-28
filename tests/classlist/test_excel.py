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

"""Tests for Excel save and load functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from eagleclasslists.classlist import (
    Academics,
    Behavior,
    Classroom,
    Cluster,
    Gender,
    GradeList,
    Student,
    Teacher,
)


class TestExcelSaveAndLoad:
    """Test suite for save_to_excel and from_excel methods."""

    @pytest.fixture
    def sample_grade_list(self) -> GradeList:
        """Create a sample GradeList with complete data for testing."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.AC, Cluster.EL])
        teacher2 = Teacher(name="Mr. Jones", clusters=[Cluster.GEM])

        student1 = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            academics=Academics.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
            resource=True,
            speech=False,
        )

        student2 = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
            cluster=None,
            resource=False,
            speech=True,
        )

        student3 = Student(
            first_name="Charlie",
            last_name="Clark",
            gender=Gender.MALE,
            academics=Academics.LOW,
            behavior=Behavior.LOW,
            cluster=Cluster.EL,
            resource=True,
            speech=True,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student1, student2])
        classroom2 = Classroom(teacher=teacher2, students=[student3])

        return GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[student1, student2, student3],
        )

    @pytest.fixture
    def temp_excel_file(self, tmp_path: Path) -> Path:
        """Create a temporary Excel file path."""
        return tmp_path / "test_grade.xlsx"

    def test_roundtrip_save_and_load(
        self, sample_grade_list: GradeList, temp_excel_file: Path
    ) -> None:
        """Test that saving and loading preserves all data correctly."""
        sample_grade_list.save_to_excel(temp_excel_file)
        loaded = GradeList.from_excel(temp_excel_file)

        # Verify counts
        assert len(loaded.teachers) == 2
        assert len(loaded.students) == 3
        assert len(loaded.classes) == 2

    def test_teacher_data_preserved(
        self, sample_grade_list: GradeList, temp_excel_file: Path
    ) -> None:
        """Test that teacher names and clusters are preserved."""
        sample_grade_list.save_to_excel(temp_excel_file)
        loaded = GradeList.from_excel(temp_excel_file)

        teacher_names = {t.name for t in loaded.teachers}
        assert "Ms. Smith" in teacher_names
        assert "Mr. Jones" in teacher_names

        smith = next(t for t in loaded.teachers if t.name == "Ms. Smith")
        assert Cluster.AC in smith.clusters
        assert Cluster.EL in smith.clusters

    def test_student_data_preserved(
        self, sample_grade_list: GradeList, temp_excel_file: Path
    ) -> None:
        """Test that all student attributes are preserved."""
        sample_grade_list.save_to_excel(temp_excel_file)
        loaded = GradeList.from_excel(temp_excel_file)

        alice = next(
            s for s in loaded.students if s.first_name == "Alice" and s.last_name == "Anderson"
        )
        assert alice.gender == Gender.FEMALE
        assert alice.academics == Academics.HIGH
        assert alice.behavior == Behavior.HIGH
        assert alice.cluster == Cluster.GEM
        assert alice.resource is True
        assert alice.speech is False

    def test_classroom_structure_preserved(
        self, sample_grade_list: GradeList, temp_excel_file: Path
    ) -> None:
        """Test that classroom assignments are preserved."""
        sample_grade_list.save_to_excel(temp_excel_file)
        loaded = GradeList.from_excel(temp_excel_file)

        # Find Ms. Smith's classroom
        smith_class = next(c for c in loaded.classes if c.teacher.name == "Ms. Smith")
        student_names = {(s.first_name, s.last_name) for s in smith_class.students}
        assert ("Alice", "Anderson") in student_names
        assert ("Bob", "Brown") in student_names

    def test_empty_grade_list(self, tmp_path: Path) -> None:
        """Test handling of empty grade list."""
        empty_grade = GradeList(classes=[], teachers=[], students=[])
        excel_file = tmp_path / "empty.xlsx"

        empty_grade.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        assert len(loaded.teachers) == 0
        assert len(loaded.students) == 0
        assert len(loaded.classes) == 0

    def test_single_classroom_single_student(self, tmp_path: Path) -> None:
        """Test with minimal data - one teacher, one student."""
        teacher = Teacher(name="Solo Teacher", clusters=[])
        student = Student(
            first_name="Solo",
            last_name="Student",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "single.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        assert len(loaded.teachers) == 1
        assert len(loaded.students) == 1
        assert len(loaded.classes) == 1
        assert loaded.teachers[0].name == "Solo Teacher"
        assert loaded.students[0].first_name == "Solo"

    def test_student_without_cluster(self, tmp_path: Path) -> None:
        """Test student with no cluster assignment."""
        teacher = Teacher(name="Test Teacher", clusters=[])
        student = Student(
            first_name="No",
            last_name="Cluster",
            gender=Gender.FEMALE,
            academics=Academics.HIGH,
            behavior=Behavior.HIGH,
            cluster=None,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "no_cluster.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        loaded_student = loaded.students[0]
        assert loaded_student.cluster is None

    def test_multiple_clusters_per_teacher(self, tmp_path: Path) -> None:
        """Test teacher with multiple cluster qualifications."""
        teacher = Teacher(name="Multi Cluster", clusters=[Cluster.AC, Cluster.GEM, Cluster.EL])
        student = Student(
            first_name="Test",
            last_name="Student",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "multi_cluster.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        loaded_teacher = loaded.teachers[0]
        assert len(loaded_teacher.clusters) == 3
        assert all(c in loaded_teacher.clusters for c in [Cluster.AC, Cluster.GEM, Cluster.EL])

    def test_teacher_without_clusters(self, tmp_path: Path) -> None:
        """Test teacher with no cluster qualifications."""
        teacher = Teacher(name="No Clusters", clusters=[])
        student = Student(
            first_name="Test",
            last_name="Student",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "no_clusters.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        loaded_teacher = loaded.teachers[0]
        assert len(loaded_teacher.clusters) == 0

    def test_special_characters_in_names(self, tmp_path: Path) -> None:
        """Test handling of special characters in names."""
        teacher = Teacher(name="O'Connor-Smith", clusters=[])
        student = Student(
            first_name="José",
            last_name="García-Muñoz",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "special_chars.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        assert loaded.teachers[0].name == "O'Connor-Smith"
        assert loaded.students[0].first_name == "José"
        assert loaded.students[0].last_name == "García-Muñoz"

    def test_all_enum_values(self, tmp_path: Path) -> None:
        """Test all combinations of enum values are preserved correctly."""
        teacher = Teacher(name="Test", clusters=[])

        students = []
        for gender in Gender:
            for academics in Academics:
                for behavior in Behavior:
                    student = Student(
                        first_name=f"{gender.value}",
                        last_name=f"{academics.value}_{behavior.value}",
                        gender=gender,
                        academics=academics,
                        behavior=behavior,
                    )
                    students.append(student)

        classroom = Classroom(teacher=teacher, students=students)
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=students)

        excel_file = tmp_path / "enums.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        for student in loaded.students:
            expected_gender = Gender(student.first_name)
            academics_str, behavior_str = student.last_name.split("_")
            expected_academics = Academics(academics_str)
            expected_behavior = Behavior(behavior_str)

            assert student.gender == expected_gender
            assert student.academics == expected_academics
            assert student.behavior == expected_behavior

    def test_boolean_fields_true(self, tmp_path: Path) -> None:
        """Test student with both resource and speech set to True."""
        teacher = Teacher(name="Test", clusters=[])
        student = Student(
            first_name="Both",
            last_name="True",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
            resource=True,
            speech=True,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "both_true.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        loaded_student = loaded.students[0]
        assert loaded_student.resource is True
        assert loaded_student.speech is True

    def test_boolean_fields_false(self, tmp_path: Path) -> None:
        """Test student with both resource and speech set to False."""
        teacher = Teacher(name="Test", clusters=[])
        student = Student(
            first_name="Both",
            last_name="False",
            gender=Gender.MALE,
            academics=Academics.MEDIUM,
            behavior=Behavior.MEDIUM,
            resource=False,
            speech=False,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        excel_file = tmp_path / "both_false.xlsx"
        grade_list.save_to_excel(excel_file)
        loaded = GradeList.from_excel(excel_file)

        loaded_student = loaded.students[0]
        assert loaded_student.resource is False
        assert loaded_student.speech is False
