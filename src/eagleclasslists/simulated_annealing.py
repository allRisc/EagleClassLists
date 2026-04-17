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

"""Simulated annealing module for optimizing GradeList assignments.

This module provides an implementation of the simulated annealing algorithm
for finding optimal student-to-classroom assignments that maximize fairness
metrics while respecting cluster constraints.

Example:
    from eagleclasslists.simulated_annealing import optimize_grade_list
    from eagleclasslists.fitness import FitnessWeights

    # Optimize with default settings
    optimized = optimize_grade_list(grade_list)

    # Optimize with custom weights
    weights = FitnessWeights(cluster=20.0, gender=2.0)
    optimized = optimize_grade_list(grade_list, weights=weights)
"""

from __future__ import annotations

import copy
import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eagleclasslists.classlist import Classroom, GradeList, Student
    from eagleclasslists.fitness import FitnessWeights


@dataclass
class AnnealingConfig:
    """Configuration parameters for simulated annealing.

    These parameters control the behavior of the optimization algorithm.
    """

    initial_temperature: float = 100.0
    """Starting temperature for the annealing process. Higher values allow more
    exploration early on."""

    cooling_rate: float = 0.995
    """Rate at which temperature decreases per iteration. Should be between 0 and 1."""

    min_temperature: float = 0.001
    """Minimum temperature at which to stop."""

    max_iterations: int = 10000
    """Maximum number of iterations to run."""

    iterations_per_temp: int = 100
    """Number of iterations at each temperature before cooling."""

    random_seed: int | None = None
    """Optional seed for reproducible results."""


def optimize_grade_list(
    grade_list: GradeList,
    weights: FitnessWeights | None = None,
    config: AnnealingConfig | None = None,
    progress_callback: Callable[[int, float, float], None] | None = None,
) -> GradeList:
    """Optimize a GradeList using simulated annealing.

    Finds a better assignment of students to classrooms by maximizing
    the fitness score while respecting cluster and teacher request constraints.

    Args:
        grade_list: The GradeList to optimize.
        weights: Optional custom weights for fitness calculation.
        config: Optional custom annealing configuration.
        progress_callback: Optional callback function called periodically
            with (iteration, temperature, current_fitness).

    Returns:
        A new GradeList with optimized student assignments.
    """
    if config is None:
        config = AnnealingConfig()

    if config.random_seed is not None:
        random.seed(config.random_seed)

    # Import fitness module here to avoid circular imports
    from eagleclasslists.fitness import calculate_fitness

    # Create a deep copy to avoid modifying the original
    current_solution = _copy_grade_list(grade_list)
    current_fitness = calculate_fitness(current_solution, weights)

    # Track the best solution found
    best_solution = _copy_grade_list(current_solution)
    best_fitness = current_fitness

    # Initialize temperature
    temperature = config.initial_temperature
    iteration = 0

    # Main annealing loop
    while temperature > config.min_temperature and iteration < config.max_iterations:
        # Perform multiple iterations at each temperature
        for _ in range(config.iterations_per_temp):
            if iteration >= config.max_iterations:
                break

            iteration += 1

            # Generate a neighbor solution that respects hard constraints
            neighbor = _generate_neighbor(current_solution)

            if neighbor is None:
                continue

            # Calculate neighbor fitness
            neighbor_fitness = calculate_fitness(neighbor, weights)

            # Decide whether to accept the neighbor
            delta = neighbor_fitness - current_fitness

            if delta > 0:
                # Better solution: always accept
                current_solution = neighbor
                current_fitness = neighbor_fitness

                # Update best if needed
                if current_fitness > best_fitness:
                    best_solution = _copy_grade_list(current_solution)
                    best_fitness = current_fitness
            else:
                # Worse solution: accept with probability based on temperature
                acceptance_probability = math.exp(delta / temperature)
                if random.random() < acceptance_probability:
                    current_solution = neighbor
                    current_fitness = neighbor_fitness

        # Cool down
        temperature *= config.cooling_rate

        # Call progress callback if provided
        if progress_callback is not None and iteration % 100 == 0:
            progress_callback(iteration, temperature, current_fitness)

    return best_solution


