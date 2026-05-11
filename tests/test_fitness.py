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

"""Tests for the fitness module."""

from __future__ import annotations

from eagleclasslists.data.classlist import (
    Classroom,
    GradeList,
    Student,
    Teacher,
)
from eagleclasslists.data.types import (
    Academic,
    Behavior,
    Cluster,
    Gender,
)
from eagleclasslists.fitness import (
    FitnessWeights,
    calculate_fitness,
    get_fitness_breakdown,
)


class TestFitnessWeights:
    """Test suite for FitnessWeights dataclass."""

    def test_default_weights(self) -> None:
        """Test that default weights are set correctly."""
        weights = FitnessWeights()
        assert weights.gender == 1.0
        assert weights.math == 0.5
        assert weights.ela == 0.5
        assert weights.behavior == 1.0
        assert weights.resource == 0.5
        assert weights.speech == 0.5
        assert weights.class_size == 1.0

    def test_custom_weights(self) -> None:
        """Test that custom weights can be set."""
        weights = FitnessWeights(
            gender=2.0, math=0.75, ela=0.75, behavior=1.5, resource=1.0, speech=1.0
        )
        assert weights.gender == 2.0
        assert weights.math == 0.75
        assert weights.ela == 0.75
        assert weights.behavior == 1.5
        assert weights.resource == 1.0
        assert weights.speech == 1.0

    def test_total_weight(self) -> None:
        """Test total weight calculation."""
        weights = FitnessWeights()
        expected = 1.0 + 0.5 + 0.5 + 1.0 + 0.5 + 0.5 + 1.0
        assert weights.total_weight() == expected


class TestClusterScore:
    """Test suite for cluster assignment scoring."""

    def test_perfect_cluster_match(self) -> None:
        """Test when all cluster students are with qualified teachers."""
        teacher = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["cluster"] == 1.0

    def test_cluster_mismatch(self) -> None:
        """Test when cluster student is with unqualified teacher."""
        teacher = Teacher(name="Ms. Smith", clusters=[])  # No clusters
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["cluster"] == 0.0

    def test_partial_cluster_mismatch(self) -> None:
        """Test when some cluster students are mismatched."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        student1 = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        student2 = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.MEDIUM,
            ela=Academic.MEDIUM,
            behavior=Behavior.MEDIUM,
            cluster=Cluster.GEM,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student1])  # Correct
        classroom2 = Classroom(teacher=teacher2, students=[student2])  # Wrong

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[student1, student2],
        )

        breakdown = get_fitness_breakdown(grade_list)
        # Binary scoring: any violation results in 0.0
        assert breakdown["cluster"] == 0.0

    def test_no_cluster_students(self) -> None:
        """Test when there are no cluster students."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=None,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["cluster"] == 1.0  # Nothing to violate


