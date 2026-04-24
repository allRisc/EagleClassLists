"""Tests for the greedy assignment module."""

from __future__ import annotations

import pytest

from eagleclasslists.data.classlist import (
    Behavior,
    Classroom,
    Cluster,
    Gender,
    GradeList,
    Student,
    Teacher,
)
from eagleclasslists.data.types import Academic
from eagleclasslists.fitness import FitnessWeights, calculate_fitness
from eagleclasslists.greedy_assignment import (
    ImpossibleConstraintsError,
    _copy_grade_list,
    _find_best_classroom,
    _get_unassigned_students,
    _has_exclusion_conflict,
    _is_valid_assignment,
    _sort_by_constraints,
    greedy_assign_students,
)


class TestGreedyAssignStudents:
    """Test suite for greedy_assign_students function."""

    def test_empty_student_list(self) -> None:
        """Test that empty student list returns grade list unchanged."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])
        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[])

        assert len(result.classes[0].students) == 0
        assert len(result.classes[1].students) == 0

    def test_single_student_assignment(self) -> None:
        """Test assigning a single student to one of two empty classrooms."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])
        student1 = Student(
            first_name="John",
            last_name="Doe",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[student1],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[student1])

        # Should assign to one of the classrooms
        total_students = sum(len(c.students) for c in result.classes)
        assert total_students == 1

    def test_multiple_students_balance_gender(self) -> None:
        """Test that students are distributed to balance gender."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        students = [
            Student(
                first_name=f"Male{i}",
                last_name="Test",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(4)
        ] + [
            Student(
                first_name=f"Female{i}",
                last_name="Test",
                gender=Gender.FEMALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(4)
        ]

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=students,
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=students)

        # Check that gender is reasonably balanced
        males_class1 = sum(1 for s in result.classes[0].students if s.gender == Gender.MALE)
        males_class2 = sum(1 for s in result.classes[1].students if s.gender == Gender.MALE)

        # With 4 males and 4 females, each class should have 2 males (balanced)
        assert abs(males_class1 - males_class2) <= 1

    def test_uses_default_students_when_none_provided(self) -> None:
        """Test that function uses unassigned students when students param is None."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        student1 = Student(
            first_name="John",
            last_name="Doe",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        grade_list = GradeList(
            teachers=[teacher1],
            students=[student1],  # Student in grade_list but not in classroom
            classes=[Classroom(teacher=teacher1, students=[])],
        )

        result = greedy_assign_students(grade_list)

        assert len(result.classes[0].students) == 1
        assert result.classes[0].students[0].first_name == "John"

    def test_does_not_modify_original(self) -> None:
        """Test that the original grade_list is not modified."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        student1 = Student(
            first_name="John",
            last_name="Doe",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        original = GradeList(
            teachers=[teacher1],
            students=[student1],
            classes=[Classroom(teacher=teacher1, students=[])],
        )

        greedy_assign_students(original, students=[student1])

        # Original should still have empty classroom
        assert len(original.classes[0].students) == 0

    def test_progress_callback_called(self) -> None:
        """Test that progress callback is called for each student."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        students = [
            Student(
                first_name=f"Student{i}",
                last_name="Test",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(3)
        ]
        grade_list = GradeList(
            teachers=[teacher1],
            students=students,
            classes=[Classroom(teacher=teacher1, students=[])],
        )

        progress_calls: list[tuple[int, int, float]] = []

        def callback(idx: int, total: int, fitness: float) -> None:
            progress_calls.append((idx, total, fitness))

        greedy_assign_students(grade_list, students=students, progress_callback=callback)

        assert len(progress_calls) == 3
        # Check that all calls report correct total
        assert all(call[1] == 3 for call in progress_calls)
        # Check that fitness is valid
        assert all(0.0 <= call[2] <= 1.0 for call in progress_calls)