def _copy_grade_list(grade_list: GradeList) -> GradeList:
    """Create a deep copy of a GradeList.

    Args:
        grade_list: The GradeList to copy.

    Returns:
        A new GradeList with copied students and classrooms.
    """
    from eagleclasslists.classlist import Classroom, GradeList

    # Copy teachers (shared reference is fine)
    teachers = list(grade_list.teachers)

    # Create new classrooms with copied student lists
    new_classes = []
    all_students = []

    for classroom in grade_list.classes:
        # Copy students in this classroom using Pydantic's model_copy
        copied_students = [s.model_copy() for s in classroom.students]
        all_students.extend(copied_students)

        # Create new classroom with copied students
        new_class = Classroom(teacher=classroom.teacher, students=copied_students)
        new_classes.append(new_class)

    # Also copy students not in any classroom
    assigned_student_ids = {
        (s.first_name, s.last_name) for c in grade_list.classes for s in c.students
    }
    for student in grade_list.students:
        if (student.first_name, student.last_name) not in assigned_student_ids:
            all_students.append(student.model_copy())

    return GradeList(classes=new_classes, teachers=teachers, students=all_students)


def _generate_neighbor(grade_list: GradeList) -> GradeList | None:
    """Generate a neighbor solution by swapping students between classrooms.

    This implementation respects hard constraints (cluster assignments,
    teacher requests, and exclusions). It only generates moves that do not
    violate these constraints.

    Args:
        grade_list: The current GradeList.

    Returns:
        A new GradeList with a single student swap, or None if no valid
        neighbor could be generated.
    """
    if len(grade_list.classes) < 2:
        return None

    # Try to find a valid swap between two classrooms
    swap_result = _generate_swap_neighbor(grade_list)
    if swap_result is not None:
        return swap_result

    # If no valid swap found, try moving a single student
    return _generate_move_neighbor(grade_list)


def _has_teacher_request(student: Student) -> bool:
    """Check if a student has a teacher request.

    Args:
        student: The student to check.

    Returns:
        True if the student has a non-empty teacher request, False otherwise.
    """
    return student.teacher is not None and student.teacher != ""


def _is_teacher_request_satisfied(student: Student, teacher_name: str) -> bool:
    """Check if a student is with their requested teacher.

    Args:
        student: The student to check.
        teacher_name: The name of the teacher the student is currently with.

    Returns:
        True if the student has no request or is with their requested teacher.
    """
    if not _has_teacher_request(student):
        return True
    return student.teacher == teacher_name


