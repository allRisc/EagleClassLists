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

"""Tests for the simulated annealing module."""

from __future__ import annotations

from eagleclasslists.classlist import (
    ELA,
    Behavior,
    Classroom,
    Cluster,
    Gender,
    GradeList,
    Math,
    Student,
    Teacher,
)
from eagleclasslists.fitness import FitnessWeights, calculate_fitness, get_fitness_breakdown
from eagleclasslists.simulated_annealing import (
    AnnealingConfig,
    _copy_grade_list,
    _is_swap_valid,
    optimize_grade_list,
    optimize_multiple_times,
)


class TestAnnealingConfig:
    """Test suite for AnnealingConfig dataclass."""

    def test_default_config(self) -> None:
        """Test that default configuration values are set correctly."""
        config = AnnealingConfig()
        assert config.initial_temperature == 100.0
        assert config.cooling_rate == 0.995
        assert config.min_temperature == 0.001
        assert config.max_iterations == 10000
        assert config.iterations_per_temp == 100
        assert config.random_seed is None

    def test_custom_config(self) -> None:
        """Test that custom configuration can be set."""
        config = AnnealingConfig(
            initial_temperature=50.0,
            cooling_rate=0.99,
            min_temperature=0.01,
            max_iterations=5000,
            iterations_per_temp=50,
            random_seed=42,
        )
        assert config.initial_temperature == 50.0
        assert config.cooling_rate == 0.99
        assert config.min_temperature == 0.01
        assert config.max_iterations == 5000
        assert config.iterations_per_temp == 50
        assert config.random_seed == 42


class TestCopyGradeList:
    """Test suite for GradeList copying."""

    def test_copy_preserves_structure(self) -> None:
        """Test that copying preserves the basic structure."""
        teacher = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        copied = _copy_grade_list(grade_list)

        assert len(copied.classes) == len(grade_list.classes)
        assert len(copied.teachers) == len(grade_list.teachers)
        assert len(copied.students) == len(grade_list.students)
        assert copied.classes[0].teacher.name == teacher.name
        assert copied.classes[0].students[0].first_name == student.first_name

    def test_copy_creates_independent_students(self) -> None:
        """Test that copying creates independent student objects."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
        )
        classroom = Classroom(teacher=teacher, students=[student])
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=[student])

        copied = _copy_grade_list(grade_list)

        # Modify the copy
        copied.classes[0].students[0].first_name = "Bob"

        # Original should be unchanged
        assert grade_list.classes[0].students[0].first_name == "Alice"


class TestSwapValidation:
    """Test suite for swap validation."""

    def test_valid_swap_same_clusters(self) -> None:
        """Test swap between students with same cluster requirements."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[Cluster.GEM])

        student1 = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        student2 = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
            cluster=Cluster.GEM,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student1])
        classroom2 = Classroom(teacher=teacher2, students=[student2])

        assert _is_swap_valid(classroom1, classroom2, student1, student2) is True

    def test_invalid_swap_cluster_mismatch(self) -> None:
        """Test invalid swap when cluster requirements aren't met."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])  # No clusters

        student1 = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        student2 = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
            cluster=None,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student1])
        classroom2 = Classroom(teacher=teacher2, students=[student2])

        # Student1 (GEM) cannot go to Mr. Jones who has no clusters
        assert _is_swap_valid(classroom1, classroom2, student1, student2) is False

    def test_valid_swap_no_clusters(self) -> None:
        """Test swap when neither student has cluster requirements."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[Cluster.GEM])

        student1 = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=None,
        )
        student2 = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.MEDIUM,
            ela=ELA.MEDIUM,
            behavior=Behavior.MEDIUM,
            cluster=None,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student1])
        classroom2 = Classroom(teacher=teacher2, students=[student2])

        # Both students have no cluster requirements, swap should be valid
        assert _is_swap_valid(classroom1, classroom2, student1, student2) is True


