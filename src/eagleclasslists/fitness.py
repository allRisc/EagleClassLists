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

"""Fitness module for computing the fairness score of a GradeList.

This module provides functions to evaluate how well-balanced a grade list is,
considering cluster assignments, gender distribution, academics, behavior,
and special services (resource, speech). The fitness score ranges from 0 to 1,
where 1 represents a perfectly balanced distribution.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from eagleclasslists.classlist import (
        GradeList,
        Student,
    )


@dataclass
class FitnessWeights:
    """Configurable weights for fitness calculation.

    All weights should be non-negative. The final fitness score is computed
    as a weighted average of individual component scores.

    Note: Cluster correctness is not included as a weight because it is a
    hard constraint enforced by the optimization algorithm. The fitness
    will always be 0.0 if cluster constraints are violated.
    """

    gender: float = 1.0
    """Weight for gender balance across classrooms."""

    academics: float = 1.0
    """Weight for academic performance balance."""

    behavior: float = 1.0
    """Weight for behavior rating balance."""

    resource: float = 0.5
    """Weight for resource services balance."""

    speech: float = 0.5
    """Weight for speech services balance."""

    class_size: float = 1.0
    """Weight for class size balance."""

    def total_weight(self) -> float:
        """Calculate the sum of all weights for normalization.

        Returns:
            The total weight value.
        """
        return (
            self.gender
            + self.academics
            + self.behavior
            + self.resource
            + self.speech
            + self.class_size
        )


def calculate_fitness(grade_list: GradeList, weights: FitnessWeights | None = None) -> float:
    """Calculate the overall fitness score for a GradeList.

    Computes a weighted fitness score between 0 and 1, where 1 represents
    a perfectly balanced grade list with all cluster constraints satisfied.

    Cluster correctness is a hard constraint - if any cluster student is
    with an unqualified teacher, the fitness is 0.0 regardless of other
    metrics.

    Args:
        grade_list: The GradeList to evaluate.
        weights: Optional custom weights for fitness components. Uses
            default weights if not provided.

    Returns:
        A float between 0 and 1 representing the fitness score.
    """
    if weights is None:
        weights = FitnessWeights()

    if not grade_list.classes:
        return 0.0

    # Check cluster constraint first (hard constraint)
    cluster_score = _calculate_cluster_score(grade_list)
    if cluster_score == 0.0:
        return 0.0  # Hard constraint violation

    # Calculate other component scores
    gender_score = _calculate_gender_balance(grade_list)
    academics_score = _calculate_academics_balance(grade_list)
    behavior_score = _calculate_behavior_balance(grade_list)
    resource_score = _calculate_resource_balance(grade_list)
    speech_score = _calculate_speech_balance(grade_list)
    class_size_score = _calculate_class_size_balance(grade_list)

    # Weighted average (cluster not included in weight calculation)
    total_weight = weights.total_weight()
    if total_weight == 0:
        return 0.0

    weighted_score = (
        weights.gender * gender_score
        + weights.academics * academics_score
        + weights.behavior * behavior_score
        + weights.resource * resource_score
        + weights.speech * speech_score
        + weights.class_size * class_size_score
    ) / total_weight

    # Clamp between 0 and 1
    return max(0.0, min(1.0, weighted_score))


def _calculate_cluster_score(grade_list: GradeList) -> float:
    """Calculate cluster assignment correctness score.

    Checks that all students with cluster assignments are placed with
    teachers qualified for that cluster.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A binary score: 1.0 if all cluster assignments are correct,
        0.0 if any cluster assignment is incorrect.
    """
    if not grade_list.classes:
        return 0.0

    # Build teacher cluster lookup
    teacher_clusters = {t.name: set(t.clusters) for t in grade_list.teachers}

    for classroom in grade_list.classes:
        teacher_name = classroom.teacher.name
        teacher_cluster_set = teacher_clusters.get(teacher_name, set())

        for student in classroom.students:
            if student.cluster is not None:
                if student.cluster not in teacher_cluster_set:
                    return 0.0  # Any violation results in score of 0

    return 1.0


def _calculate_gender_balance(grade_list: GradeList) -> float:
    """Calculate gender distribution balance score.

    Measures how evenly gender is distributed across classrooms.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A score between 0 and 1, where 1 means perfect gender balance.
    """
    from eagleclasslists.classlist import Gender

    return _calculate_enum_balance(grade_list, lambda s: s.gender, [Gender.MALE, Gender.FEMALE])


def _calculate_academics_balance(grade_list: GradeList) -> float:
    """Calculate academic performance distribution balance score.

    Measures how evenly academic performance levels are distributed
    across classrooms.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A score between 0 and 1, where 1 means perfect balance.
    """
    from eagleclasslists.classlist import Academics

    return _calculate_enum_balance(
        grade_list,
        lambda s: s.academics,
        [Academics.HIGH, Academics.MEDIUM, Academics.LOW],
    )


def _calculate_behavior_balance(grade_list: GradeList) -> float:
    """Calculate behavior rating distribution balance score.

    Measures how evenly behavior ratings are distributed across classrooms.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A score between 0 and 1, where 1 means perfect balance.
    """
    from eagleclasslists.classlist import Behavior

    return _calculate_enum_balance(
        grade_list,
        lambda s: s.behavior,
        [Behavior.HIGH, Behavior.MEDIUM, Behavior.LOW],
    )


def _calculate_resource_balance(grade_list: GradeList) -> float:
    """Calculate resource services distribution balance score.

    Measures how evenly students receiving resource services are
    distributed across classrooms.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A score between 0 and 1, where 1 means perfect balance.
    """
    return _calculate_boolean_balance(grade_list, lambda s: s.resource)


def _calculate_speech_balance(grade_list: GradeList) -> float:
    """Calculate speech services distribution balance score.

    Measures how evenly students receiving speech services are
    distributed across classrooms.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A score between 0 and 1, where 1 means perfect balance.
    """
    return _calculate_boolean_balance(grade_list, lambda s: s.speech)


def _calculate_class_size_balance(grade_list: GradeList) -> float:
    """Calculate class size balance score.

    Measures how evenly students are distributed across classrooms.

    Args:
        grade_list: The GradeList to evaluate.

    Returns:
        A score between 0 and 1, where 1 means perfectly equal class sizes.
    """
    if not grade_list.classes or len(grade_list.classes) < 2:
        return 1.0

    sizes = [len(c.students) for c in grade_list.classes]

    if not sizes or max(sizes) == 0:
        return 1.0

    # Calculate coefficient of variation (lower is better)
    mean_size = sum(sizes) / len(sizes)
    if mean_size == 0:
        return 1.0

    variance = sum((s - mean_size) ** 2 for s in sizes) / len(sizes)
    std_dev = variance**0.5
    cv = std_dev / mean_size

    # Convert CV to score (CV of 0 -> score of 1, higher CV -> lower score)
    # Using exponential decay: score = exp(-2 * CV)
    import math

    score = math.exp(-2 * cv)
    return score


def _calculate_enum_balance(
    grade_list: GradeList,
    getter: Callable[[Student], Any],
    enum_values: list,
) -> float:
    """Calculate balance score for an enum attribute across classrooms.

    Args:
        grade_list: The GradeList to evaluate.
        getter: Function to extract the enum value from a Student.
        enum_values: List of all possible enum values.

    Returns:
        A score between 0 and 1, where 1 means perfect balance.
    """
    if not grade_list.classes or len(grade_list.classes) < 2:
        return 1.0

    # Count occurrences per classroom for each enum value
    classroom_counts: list[dict] = []
    for classroom in grade_list.classes:
        counts: dict = {val: 0 for val in enum_values}
        for student in classroom.students:
            val = getter(student)
            if val in counts:
                counts[val] += 1
        classroom_counts.append(counts)

    # Calculate ideal count per classroom for each enum value
    total_students = sum(len(c.students) for c in grade_list.classes)
    if total_students == 0:
        return 1.0

    # For each enum value, calculate how evenly it's distributed
    total_deviation = 0.0
    num_metrics = len(enum_values)

    for enum_val in enum_values:
        # Total count of this value across all classrooms
        total_count = sum(counts[enum_val] for counts in classroom_counts)
        if total_count == 0:
            continue

        # Ideal count per classroom (proportional to classroom size)
        classroom_sizes = [len(c.students) for c in grade_list.classes]
        ideal_counts = [(size / total_students) * total_count for size in classroom_sizes]

        # Calculate deviation from ideal
        actual_counts = [counts[enum_val] for counts in classroom_counts]
        deviations = [
            abs(actual - ideal) / max(ideal, 1)
            for actual, ideal in zip(actual_counts, ideal_counts, strict=True)
        ]
        avg_deviation = sum(deviations) / len(deviations) if deviations else 0
        total_deviation += avg_deviation

    if num_metrics == 0:
        return 1.0

    avg_deviation = total_deviation / num_metrics

    # Convert deviation to score (lower deviation -> higher score)
    # Using exponential decay: score = exp(-avg_deviation)
    import math

    score = math.exp(-avg_deviation)
    return score


def _calculate_boolean_balance(grade_list: GradeList, getter: Callable[[Student], bool]) -> float:
    """Calculate balance score for a boolean attribute across classrooms.

    Args:
        grade_list: The GradeList to evaluate.
        getter: Function to extract the boolean value from a Student.

    Returns:
        A score between 0 and 1, where 1 means perfect balance.
    """
    if not grade_list.classes or len(grade_list.classes) < 2:
        return 1.0

    # Count "True" occurrences per classroom
    true_counts = []
    classroom_sizes = []

    for classroom in grade_list.classes:
        count = sum(1 for s in classroom.students if getter(s))
        true_counts.append(count)
        classroom_sizes.append(len(classroom.students))

    total_true = sum(true_counts)
    total_students = sum(classroom_sizes)

    if total_true == 0 or total_students == 0:
        return 1.0  # Nothing to balance

    # Calculate ideal count per classroom (proportional to classroom size)
    ideal_counts = [(size / total_students) * total_true for size in classroom_sizes]

    # Calculate deviation from ideal
    deviations = [
        abs(actual - ideal) / max(ideal, 1)
        for actual, ideal in zip(true_counts, ideal_counts, strict=True)
    ]
    avg_deviation = sum(deviations) / len(deviations)

    # Convert deviation to score
    import math

    score = math.exp(-avg_deviation)
    return score


def get_fitness_breakdown(
    grade_list: GradeList, weights: FitnessWeights | None = None
) -> dict[str, float]:
    """Get a detailed breakdown of fitness component scores.

    Args:
        grade_list: The GradeList to evaluate.
        weights: Optional custom weights for fitness components.

    Returns:
        A dictionary mapping component names to their individual scores.
    """
    if weights is None:
        weights = FitnessWeights()

    return {
        "cluster": _calculate_cluster_score(grade_list),
        "gender": _calculate_gender_balance(grade_list),
        "academics": _calculate_academics_balance(grade_list),
        "behavior": _calculate_behavior_balance(grade_list),
        "resource": _calculate_resource_balance(grade_list),
        "speech": _calculate_speech_balance(grade_list),
        "class_size": _calculate_class_size_balance(grade_list),
        "overall": calculate_fitness(grade_list, weights),
    }