def _generate_swap_neighbor(grade_list: GradeList) -> GradeList | None:
    """Generate a neighbor by swapping two students between classrooms.

    Intelligently searches for valid swaps that respect cluster constraints
    and teacher requests, trying multiple student combinations.

    Args:
        grade_list: The current GradeList.

    Returns:
        A new GradeList with a valid swap, or None if no valid swap found.
    """
    num_classes = len(grade_list.classes)

    # Try multiple random classroom pairs
    for _ in range(min(50, num_classes * (num_classes - 1) // 2)):
        # Select two different classrooms randomly
        idx1, idx2 = random.sample(range(num_classes), 2)

        classroom1 = grade_list.classes[idx1]
        classroom2 = grade_list.classes[idx2]

        if not classroom1.students or not classroom2.students:
            continue

        # Try multiple student combinations from these classrooms
        # Prioritize students without cluster constraints as they're easier to swap
        students1_with_indices = list(enumerate(classroom1.students))
        students2_with_indices = list(enumerate(classroom2.students))

        # Shuffle to try random combinations
        random.shuffle(students1_with_indices)
        random.shuffle(students2_with_indices)

        # Try combinations, prioritizing students without clusters first
        for s1_idx, student1 in students1_with_indices:
            # Skip students with teacher requests - they must stay with their teacher
            if _has_teacher_request(student1):
                continue

            for s2_idx, student2 in students2_with_indices:
                # Skip students with teacher requests - they must stay with their teacher
                if _has_teacher_request(student2):
                    continue

                # Check if swap is valid (respects cluster and teacher request constraints)
                if _is_swap_valid(classroom1, classroom2, student1, student2):
                    return _create_swap_neighbor(grade_list, idx1, s1_idx, idx2, s2_idx)

    return None


def _is_swap_valid(
    classroom1: Classroom,
    classroom2: Classroom,
    student1: Student,
    student2: Student,
) -> bool:
    """Check if swapping two students between classrooms is valid.

    A swap is valid if cluster constraints, teacher requests, and exclusions
    are respected after the swap.

    Args:
        classroom1: First classroom.
        classroom2: Second classroom.
        student1: Student from classroom1 to swap.
        student2: Student from classroom2 to swap.

    Returns:
        True if the swap is valid, False otherwise.
    """
    # Get teacher names
    teacher1_name = classroom1.teacher.name
    teacher2_name = classroom2.teacher.name

    # Check teacher request constraints
    # If student1 has a teacher request, they can only be with that teacher
    if _has_teacher_request(student1) and student1.teacher != teacher2_name:
        return False

    # If student2 has a teacher request, they can only be with that teacher
    if _has_teacher_request(student2) and student2.teacher != teacher1_name:
        return False

    # Get teacher cluster qualifications
    teacher1_clusters = set(classroom1.teacher.clusters)
    teacher2_clusters = set(classroom2.teacher.clusters)

    # Check if student1 can go to classroom2
    if student1.cluster is not None and student1.cluster not in teacher2_clusters:
        return False

    # Check if student2 can go to classroom1
    if student2.cluster is not None and student2.cluster not in teacher1_clusters:
        return False

    # Check exclusion constraints for the swap
    # When swapping, student1 leaves classroom1 and goes to classroom2
    # student2 leaves classroom2 and goes to classroom1
    if _has_exclusion_conflict_for_swap(classroom1, classroom2, student1, student2):
        return False

    return True


def _has_exclusion_conflict_for_swap(
    classroom1: Classroom,
    classroom2: Classroom,
    student1: Student,
    student2: Student,
) -> bool:
    """Check if swapping two students would create exclusion conflicts.

    When swapping, student1 leaves classroom1 and joins classroom2,
    while student2 leaves classroom2 and joins classroom1.

    Args:
        classroom1: First classroom.
        classroom2: Second classroom.
        student1: Student from classroom1 to swap.
        student2: Student from classroom2 to swap.

    Returns:
        True if the swap would create an exclusion conflict, False otherwise.
    """
    student1_name = f"{student1.first_name} {student1.last_name}"
    student2_name = f"{student2.first_name} {student2.last_name}"

    # Build sets of students in each classroom after the swap
    # classroom1 will have student2 instead of student1
    classroom1_after = {
        f"{s.first_name} {s.last_name}"
        for s in classroom1.students
        if s.first_name != student1.first_name or s.last_name != student1.last_name
    }
    classroom1_after.add(student2_name)

    # classroom2 will have student1 instead of student2
    classroom2_after = {
        f"{s.first_name} {s.last_name}"
        for s in classroom2.students
        if s.first_name != student2.first_name or s.last_name != student2.last_name
    }
    classroom2_after.add(student1_name)

    # Check student1's exclusions against classroom2 (after swap)
    if student1.exclusions:
        for excluded_name in student1.exclusions:
            if excluded_name in classroom2_after and excluded_name != student2_name:
                return True

    # Check student2's exclusions against classroom1 (after swap)
    if student2.exclusions:
        for excluded_name in student2.exclusions:
            if excluded_name in classroom1_after and excluded_name != student1_name:
                return True

    # Check if anyone in classroom2 (after swap) excludes student1
    for s in classroom2.students:
        if s.first_name == student2.first_name and s.last_name == student2.last_name:
            continue  # Skip student2 who is leaving
        if s.exclusions and student1_name in s.exclusions:
            return True
    # Also check student2 (who will be in classroom1 after swap)
    if student2.exclusions and student1_name in student2.exclusions:
        return True

    # Check if anyone in classroom1 (after swap) excludes student2
    for s in classroom1.students:
        if s.first_name == student1.first_name and s.last_name == student1.last_name:
            continue  # Skip student1 who is leaving
        if s.exclusions and student2_name in s.exclusions:
            return True
    # Also check student1 (who will be in classroom2 after swap)
    if student1.exclusions and student2_name in student1.exclusions:
        return True

    return False


def _create_swap_neighbor(
    grade_list: GradeList,
    class_idx1: int,
    student_idx1: int,
    class_idx2: int,
    student_idx2: int,
) -> GradeList:
    """Create a new GradeList with two students swapped.

    Args:
        grade_list: The original GradeList.
        class_idx1: Index of first classroom.
        student_idx1: Index of student in first classroom.
        class_idx2: Index of second classroom.
        student_idx2: Index of student in second classroom.

    Returns:
        A new GradeList with the swap applied.
    """
    # Create a copy
    new_grade = _copy_grade_list(grade_list)

    # Perform the swap
    class1 = new_grade.classes[class_idx1]
    class2 = new_grade.classes[class_idx2]

    student1 = class1.students[student_idx1]
    student2 = class2.students[student_idx2]

    class1.students[student_idx1] = student2
    class2.students[student_idx2] = student1

    return new_grade


def _generate_move_neighbor(grade_list: GradeList) -> GradeList | None:
    """Generate a neighbor by moving a single student between classrooms.

    Intelligently selects students that can be moved without violating
    cluster constraints, teacher requests, or exclusion constraints.

    Args:
        grade_list: The current GradeList.

    Returns:
        A new GradeList with a single student moved, or None if no valid
        move could be generated.
    """
    if len(grade_list.classes) < 2:
        return None

    num_classes = len(grade_list.classes)

    # Build list of all possible valid moves
    valid_moves: list[tuple[int, int, int]] = []  # (source_idx, student_idx, target_idx)

    for source_idx in range(num_classes):
        source_class = grade_list.classes[source_idx]

        if not source_class.students:
            continue

        for student_idx, student in enumerate(source_class.students):
            # Skip students with teacher requests - they must stay with their teacher
            if _has_teacher_request(student):
                continue

            for target_idx in range(num_classes):
                if source_idx == target_idx:
                    continue

                target_class = grade_list.classes[target_idx]
                target_clusters = set(target_class.teacher.clusters)

                # Check if this student can move to this classroom
                if student.cluster is not None and student.cluster not in target_clusters:
                    continue

                # Check exclusion constraints
                if _has_exclusion_conflict_for_move(target_class, student):
                    continue

                valid_moves.append((source_idx, student_idx, target_idx))

    if valid_moves:
        # Pick a random valid move
        source_idx, student_idx, target_idx = random.choice(valid_moves)
        return _create_move_neighbor(grade_list, source_idx, student_idx, target_idx)

    return None


def _has_exclusion_conflict_for_move(target_class: Classroom, student: Student) -> bool:
    """Check if moving a student to a classroom would create exclusion conflicts.

    Args:
        target_class: The classroom the student would move to.
        student: The student to check.

    Returns:
        True if the move would create an exclusion conflict, False otherwise.
    """
    student_name = f"{student.first_name} {student.last_name}"

    # Build set of students in target classroom
    classroom_student_names = {f"{s.first_name} {s.last_name}" for s in target_class.students}

    # Check 1: Does this student exclude anyone in the classroom?
    if student.exclusions:
        for excluded_name in student.exclusions:
            if excluded_name in classroom_student_names:
                return True

    # Check 2: Does anyone in the classroom exclude this student?
    for classroom_student in target_class.students:
        if classroom_student.exclusions and student_name in classroom_student.exclusions:
            return True

    return False


def _create_move_neighbor(
    grade_list: GradeList,
    source_idx: int,
    student_idx: int,
    target_idx: int,
) -> GradeList:
    """Create a new GradeList with a student moved between classrooms.

    Args:
        grade_list: The original GradeList.
        source_idx: Index of source classroom.
        student_idx: Index of student to move.
        target_idx: Index of target classroom.

    Returns:
        A new GradeList with the move applied.
    """
    # Create a copy
    new_grade = _copy_grade_list(grade_list)

    # Perform the move
    source_class = new_grade.classes[source_idx]
    target_class = new_grade.classes[target_idx]

    student = source_class.students.pop(student_idx)
    target_class.students.append(student)

    return new_grade


def optimize_multiple_times(
    grade_list: GradeList,
    num_runs: int = 5,
    weights: FitnessWeights | None = None,
    config: AnnealingConfig | None = None,
) -> tuple[GradeList, float]:
    """Run simulated annealing multiple times and return the best result.

    Args:
        grade_list: The GradeList to optimize.
        num_runs: Number of times to run the optimization (default: 5).
        weights: Optional custom weights for fitness calculation.
        config: Optional custom annealing configuration.

    Returns:
        A tuple of (best_grade_list, best_fitness_score).
    """
    from eagleclasslists.fitness import calculate_fitness

    best_solution = None
    best_fitness = 0.0

    for _run in range(num_runs):
        # Vary the random seed for each run
        run_config = copy.copy(config) if config else AnnealingConfig()
        run_config.random_seed = random.randint(0, 1000000)

        solution = optimize_grade_list(grade_list, weights, run_config)
        fitness = calculate_fitness(solution, weights)

        if fitness > best_fitness:
            best_fitness = fitness
            best_solution = solution

    if best_solution is None:
        return grade_list, 0.0

    return best_solution, best_fitness