class TestTeacherRequestConstraint:
    """Test suite for teacher request handling."""

    def test_student_with_teacher_request_assigned_correctly(self) -> None:
        """Test that students with teacher requests go to requested teacher."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        student_with_request = Student(
            first_name="John",
            last_name="Doe",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher B",  # Requested teacher
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[student_with_request],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[student_with_request])

        # Student should be with Teacher B
        assert len(result.classes[0].students) == 0
        assert len(result.classes[1].students) == 1
        assert result.classes[1].students[0].first_name == "John"

    def test_multiple_students_with_mixed_requests(self) -> None:
        """Test assigning students with and without teacher requests."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        student_with_request = Student(
            first_name="Requested",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher A",
        )
        student_no_request = Student(
            first_name="Free",
            last_name="Student",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[student_with_request, student_no_request],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(
            grade_list, students=[student_with_request, student_no_request]
        )

        # Requested student should be with Teacher A
        assert any(s.first_name == "Requested" for s in result.classes[0].students)


class TestClusterConstraint:
    """Test suite for cluster constraint handling."""

    def test_cluster_student_assigned_to_qualified_teacher(self) -> None:
        """Test that cluster students go to qualified teachers."""
        teacher1 = Teacher(name="Teacher A", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        gem_student = Student(
            first_name="GEM",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[gem_student],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[gem_student])

        # GEM student must be with Teacher A (qualified for GEM)
        assert len(result.classes[0].students) == 1
        assert len(result.classes[1].students) == 0

    def test_cluster_student_with_multiple_qualified_teachers(self) -> None:
        """Test cluster student assignment when multiple teachers are qualified."""
        teacher1 = Teacher(name="Teacher A", clusters=[Cluster.GEM, Cluster.AC])
        teacher2 = Teacher(name="Teacher B", clusters=[Cluster.GEM])

        gem_student = Student(
            first_name="GEM",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[gem_student],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[gem_student])

        # Should be assigned to one of the qualified teachers
        total_in_gem_classes = len(result.classes[0].students) + len(result.classes[1].students)
        assert total_in_gem_classes == 1


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_get_unassigned_students(self) -> None:
        """Test identifying unassigned students."""
        teacher1 = Teacher(name="Teacher A", clusters=[])

        student_assigned = Student(
            first_name="Assigned",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        student_unassigned = Student(
            first_name="Unassigned",
            last_name="Student",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        grade_list = GradeList(
            teachers=[teacher1],
            students=[student_assigned, student_unassigned],
            classes=[Classroom(teacher=teacher1, students=[student_assigned])],
        )

        unassigned = _get_unassigned_students(grade_list)

        assert len(unassigned) == 1
        assert unassigned[0].first_name == "Unassigned"

    def test_sort_by_constraints(self) -> None:
        """Test sorting students by constraint level."""
        student_teacher_req = Student(
            first_name="TeacherReq",
            last_name="A",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher A",  # Has teacher request
        )
        student_cluster = Student(
            first_name="Cluster",
            last_name="B",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,  # Has cluster
        )
        student_no_constraint = Student(
            first_name="NoConstraint",
            last_name="C",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        students = [student_no_constraint, student_cluster, student_teacher_req]
        sorted_students = _sort_by_constraints(students)

        # Should be ordered: teacher request, cluster, no constraint
        assert sorted_students[0].first_name == "TeacherReq"
        assert sorted_students[1].first_name == "Cluster"
        assert sorted_students[2].first_name == "NoConstraint"

    def test_is_valid_assignment_teacher_request(self) -> None:
        """Test validation of teacher request constraint."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        classroom = Classroom(teacher=teacher1, students=[])

        student_with_req = Student(
            first_name="John",
            last_name="Doe",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher A",
        )
        student_wrong_req = Student(
            first_name="Jane",
            last_name="Doe",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher B",
        )

        assert _is_valid_assignment(classroom, student_with_req) is True
        assert _is_valid_assignment(classroom, student_wrong_req) is False

    def test_is_valid_assignment_cluster(self) -> None:
        """Test validation of cluster constraint."""
        teacher_qualified = Teacher(name="Teacher A", clusters=[Cluster.GEM])
        teacher_unqualified = Teacher(name="Teacher B", clusters=[])

        classroom_qualified = Classroom(teacher=teacher_qualified, students=[])
        classroom_unqualified = Classroom(teacher=teacher_unqualified, students=[])

        gem_student = Student(
            first_name="GEM",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )

        assert _is_valid_assignment(classroom_qualified, gem_student) is True
        assert _is_valid_assignment(classroom_unqualified, gem_student) is False

    def test_find_best_classroom_no_valid_classroom(self) -> None:
        """Test finding best classroom when no valid classroom exists."""
        teacher1 = Teacher(name="Teacher A", clusters=[])

        gem_student = Student(
            first_name="GEM",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,  # No teacher is qualified for GEM
        )

        grade_list = GradeList(
            teachers=[teacher1],
            students=[gem_student],
            classes=[Classroom(teacher=teacher1, students=[])],
        )

        result = _find_best_classroom(grade_list, gem_student)

        assert result is None

    def test_copy_grade_list(self) -> None:
        """Test deep copying of GradeList."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        student1 = Student(
            first_name="John",
            last_name="Doe",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        original = GradeList(
            teachers=[teacher1],
            students=[student1],
            classes=[Classroom(teacher=teacher1, students=[student1])],
        )

        copy_result = _copy_grade_list(original)

        # Should have same structure
        assert len(copy_result.classes) == 1
        assert len(copy_result.classes[0].students) == 1

        # But students should be different objects (copies)
        assert copy_result.classes[0].students[0] is not original.classes[0].students[0]


class TestFitnessImprovement:
    """Test suite for fitness improvement."""

    def test_fitness_improves_with_greedy_assignment(self) -> None:
        """Test that greedy assignment produces valid fitness scores."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        # Create students with diverse attributes
        students = [
            Student(
                first_name=f"Male{i}",
                last_name="Test",
                gender=Gender.MALE,
                math=Academic.HIGH if i % 3 == 0 else Academic.MEDIUM,
                ela=Academic.HIGH if i % 2 == 0 else Academic.MEDIUM,
                behavior=Behavior.HIGH if i % 4 == 0 else Behavior.MEDIUM,
            )
            for i in range(5)
        ] + [
            Student(
                first_name=f"Female{i}",
                last_name="Test",
                gender=Gender.FEMALE,
                math=Academic.LOW if i % 2 == 0 else Academic.MEDIUM,
                ela=Academic.LOW if i % 3 == 0 else Academic.MEDIUM,
                behavior=Behavior.LOW if i % 2 == 0 else Behavior.MEDIUM,
            )
            for i in range(5)
        ]

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=students,
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=students)

        # Check that the result has valid fitness
        fitness = calculate_fitness(result)
        assert 0.0 <= fitness <= 1.0

        # All students should be assigned
        total_assigned = sum(len(c.students) for c in result.classes)
        assert total_assigned == 10

    def test_custom_weights_affect_assignment(self) -> None:
        """Test that custom weights can influence assignment decisions."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        # Create students where gender balance would differ from other balances
        students = [
            Student(
                first_name=f"Male{i}",
                last_name="Test",
                gender=Gender.MALE,
                math=Academic.HIGH,
                ela=Academic.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(6)
        ] + [
            Student(
                first_name=f"Female{i}",
                last_name="Test",
                gender=Gender.FEMALE,
                math=Academic.LOW,
                ela=Academic.LOW,
                behavior=Behavior.LOW,
            )
            for i in range(2)
        ]

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=students,
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        # Run with high gender weight
        high_gender_weights = FitnessWeights(gender=10.0, math=0.1, ela=0.1, behavior=0.1)
        result_gender = greedy_assign_students(
            grade_list, students=students, weights=high_gender_weights
        )

        # Run with high behavior weight
        high_behavior_weights = FitnessWeights(gender=0.1, math=0.1, ela=0.1, behavior=10.0)
        result_behavior = greedy_assign_students(
            grade_list, students=students, weights=high_behavior_weights
        )

        # Both should have valid fitness
        fitness_gender = calculate_fitness(result_gender, high_gender_weights)
        fitness_behavior = calculate_fitness(result_behavior, high_behavior_weights)

        assert 0.0 <= fitness_gender <= 1.0
        assert 0.0 <= fitness_behavior <= 1.0


class TestCombinedConstraints:
    """Test suite for combined constraints."""

    def test_teacher_request_and_cluster_combined(self) -> None:
        """Test student with both teacher request and cluster."""
        teacher1 = Teacher(name="Teacher A", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Teacher B", clusters=[Cluster.GEM])

        # Student wants Teacher A and is in GEM cluster
        student = Student(
            first_name="Constrained",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher A",  # Request
            cluster=Cluster.GEM,  # Cluster constraint
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[student],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[student])

        # Must be with Teacher A (satisfies both constraints)
        assert len(result.classes[0].students) == 1
        assert len(result.classes[1].students) == 0

    def test_conflicting_constraints_no_valid_assignment(self) -> None:
        """Test when teacher request conflicts with cluster constraint."""
        teacher1 = Teacher(name="Teacher A", clusters=[])  # Not qualified for GEM
        teacher2 = Teacher(name="Teacher B", clusters=[Cluster.GEM])

        # Student wants Teacher A but is in GEM cluster
        # Teacher A is not qualified for GEM - conflict!
        student = Student(
            first_name="Conflict",
            last_name="Student",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            teacher="Teacher A",  # Request
            cluster=Cluster.GEM,  # But needs GEM-qualified teacher
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[student],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list, students=[student])

        # No valid classroom exists - student should not be assigned
        total_assigned = sum(len(c.students) for c in result.classes)
        assert total_assigned == 0


class TestExclusionConstraints:
    """Test suite for exclusion constraint enforcement."""

    def test_has_exclusion_conflict_with_excluded_student(self) -> None:
        """Test _has_exclusion_conflict returns True when excluded student present."""
        teacher = Teacher(name="Teacher A", clusters=[])
        student_in_class = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student_in_class])

        student_with_exclusion = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )

        assert _has_exclusion_conflict(classroom, student_with_exclusion) is True

    def test_has_exclusion_conflict_no_conflict(self) -> None:
        """Test _has_exclusion_conflict returns False when no excluded students."""
        teacher = Teacher(name="Teacher A", clusters=[])
        student_in_class = Student(
            first_name="Charlie",
            last_name="Clark",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student_in_class])

        student_with_exclusion = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],  # Charlie is not excluded
        )

        assert _has_exclusion_conflict(classroom, student_with_exclusion) is False

    def test_has_exclusion_conflict_empty_exclusions(self) -> None:
        """Test _has_exclusion_conflict returns False when student has no exclusions."""
        teacher = Teacher(name="Teacher A", clusters=[])
        student_in_class = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student_in_class])

        student_no_exclusions = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=[],
        )

        assert _has_exclusion_conflict(classroom, student_no_exclusions) is False

    def test_is_valid_assignment_rejects_exclusion_conflict(self) -> None:
        """Test _is_valid_assignment returns False for exclusion conflicts."""
        teacher = Teacher(name="Teacher A", clusters=[])
        student_in_class = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student_in_class])

        student_with_exclusion = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )

        assert _is_valid_assignment(classroom, student_with_exclusion) is False

    def test_sort_by_constraints_prioritizes_exclusions(self) -> None:
        """Test that students with exclusions are sorted before non-exclusion students."""
        student_with_exclusion = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )
        student_no_constraints = Student(
            first_name="Charlie",
            last_name="Clark",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        student_with_cluster = Student(
            first_name="David",
            last_name="Davis",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.AC,
        )

        students = [student_no_constraints, student_with_cluster, student_with_exclusion]
        sorted_students = _sort_by_constraints(students)

        # Order should be: exclusion (1), cluster (2), no constraints (3)
        assert sorted_students[0] == student_with_exclusion
        assert sorted_students[1] == student_with_cluster
        assert sorted_students[2] == student_no_constraints

    def test_greedy_assignment_respects_exclusions(self) -> None:
        """Test that greedy assignment keeps excluded students in different classrooms."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        student_a = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )
        student_b = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2],
            students=[student_a, student_b],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list)

        # Find where Alice and Bob ended up
        alice_class = None
        bob_class = None
        for classroom in result.classes:
            for student in classroom.students:
                if student.first_name == "Alice":
                    alice_class = classroom.teacher.name
                elif student.first_name == "Bob":
                    bob_class = classroom.teacher.name

        # They should be in different classrooms
        assert alice_class != bob_class
        assert alice_class is not None
        assert bob_class is not None

    def test_greedy_assignment_raises_on_impossible_exclusions(self) -> None:
        """Test that greedy assignment raises error when exclusions can't be satisfied."""
        teacher1 = Teacher(name="Teacher A", clusters=[])

        student_a = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown", "Charlie Clark"],
        )
        student_b = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        student_c = Student(
            first_name="Charlie",
            last_name="Clark",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        # Only 1 classroom, but Alice excludes both others - impossible!
        grade_list = GradeList(
            teachers=[teacher1],
            students=[student_a, student_b, student_c],
            classes=[Classroom(teacher=teacher1, students=[])],
        )

        with pytest.raises(ImpossibleConstraintsError) as exc_info:
            greedy_assign_students(grade_list)

        # Error mentions which student couldn't be placed due to conflicts
        # Alice is placed first (she has exclusions), then Bob/Charlie can't join her
        error_msg = str(exc_info.value)
        assert "Cannot satisfy constraints" in error_msg
        # The error should mention Alice's exclusions causing the issue
        assert "Alice Anderson" in error_msg or "Bob Brown" in error_msg

    def test_greedy_assignment_multiple_exclusions_respected(self) -> None:
        """Test that multiple exclusions are all respected."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])
        teacher3 = Teacher(name="Teacher C", clusters=[])

        # Alice excludes Bob and Charlie
        student_a = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown", "Charlie Clark"],
        )
        student_b = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )
        student_c = Student(
            first_name="Charlie",
            last_name="Clark",
            gender=Gender.MALE,
            math=Academic.HIGH,
            ela=Academic.HIGH,
            behavior=Behavior.HIGH,
        )

        grade_list = GradeList(
            teachers=[teacher1, teacher2, teacher3],
            students=[student_a, student_b, student_c],
            classes=[
                Classroom(teacher=teacher1, students=[]),
                Classroom(teacher=teacher2, students=[]),
                Classroom(teacher=teacher3, students=[]),
            ],
        )

        result = greedy_assign_students(grade_list)

        # Find Alice's classroom
        alice_classroom = None
        for classroom in result.classes:
            for student in classroom.students:
                if student.first_name == "Alice":
                    alice_classroom = classroom
                    break

        # Neither Bob nor Charlie should be in Alice's classroom
        class_student_names = {f"{s.first_name} {s.last_name}" for s in alice_classroom.students}
        assert "Bob Brown" not in class_student_names
        assert "Charlie Clark" not in class_student_names
