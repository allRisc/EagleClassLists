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

"""Greedy optimization module for assigning students to classrooms.

This module provides a greedy algorithm that sequentially assigns students
to classrooms by always choosing the assignment that maximizes the overall
fitness score. It respects hard constraints such as cluster assignments
and teacher requests.

Example:
    from eagleclasslists.greedy_assignment import greedy_assign_students
    from eagleclasslists.fitness import FitnessWeights

    # Assign students with default settings
    assigned = greedy_assign_students(grade_list)

    # Assign students with custom weights
    weights = FitnessWeights(gender=2.0, behavior=1.5)
    assigned = greedy_assign_students(grade_list, weights=weights)
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eagleclasslists.classlist import Classroom, GradeList, Student
    from eagleclasslists.fitness import FitnessWeights


def greedy_assign_students(
    grade_list: GradeList,
    students: list[Student] | None = None,
    weights: FitnessWeights | None = None,
    progress_callback: Callable[[int, int, float], None] | None = None,
) -> GradeList:
    """Assign students to classrooms using a greedy optimization algorithm.

    Sequentially assigns each student to the classroom that maximizes the
    overall fitness score. For each student, the algorithm tries all valid
    classrooms (respecting cluster constraints and teacher requests) and
    selects the one that yields the highest fitness.

    Hard constraints are always respected:
    - Cluster students are only placed with qualified teachers
    - Students with teacher requests are only placed with their requested teacher

    Args:
        grade_list: The GradeList containing the classrooms and teachers.
            The existing classes will be used as the base for assignments.
        students: Optional list of students to assign. If None, uses all
            students from grade_list.students that are not already assigned
            to a classroom.
        weights: Optional custom weights for fitness calculation.
            Uses default weights if not provided.
        progress_callback: Optional callback function called after each
            student assignment with (student_index, total_students, current_fitness).

    Returns:
        A new GradeList with all students assigned to classrooms.
    """
    from eagleclasslists.fitness import calculate_fitness

    # Create a deep copy to avoid modifying the original
    result = _copy_grade_list(grade_list)

    # Determine which students to assign
    if students is None:
        students = _get_unassigned_students(grade_list)

    # Sort students to handle hard constraints first:
    # 1. Students with teacher requests (most constrained)
    # 2. Students with cluster assignments
    # 3. Other students
    sorted_students = _sort_by_constraints(students)

    total_students = len(sorted_students)

    for idx, student in enumerate(sorted_students):
        # Find the best classroom for this student
        best_classroom_idx = _find_best_classroom(result, student, weights)

        if best_classroom_idx is None:
            # No valid classroom found - this shouldn't happen with proper input
            # but we handle it gracefully by skipping this student
            continue

        # Add student to the best classroom
        result.classes[best_classroom_idx].students.append(copy.copy(student))

        # Call progress callback if provided
        if progress_callback is not None:
            current_fitness = calculate_fitness(result, weights)
            progress_callback(idx + 1, total_students, current_fitness)

    return result


def _get_unassigned_students(grade_list: GradeList) -> list[Student]:
    """Get students from the grade_list that are not in any classroom.

    Args:
        grade_list: The GradeList to check.

    Returns:
        A list of students not assigned to any classroom.
    """
    # Build set of assigned student identifiers
    assigned_ids = {(s.first_name, s.last_name) for c in grade_list.classes for s in c.students}

    # Return students not in the assigned set
    return [s for s in grade_list.students if (s.first_name, s.last_name) not in assigned_ids]


def _sort_by_constraints(students: list[Student]) -> list[Student]:
    """Sort students by constraint level (most constrained first).

    Students with more constraints should be assigned first to ensure
    they get valid placements.

    Args:
        students: The list of students to sort.

    Returns:
        A new list sorted by constraint level (teacher request > cluster > none).
    """

    def constraint_key(student: Student) -> int:
        # Lower values = higher priority (assigned first)
        if student.teacher is not None and student.teacher != "":
            return 0  # Highest priority: has teacher request
        if student.cluster is not None:
            return 1  # Medium priority: has cluster assignment
        return 2  # Lowest priority: no constraints

    return sorted(students, key=constraint_key)


def _find_best_classroom(
    grade_list: GradeList,
    student: Student,
    weights: FitnessWeights | None = None,
) -> int | None:
    """Find the classroom that maximizes fitness for a given student.

    Args:
        grade_list: The current GradeList with existing assignments.
        student: The student to assign.
        weights: Optional fitness weights.

    Returns:
        The index of the best classroom, or None if no valid classroom exists.
    """
    from eagleclasslists.fitness import calculate_fitness

    if not grade_list.classes:
        return None

    best_idx: int | None = None
    best_fitness = -1.0

    for idx, classroom in enumerate(grade_list.classes):
        # Check if this student can be placed in this classroom
        if not _is_valid_assignment(classroom, student):
            continue

        # Temporarily add student to this classroom
        classroom.students.append(copy.copy(student))

        # Calculate fitness with this assignment
        fitness = calculate_fitness(grade_list, weights)

        # Remove the student (we'll add them permanently to the best one)
        classroom.students.pop()

        # Track the best classroom
        if fitness > best_fitness:
            best_fitness = fitness
            best_idx = idx

    return best_idx


def _is_valid_assignment(classroom: Classroom, student: Student) -> bool:
    """Check if a student can be assigned to a classroom.

    Validates hard constraints:
    - Teacher request: if student has a request, must match classroom's teacher
    - Cluster: if student has a cluster, teacher must be qualified

    Args:
        classroom: The classroom to check.
        student: The student to assign.

    Returns:
        True if the assignment is valid, False otherwise.
    """
    teacher_name = classroom.teacher.name
    teacher_clusters = set(classroom.teacher.clusters)

    # Check teacher request constraint
    if student.teacher is not None and student.teacher != "":
        if student.teacher != teacher_name:
            return False

    # Check cluster constraint
    if student.cluster is not None and student.cluster not in teacher_clusters:
        return False

    return True


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
        # Copy students in this classroom
        copied_students = [copy.copy(s) for s in classroom.students]
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
            all_students.append(copy.copy(student))

    return GradeList(classes=new_classes, teachers=teachers, students=all_students)