class TestTeacherRequestScore:
    """Test suite for teacher request assignment scoring."""

    def test_perfect_teacher_request_match(self) -> None:
        """Test when all students are with their requested teachers."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Ms. Smith",  # Requested teacher
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["teacher_request"] == 1.0

    def test_teacher_request_mismatch(self) -> None:
        """Test when student with teacher request is with wrong teacher."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Ms. Smith",  # Requested Ms. Smith
        )
        # But placed with Mr. Jones
        classroom = Classroom(teacher=teacher2, students=[student])
        grade_list = GradeList(
            classes=[classroom], teachers=[teacher1, teacher2], students=[student]
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["teacher_request"] == 0.0

    def test_partial_teacher_request_mismatch(self) -> None:
        """Test when some students with requests are mismatched."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        student1 = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Ms. Smith",  # Requested Ms. Smith, got Ms. Smith
        )
        student2 = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.MEDIUM,
            ela=Academic.MEDIUM,
            behavior=Behavior.MEDIUM,
            teacher="Ms. Smith",  # Requested Ms. Smith, but got Mr. Jones
        )

        classroom1 = Classroom(teacher=teacher1, students=[student1])  # Correct
        classroom2 = Classroom(teacher=teacher2, students=[student2])  # Wrong

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[student1, student2],
        )

        breakdown = get_fitness_breakdown(grade_list)
        # Binary scoring: any violation results in 0.0
        assert breakdown["teacher_request"] == 0.0

    def test_no_teacher_requests(self) -> None:
        """Test when there are no students with teacher requests."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher=None,  # No teacher request
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["teacher_request"] == 1.0  # Nothing to violate

    def test_teacher_request_causes_zero_fitness(self) -> None:
        """Test that teacher request mismatch causes overall fitness of 0.0."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Ms. Smith",  # Requested Ms. Smith
        )
        # But placed with Mr. Jones
        classroom = Classroom(teacher=teacher2, students=[student])
        grade_list = GradeList(
            classes=[classroom], teachers=[teacher1, teacher2], students=[student]
        )

        # Overall fitness should be 0.0 due to teacher request violation
        fitness = calculate_fitness(grade_list)
        assert fitness == 0.0

    def test_teacher_request_empty_string_treated_as_no_request(self) -> None:
        """Test that empty string teacher is treated as no request."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="",  # Empty string should be treated as no request
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["teacher_request"] == 1.0  # Empty string is no request


class TestGenderBalance:
    """Test suite for gender balance scoring."""

    def test_perfect_gender_balance(self) -> None:
        """Test perfectly balanced gender distribution."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Each classroom has 1 male and 1 female
        students1 = [
            Student(
                first_name="Alice",
                last_name="Anderson",
                gender=Gender.FEMALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            ),
            Student(
                first_name="Bob",
                last_name="Brown",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            ),
        ]
        students2 = [
            Student(
                first_name="Carol",
                last_name="Clark",
                gender=Gender.FEMALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            ),
            Student(
                first_name="David",
                last_name="Davis",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            ),
        ]

        classroom1 = Classroom(teacher=teacher1, students=students1)
        classroom2 = Classroom(teacher=teacher2, students=students2)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students1 + students2,
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["gender"] > 0.9  # Should be very close to perfect

    def test_imbalanced_gender(self) -> None:
        """Test imbalanced gender distribution."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Classroom 1: all females, Classroom 2: all males
        students1 = [
            Student(
                first_name=f"Girl{i}",
                last_name=f"Name{i}",
                gender=Gender.FEMALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(5)
        ]
        students2 = [
            Student(
                first_name=f"Boy{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(5)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students1)
        classroom2 = Classroom(teacher=teacher2, students=students2)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students1 + students2,
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["gender"] < 0.5  # Should be imbalanced


class TestClassSizeBalance:
    """Test suite for class size balance scoring."""

    def test_equal_class_sizes(self) -> None:
        """Test perfectly equal class sizes."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        students1 = [
            Student(
                first_name=f"Student{i}",
                last_name="Smith",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(10)
        ]
        students2 = [
            Student(
                first_name=f"Student{i}",
                last_name="Jones",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(10)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students1)
        classroom2 = Classroom(teacher=teacher2, students=students2)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students1 + students2,
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["class_size"] == 1.0

    def test_unequal_class_sizes(self) -> None:
        """Test unequal class sizes."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        students1 = [
            Student(
                first_name=f"Student{i}",
                last_name="Smith",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(20)
        ]
        students2 = [
            Student(
                first_name=f"Student{i}",
                last_name="Jones",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(5)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students1)
        classroom2 = Classroom(teacher=teacher2, students=students2)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students1 + students2,
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["class_size"] < 1.0
        assert breakdown["class_size"] > 0.0


class TestResourceAndSpeechBalance:
    """Test suite for resource and speech services balance."""

    def test_balanced_resource(self) -> None:
        """Test balanced resource services distribution."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Each classroom has 2 resource students
        students1 = [
            Student(
                first_name=f"Student{i}",
                last_name="Smith",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
                resource=(i < 2),  # First 2 have resource
            )
            for i in range(10)
        ]
        students2 = [
            Student(
                first_name=f"Student{i}",
                last_name="Jones",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
                resource=(i < 2),  # First 2 have resource
            )
            for i in range(10)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students1)
        classroom2 = Classroom(teacher=teacher2, students=students2)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students1 + students2,
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["resource"] > 0.9

    def test_imbalanced_speech(self) -> None:
        """Test imbalanced speech services distribution."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # All speech students in one classroom
        students1 = [
            Student(
                first_name=f"Student{i}",
                last_name="Smith",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
                speech=True,
            )
            for i in range(5)
        ]
        students2 = [
            Student(
                first_name=f"Student{i}",
                last_name="Jones",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
                speech=False,
            )
            for i in range(10)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students1)
        classroom2 = Classroom(teacher=teacher2, students=students2)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students1 + students2,
        )

        breakdown = get_fitness_breakdown(grade_list)
        assert breakdown["speech"] < 0.5


class TestOverallFitness:
    """Test suite for overall fitness calculation."""

    def test_fitness_range(self) -> None:
        """Test that fitness scores are always between 0 and 1."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        fitness = calculate_fitness(grade_list)
        assert 0.0 <= fitness <= 1.0

    def test_empty_grade_list(self) -> None:
        """Test fitness of empty grade list."""
        grade_list = GradeList(classes=[], teachers=[], students=[])
        fitness = calculate_fitness(grade_list)
        assert fitness == 0.0

    def test_custom_weights_affect_score(self) -> None:
        """Test that custom weights change the fitness score."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # One GEM student with wrong teacher (high cluster violation)
        gem_student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        regular_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Academic.MEDIUM,
                ela=Academic.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(6)
        ]

        # Create balanced classrooms without cluster violations
        classroom1 = Classroom(teacher=teacher1, students=[gem_student] + regular_students[:3])
        classroom2 = Classroom(teacher=teacher2, students=regular_students[3:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[gem_student] + regular_students,
        )

        # Test that different weights produce different scores
        # With default weights
        default_fitness = calculate_fitness(grade_list)

        # With gender prioritized (should give different score if gender is imbalanced)
        gender_weights = FitnessWeights(gender=5.0, math=0.05, ela=0.05, behavior=0.1)
        gender_fitness = calculate_fitness(grade_list, gender_weights)

        # Scores should be different with different weight emphasis
        assert default_fitness != gender_fitness


class TestFitnessBreakdown:
    """Test suite for fitness breakdown function."""

    def test_breakdown_structure(self) -> None:
        """Test that breakdown contains all expected keys."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        breakdown = get_fitness_breakdown(grade_list)

        expected_keys = [
            "cluster",
            "teacher_request",
            "gender",
            "math",
            "ela",
            "behavior",
            "resource",
            "speech",
            "class_size",
            "overall",
        ]
        for key in expected_keys:
            assert key in breakdown
            assert 0.0 <= breakdown[key] <= 1.0