class TestSmartNeighborGeneration:
    """Test suite for smart neighbor generation that respects clusters."""

    def test_neighbor_generator_only_produces_valid_swaps(self) -> None:
        """Test that _generate_swap_neighbor only returns valid swaps."""
        from eagleclasslists.simulated_annealing import _generate_swap_neighbor

        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Mix of cluster and non-cluster students
        students = [
            Student(
                first_name="GEM1",
                last_name="Student",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
                cluster=Cluster.GEM,
            ),
            Student(
                first_name="GEM2",
                last_name="Student",
                gender=Gender.MALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
                cluster=Cluster.GEM,
            ),
            Student(
                first_name="Regular1",
                last_name="Student",
                gender=Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
                cluster=None,
            ),
            Student(
                first_name="Regular2",
                last_name="Student",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
                cluster=None,
            ),
        ]

        # Put GEM students with qualified teacher, regular with other
        classroom1 = Classroom(teacher=teacher1, students=students[:2])  # GEM students
        classroom2 = Classroom(teacher=teacher2, students=students[2:])  # Regular students

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students,
        )

        # Generate many neighbors and verify none violate constraints
        for _ in range(50):
            neighbor = _generate_swap_neighbor(grade_list)
            if neighbor is not None:
                # Verify the swap is valid
                for classroom in neighbor.classes:
                    teacher_clusters = set(classroom.teacher.clusters)
                    for student in classroom.students:
                        if student.cluster is not None:
                            assert student.cluster in teacher_clusters, (
                                f"Cluster violation: {student.first_name} "
                                f"({student.cluster.value}) with {classroom.teacher.name}"
                            )

    def test_neighbor_generator_only_produces_valid_moves(self) -> None:
        """Test that _generate_move_neighbor only returns valid moves."""
        from eagleclasslists.simulated_annealing import _generate_move_neighbor

        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        students = [
            Student(
                first_name="GEM1",
                last_name="Student",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
                cluster=Cluster.GEM,
            ),
            Student(
                first_name="Regular1",
                last_name="Student",
                gender=Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
                cluster=None,
            ),
            Student(
                first_name="Regular2",
                last_name="Student",
                gender=Gender.MALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
                cluster=None,
            ),
        ]

        # GEM student with qualified teacher, regular students with other
        classroom1 = Classroom(teacher=teacher1, students=[students[0]])
        classroom2 = Classroom(teacher=teacher2, students=students[1:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students,
        )

        # Generate many neighbors and verify none violate constraints
        for _ in range(50):
            neighbor = _generate_move_neighbor(grade_list)
            if neighbor is not None:
                # Verify the move is valid
                for classroom in neighbor.classes:
                    teacher_clusters = set(classroom.teacher.clusters)
                    for student in classroom.students:
                        if student.cluster is not None:
                            assert student.cluster in teacher_clusters, (
                                f"Cluster violation: {student.first_name} "
                                f"({student.cluster.value}) with {classroom.teacher.name}"
                            )

    def test_cluster_violations_get_fixed(self) -> None:
        """Test that optimization fixes existing cluster violations."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Create a cluster violation
        gem_student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        regular_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(6)
        ]

        # Place GEM student with wrong teacher
        classroom1 = Classroom(teacher=teacher2, students=[gem_student])
        classroom2 = Classroom(teacher=teacher1, students=regular_students)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[gem_student] + regular_students,
        )

        # Verify initial state has violation
        initial_breakdown = get_fitness_breakdown(grade_list)
        assert initial_breakdown["cluster"] == 0.0

        # Optimize - cluster constraint is automatically enforced (hard constraint)
        # Any valid solution must have cluster_score = 1.0
        weights = FitnessWeights(gender=0.0, math=0.0, ela=0.0, behavior=0.0)
        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=1000,
            iterations_per_temp=20,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, weights=weights, config=config)

        # Verify cluster violation is fixed
        final_breakdown = get_fitness_breakdown(optimized)
        assert final_breakdown["cluster"] == 1.0

        # Verify the GEM student is now with the qualified teacher
        gem_class = None
        for classroom in optimized.classes:
            for student in classroom.students:
                if student.cluster == Cluster.GEM:
                    gem_class = classroom
                    break

        assert gem_class is not None
        assert Cluster.GEM in gem_class.teacher.clusters

    def test_neighbor_generator_never_moves_teacher_requested_students(self) -> None:
        """Test that neighbor generation never moves students with teacher requests."""
        from eagleclasslists.simulated_annealing import (
            _generate_move_neighbor,
            _generate_swap_neighbor,
        )

        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Create students - one with a teacher request, others without
        requested_student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            teacher="Ms. Smith",  # Requested to be with Ms. Smith
        )
        regular_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(4)
        ]

        # Place requested student with Ms. Smith (correct)
        classroom1 = Classroom(
            teacher=teacher1, students=[requested_student] + regular_students[:2]
        )
        classroom2 = Classroom(teacher=teacher2, students=regular_students[2:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[requested_student] + regular_students,
        )

        # Generate many neighbors and verify none move the requested student
        for _ in range(50):
            # Try swap neighbor
            swap_neighbor = _generate_swap_neighbor(grade_list)
            if swap_neighbor is not None:
                # Find Alice in the result
                for classroom in swap_neighbor.classes:
                    for student in classroom.students:
                        if student.first_name == "Alice" and student.last_name == "Anderson":
                            # Alice should still be with Ms. Smith
                            assert classroom.teacher.name == "Ms. Smith", (
                                f"Teacher request violated: Alice moved to {classroom.teacher.name}"
                            )

            # Try move neighbor
            move_neighbor = _generate_move_neighbor(grade_list)
            if move_neighbor is not None:
                # Find Alice in the result
                for classroom in move_neighbor.classes:
                    for student in classroom.students:
                        if student.first_name == "Alice" and student.last_name == "Anderson":
                            # Alice should still be with Ms. Smith
                            assert classroom.teacher.name == "Ms. Smith", (
                                f"Teacher request violated: Alice moved to {classroom.teacher.name}"
                            )

    def test_optimization_preserves_teacher_requests(self) -> None:
        """Test that optimization never moves students with teacher requests."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Create a student with a teacher request
        requested_student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            teacher="Ms. Smith",  # Requested to be with Ms. Smith
        )
        regular_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(10)
        ]

        # Place requested student with Ms. Smith
        classroom1 = Classroom(
            teacher=teacher1, students=[requested_student] + regular_students[:5]
        )
        classroom2 = Classroom(teacher=teacher2, students=regular_students[5:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[requested_student] + regular_students,
        )

        # Optimize
        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=500,
            iterations_per_temp=10,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, config=config)

        # Verify Alice is still with Ms. Smith
        alice_class = None
        for classroom in optimized.classes:
            for student in classroom.students:
                if student.first_name == "Alice" and student.last_name == "Anderson":
                    alice_class = classroom
                    break

        assert alice_class is not None
        assert alice_class.teacher.name == "Ms. Smith"

        # Verify teacher request score is still 1.0
        breakdown = get_fitness_breakdown(optimized)
        assert breakdown["teacher_request"] == 1.0


class TestOptimizeGradeList:
    """Test suite for optimize_grade_list function."""

    def test_optimization_improves_fitness(self) -> None:
        """Test that optimization improves fitness score."""
        # Create an imbalanced grade list
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # All males in one class, all females in another
        male_students = [
            Student(
                first_name=f"Boy{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(10)
        ]
        female_students = [
            Student(
                first_name=f"Girl{i}",
                last_name=f"Name{i}",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(10)
        ]

        classroom1 = Classroom(teacher=teacher1, students=male_students)
        classroom2 = Classroom(teacher=teacher2, students=female_students)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=male_students + female_students,
        )

        initial_fitness = calculate_fitness(grade_list)

        # Optimize with reduced iterations for faster testing
        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=500,
            iterations_per_temp=10,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, config=config)
        optimized_fitness = calculate_fitness(optimized)

        # Fitness should improve (or at least not get worse)
        assert optimized_fitness >= initial_fitness

    def test_optimization_preserves_cluster_constraints(self) -> None:
        """Test that optimization respects cluster constraints."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        gem_student = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            cluster=Cluster.GEM,
        )
        regular_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(10)
        ]

        # Place GEM student with Mr. Jones (wrong)
        classroom1 = Classroom(teacher=teacher2, students=[gem_student])
        classroom2 = Classroom(teacher=teacher1, students=regular_students)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[gem_student] + regular_students,
        )

        # Optimize - cluster constraint is automatically enforced
        weights = FitnessWeights()
        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=500,
            iterations_per_temp=10,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, weights=weights, config=config)

        # Check that GEM student is now with qualified teacher
        gem_class = None
        for classroom in optimized.classes:
            for student in classroom.students:
                if student.cluster == Cluster.GEM:
                    gem_class = classroom
                    break

        assert gem_class is not None
        assert Cluster.GEM in gem_class.teacher.clusters

    def test_optimization_preserves_total_students(self) -> None:
        """Test that optimization preserves the total number of students."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(20)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students[:10])
        classroom2 = Classroom(teacher=teacher2, students=students[10:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students,
        )

        initial_count = sum(len(c.students) for c in grade_list.classes)

        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=200,
            iterations_per_temp=5,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, config=config)
        final_count = sum(len(c.students) for c in optimized.classes)

        assert final_count == initial_count

    def test_progress_callback(self) -> None:
        """Test that progress callback is called during optimization."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(10)
        ]

        classroom1 = Classroom(teacher=teacher1, students=students[:5])
        classroom2 = Classroom(teacher=teacher2, students=students[5:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=students,
        )

        progress_calls = []

        def callback(iteration: int, temp: float, fitness: float) -> None:
            progress_calls.append((iteration, temp, fitness))

        config = AnnealingConfig(
            initial_temperature=5.0,
            cooling_rate=0.9,
            min_temperature=0.1,
            max_iterations=200,
            iterations_per_temp=5,
            random_seed=42,
        )

        optimize_grade_list(grade_list, config=config, progress_callback=callback)

        # Callback should have been called at least once
        assert len(progress_calls) > 0

        # Check that callback receives valid values
        for iteration, temp, fitness in progress_calls:
            assert iteration > 0
            assert temp > 0
            assert 0.0 <= fitness <= 1.0

    def test_single_classroom_no_change(self) -> None:
        """Test that single classroom returns unchanged."""
        teacher = Teacher(name="Ms. Smith", clusters=[])
        students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(5)
        ]

        classroom = Classroom(teacher=teacher, students=students)
        grade_list = GradeList(classes=[classroom], teachers=[teacher], students=students)

        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=100,
            iterations_per_temp=5,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, config=config)

        # With only one classroom, no swaps are possible
        assert len(optimized.classes) == 1
        assert len(optimized.classes[0].students) == 5


class TestOptimizeMultipleTimes:
    """Test suite for optimize_multiple_times function."""

    def test_multiple_runs_improve_result(self) -> None:
        """Test that running multiple times can find better results."""
        teacher1 = Teacher(name="Ms. Smith", clusters=[])
        teacher2 = Teacher(name="Mr. Jones", clusters=[])

        # Imbalanced distribution
        male_students = [
            Student(
                first_name=f"Boy{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(8)
        ]
        female_students = [
            Student(
                first_name=f"Girl{i}",
                last_name=f"Name{i}",
                gender=Gender.FEMALE,
                math=Math.HIGH,
                ela=ELA.HIGH,
                behavior=Behavior.HIGH,
            )
            for i in range(8)
        ]

        classroom1 = Classroom(teacher=teacher1, students=male_students)
        classroom2 = Classroom(teacher=teacher2, students=female_students)

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=male_students + female_students,
        )

        config = AnnealingConfig(
            initial_temperature=5.0,
            cooling_rate=0.9,
            min_temperature=0.01,
            max_iterations=200,
            iterations_per_temp=5,
        )

        optimized, fitness = optimize_multiple_times(grade_list, num_runs=3, config=config)

        assert optimized is not None
        assert 0.0 <= fitness <= 1.0
        assert isinstance(optimized, GradeList)


class TestExclusionConstraintsAnnealing:
    """Test suite for exclusion constraint enforcement in simulated annealing."""

    def test_is_swap_valid_rejects_exclusion_conflict(self) -> None:
        """Test that _is_swap_valid returns False for exclusion conflicts."""
        from eagleclasslists.simulated_annealing import _is_swap_valid

        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        # Alice excludes Bob
        student_alice = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )
        student_bob = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student_alice])
        classroom2 = Classroom(teacher=teacher2, students=[student_bob])

        # Swapping Alice and Bob would put them together - invalid
        assert _is_swap_valid(classroom1, classroom2, student_alice, student_bob) is False

    def test_is_swap_valid_allows_valid_swap(self) -> None:
        """Test that _is_swap_valid returns True when no exclusion conflicts."""
        from eagleclasslists.simulated_annealing import _is_swap_valid

        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        # Alice excludes Charlie (not Bob)
        student_alice = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Charlie Clark"],
        )
        student_bob = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
        )

        classroom1 = Classroom(teacher=teacher1, students=[student_alice])
        classroom2 = Classroom(teacher=teacher2, students=[student_bob])

        # Swapping Alice and Bob would be fine
        assert _is_swap_valid(classroom1, classroom2, student_alice, student_bob) is True

    def test_optimization_preserves_exclusions(self) -> None:
        """Test that optimization never violates exclusion constraints."""
        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        # Alice excludes Bob - they start in different classes
        student_alice = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )
        student_bob = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
        )
        # Add some other students for more optimization options
        other_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(8)
        ]

        # Alice and Bob start in different classrooms
        classroom1 = Classroom(teacher=teacher1, students=[student_alice] + other_students[:4])
        classroom2 = Classroom(teacher=teacher2, students=[student_bob] + other_students[4:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[student_alice, student_bob] + other_students,
        )

        # Optimize
        config = AnnealingConfig(
            initial_temperature=10.0,
            cooling_rate=0.95,
            min_temperature=0.01,
            max_iterations=500,
            iterations_per_temp=10,
            random_seed=42,
        )

        optimized = optimize_grade_list(grade_list, config=config)

        # Verify Alice and Bob are still in different classrooms
        alice_class = None
        bob_class = None
        for classroom in optimized.classes:
            for student in classroom.students:
                if student.first_name == "Alice" and student.last_name == "Anderson":
                    alice_class = classroom.teacher.name
                elif student.first_name == "Bob" and student.last_name == "Brown":
                    bob_class = classroom.teacher.name

        assert alice_class != bob_class
        assert alice_class is not None
        assert bob_class is not None

    def test_neighbor_generator_never_creates_exclusion_violations(self) -> None:
        """Test that neighbor generation never creates exclusion conflicts."""
        from eagleclasslists.simulated_annealing import (
            _generate_move_neighbor,
            _generate_swap_neighbor,
        )

        teacher1 = Teacher(name="Teacher A", clusters=[])
        teacher2 = Teacher(name="Teacher B", clusters=[])

        # Alice excludes Bob
        student_alice = Student(
            first_name="Alice",
            last_name="Anderson",
            gender=Gender.FEMALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
            exclusions=["Bob Brown"],
        )
        student_bob = Student(
            first_name="Bob",
            last_name="Brown",
            gender=Gender.MALE,
            math=Math.HIGH,
            ela=ELA.HIGH,
            behavior=Behavior.HIGH,
        )
        other_students = [
            Student(
                first_name=f"Student{i}",
                last_name=f"Name{i}",
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
                math=Math.MEDIUM,
                ela=ELA.MEDIUM,
                behavior=Behavior.MEDIUM,
            )
            for i in range(6)
        ]

        # Alice and Bob in different classrooms
        classroom1 = Classroom(teacher=teacher1, students=[student_alice] + other_students[:3])
        classroom2 = Classroom(teacher=teacher2, students=[student_bob] + other_students[3:])

        grade_list = GradeList(
            classes=[classroom1, classroom2],
            teachers=[teacher1, teacher2],
            students=[student_alice, student_bob] + other_students,
        )

        # Generate many neighbors and verify none create exclusion conflicts
        for _ in range(50):
            # Try swap neighbor
            swap_neighbor = _generate_swap_neighbor(grade_list)
            if swap_neighbor is not None:
                for classroom in swap_neighbor.classes:
                    student_names = {f"{s.first_name} {s.last_name}" for s in classroom.students}
                    # Alice and Bob should never be in the same classroom
                    assert not (
                        "Alice Anderson" in student_names and "Bob Brown" in student_names
                    ), f"Swap created exclusion violation: {student_names}"

            # Try move neighbor
            move_neighbor = _generate_move_neighbor(grade_list)
            if move_neighbor is not None:
                for classroom in move_neighbor.classes:
                    student_names = {f"{s.first_name} {s.last_name}" for s in classroom.students}
                    # Alice and Bob should never be in the same classroom
                    assert not (
                        "Alice Anderson" in student_names and "Bob Brown" in student_names
                    ), f"Move created exclusion violation: {student_names}"
