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

"""Classroom management page for the Streamlit app."""

from __future__ import annotations

from typing import Literal

import streamlit as st

from eagleclasslists.classlist import Classroom, GradeList, Student, Teacher
from eagleclasslists.fitness import FitnessWeights, calculate_fitness, get_fitness_breakdown
from eagleclasslists.simulated_annealing import AnnealingConfig, optimize_grade_list


def _get_student_display_name(student: Student) -> str:
    """Generate display name for a student with attributes."""
    attrs = []
    if student.cluster:
        attrs.append(str(student.cluster))
    if student.resource:
        attrs.append("R")
    if student.speech:
        attrs.append("S")
    if attrs:
        return f"{student.first_name} {student.last_name} ({', '.join(attrs)})"
    return f"{student.first_name} {student.last_name}"


def _get_teacher_color(teacher: Teacher) -> tuple[str, str]:
    """Generate background and text colors for a teacher based on their clusters.

    Returns:
        Tuple of (background_color, text_color)
    """
    if not teacher.clusters:
        return ("#6b7280", "#ffffff")  # Gray with white text
    cluster_colors = {
        "AC": ("#1e40af", "#ffffff"),  # Dark blue with white text
        "GEM": ("#b45309", "#ffffff"),  # Dark orange/amber with white text
        "EL": ("#047857", "#ffffff"),  # Dark green with white text
    }
    return cluster_colors.get(str(teacher.clusters[0]), ("#6b7280", "#ffffff"))


def _build_teacher_students_map(grade_list: GradeList) -> dict[str, list[Student]]:
    """Build a map of teacher names to their assigned students."""
    teacher_students: dict[str, list[Student]] = {}
    for cls in grade_list.classes:
        teacher_students[cls.teacher.name] = cls.students.copy()
    return teacher_students


def _get_unassigned_students(
    grade_list: GradeList, teacher_students: dict[str, list[Student]]
) -> list[Student]:
    """Get students not assigned to any teacher."""
    assigned_students = set()
    for students in teacher_students.values():
        for s in students:
            assigned_students.add((s.first_name, s.last_name))

    return [s for s in grade_list.students if (s.first_name, s.last_name) not in assigned_students]


def _remove_student_from_teacher(
    grade_list: GradeList, teacher_name: str, first_name: str, last_name: str
) -> None:
    """Remove a student from a teacher's classroom."""
    for cls in grade_list.classes:
        if cls.teacher.name == teacher_name:
            cls.students = [
                s
                for s in cls.students
                if not (s.first_name == first_name and s.last_name == last_name)
            ]
            break


def _add_student_to_teacher(
    grade_list: GradeList, teacher_name: str, first_name: str, last_name: str
) -> None:
    """Add a student to a teacher's classroom."""
    teacher = next(t for t in grade_list.teachers if t.name == teacher_name)
    student = next(
        s for s in grade_list.students if s.first_name == first_name and s.last_name == last_name
    )

    # Find or create classroom
    classroom: Classroom | None = next(
        (c for c in grade_list.classes if c.teacher.name == teacher_name),
        None,
    )
    if classroom is None:
        new_classroom = Classroom(teacher=teacher, students=[])
        grade_list.classes.append(new_classroom)
        classroom = new_classroom

    # Check if student already assigned to this teacher
    already_assigned = any(
        s.first_name == first_name and s.last_name == last_name for s in classroom.students
    )

    if not already_assigned:
        classroom.students.append(student)


def render_classrooms_page() -> None:
    """Render the classrooms page for managing student-teacher assignments."""
    st.header("Classroom Management")
    st.write(
        "Check the students you want to move, select a destination, then click 'Move Selected'."
    )

    grade_list: GradeList = st.session_state.grade_list

    # Process any pending assignment operations
    if st.session_state.get("assignment_to_add") is not None:
        teacher_name, first_name, last_name = st.session_state.assignment_to_add
        _add_student_to_teacher(grade_list, teacher_name, first_name, last_name)
        st.session_state.assignment_to_add = None
        st.success(f"Added {first_name} {last_name} to {teacher_name}")
        st.rerun()

    if not grade_list.teachers:
        st.warning("No teachers available. Add teachers first.")
        return

    if not grade_list.students:
        st.warning("No students available. Add students first.")
        return

    # Build data structures
    teacher_students = _build_teacher_students_map(grade_list)
    unassigned = _get_unassigned_students(grade_list, teacher_students)

    # Initialize session state for selections
    if "selected_students" not in st.session_state:
        st.session_state.selected_students = []
    if "selected_teacher" not in st.session_state:
        st.session_state.selected_teacher = None

    # CSS for styling
    st.markdown(
        """
        <style>
        .student-card {
            background-color: rgba(128, 128, 128, 0.15);
            border: 2px solid rgba(128, 128, 128, 0.3);
            border-radius: 8px;
            padding: 8px 12px;
            margin: 4px 0;
            cursor: pointer;
            transition: all 0.2s;
        }
        .student-card:hover {
            border-color: #ff4b4b;
            background-color: rgba(255, 75, 75, 0.15);
        }
        .student-card-selected {
            background-color: #ff4b4b;
            color: white;
            border-color: #ff4b4b;
        }
        .teacher-column {
            background-color: rgba(128, 128, 128, 0.05);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 8px;
            padding: 12px;
            min-height: 200px;
        }
        .teacher-header {
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 12px;
            text-align: center;
        }
        .assigned-student {
            background-color: rgba(128, 128, 128, 0.1);
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 4px;
            padding: 8px 12px;
            margin: 6px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Main layout: Unassigned students on left, teachers on right
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Unassigned Students")
        st.write(f"**Count: {len(unassigned)}**")

        # Target teacher selection for assigning
        if unassigned:
            target_teacher = st.selectbox(
                "Assign selected to:",
                options=[t.name for t in grade_list.teachers],
                key="target_teacher_unassigned",
            )

            if st.button("Assign Selected", type="primary", use_container_width=True):
                if st.session_state.selected_students:
                    count = 0
                    for student_key in st.session_state.selected_students:
                        first_name, last_name = student_key.split("|", 1)
                        _add_student_to_teacher(grade_list, target_teacher, first_name, last_name)
                        count += 1
                    st.session_state.selected_students = []
                    st.success(f"Assigned {count} students to {target_teacher}")
                    st.rerun()
                else:
                    st.warning("No students selected")

        st.divider()

        # Display unassigned students as clickable cards
        if unassigned:
            for student in unassigned:
                student_key = f"{student.first_name}|{student.last_name}"
                display_name = _get_student_display_name(student)

                is_selected = student_key in st.session_state.selected_students
                button_type: Literal["primary", "secondary"] = (
                    "primary" if is_selected else "secondary"
                )

                cols = st.columns([4, 1])
                with cols[0]:
                    if st.button(
                        display_name,
                        key=f"select_{student_key}",
                        type=button_type,
                        use_container_width=True,
                    ):
                        if student_key in st.session_state.selected_students:
                            st.session_state.selected_students.remove(student_key)
                        else:
                            st.session_state.selected_students.append(student_key)
                        st.rerun()

                with cols[1]:
                    if st.button("➕", key=f"quick_add_{student_key}", help="Quick assign"):
                        _add_student_to_teacher(
                            grade_list, target_teacher, student.first_name, student.last_name
                        )
                        st.success(f"Assigned to {target_teacher}")
                        st.rerun()
        else:
            st.info("All students assigned! 🎉")

    with col2:
        st.subheader("Classroom Assignments")

        # Display teachers in a grid layout
        teacher_cols = st.columns(min(len(grade_list.teachers), 4))

        for idx, teacher in enumerate(grade_list.teachers):
            col_idx = idx % len(teacher_cols)
            with teacher_cols[col_idx]:
                # Teacher header with color
                bg_color, text_color = _get_teacher_color(teacher)
                clusters_str = (
                    ", ".join(str(c) for c in teacher.clusters) if teacher.clusters else ""
                )
                style_attr = f"background-color: {bg_color}; color: {text_color};"
                st.markdown(
                    f"""
                    <div class="teacher-header" style="{style_attr}">
                        <strong>{teacher.name}</strong><br>
                        <small>{clusters_str}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Get students for this teacher
                students = teacher_students.get(teacher.name, [])

                if students:
                    st.write(f"**Students: {len(students)}**")

                    # Target for moving students from this teacher
                    other_teachers = [t.name for t in grade_list.teachers if t.name != teacher.name]
                    move_target: str = "Unassigned"
                    if other_teachers:
                        move_target = st.selectbox(
                            "Move to:",
                            options=["Unassigned"] + other_teachers,
                            key=f"move_target_{teacher.name}",
                            label_visibility="collapsed",
                        )

                    # Initialize session state for selected students in this column
                    selected_key = f"selected_in_column_{teacher.name}"
                    if selected_key not in st.session_state:
                        st.session_state[selected_key] = []

                    # Display assigned students with checkboxes for selection
                    for _s_idx, student in enumerate(students):
                        display_name = _get_student_display_name(student)
                        student_key = f"{student.first_name}|{student.last_name}"

                        # Checkbox for selecting this student
                        is_checked = st.checkbox(
                            display_name,
                            key=f"chk_{teacher.name}_{student_key}",
                            value=student_key in st.session_state[selected_key],
                        )

                        if is_checked and student_key not in st.session_state[selected_key]:
                            st.session_state[selected_key].append(student_key)
                        elif not is_checked and student_key in st.session_state[selected_key]:
                            st.session_state[selected_key].remove(student_key)

                    # Move Selected button (only show if students are selected)
                    if st.session_state[selected_key]:
                        count = len(st.session_state[selected_key])
                        if st.button(
                            f"Move {count} Selected",
                            key=f"move_selected_{teacher.name}",
                            type="primary",
                            use_container_width=True,
                        ):
                            moved_count = 0
                            for student_key in st.session_state[selected_key]:
                                first_name, last_name = student_key.split("|", 1)
                                _remove_student_from_teacher(
                                    grade_list, teacher.name, first_name, last_name
                                )
                                if move_target != "Unassigned":
                                    _add_student_to_teacher(
                                        grade_list, move_target, first_name, last_name
                                    )
                                moved_count += 1

                            st.session_state[selected_key] = []
                            destination = (
                                move_target if move_target != "Unassigned" else "unassigned"
                            )
                            st.success(f"Moved {moved_count} students to {destination}")
                            st.rerun()
                else:
                    st.write("*No students assigned*")

                st.divider()

    # Bulk operations section
    st.divider()
    st.subheader("Bulk Operations")

    bulk_col1, bulk_col2, bulk_col3, bulk_col4 = st.columns(4)

    with bulk_col1:
        if st.button("Uncheck All", use_container_width=True):
            st.session_state.selected_students = []
            # Clear column-specific selections
            for teacher in grade_list.teachers:
                key = f"selected_in_column_{teacher.name}"
                if key in st.session_state:
                    st.session_state[key] = []
            st.rerun()

    with bulk_col2:
        if st.button("Unassign All", type="secondary", use_container_width=True):
            # Move all assigned students back to unassigned
            total_moved = 0
            for cls in grade_list.classes:
                for student in cls.students[:]:
                    _remove_student_from_teacher(
                        grade_list, cls.teacher.name, student.first_name, student.last_name
                    )
                    total_moved += 1
            if total_moved > 0:
                st.success(f"Unassigned {total_moved} students")
                st.rerun()
            else:
                st.info("No students to unassign")

    with bulk_col3:
        if st.button("Auto-Balance Classes", use_container_width=True):
            # Simple auto-balance: distribute unassigned students evenly
            if unassigned and grade_list.teachers:
                teacher_names = [t.name for t in grade_list.teachers]
                students_per_teacher = len(unassigned) // len(teacher_names)
                extra = len(unassigned) % len(teacher_names)

                student_idx = 0
                for t_idx, teacher_name in enumerate(teacher_names):
                    count = students_per_teacher + (1 if t_idx < extra else 0)
                    for _ in range(count):
                        if student_idx < len(unassigned):
                            student = unassigned[student_idx]
                            _add_student_to_teacher(
                                grade_list, teacher_name, student.first_name, student.last_name
                            )
                            student_idx += 1

                st.success(f"Auto-assigned {len(unassigned)} students evenly")
                st.rerun()

    with bulk_col4:
        # Show summary stats
        total_students = len(grade_list.students)
        assigned_count = total_students - len(unassigned)
        st.write(f"**Progress: {assigned_count}/{total_students} assigned**")
        progress_pct = assigned_count / total_students if total_students > 0 else 0
        st.progress(progress_pct)

    # Simulated Annealing Optimization Section
    st.divider()
    st.header("🔬 Optimize Class Assignments")
    st.write(
        "Use simulated annealing to automatically find an optimal class "
        "distribution that balances students across all classrooms."
    )

    _render_optimization_section(grade_list)


def _render_optimization_section(grade_list: GradeList) -> None:
    """Render the simulated annealing optimization section."""
    # Initialize session state for optimization
    if "optimization_running" not in st.session_state:
        st.session_state.optimization_running = False
    if "optimization_progress" not in st.session_state:
        st.session_state.optimization_progress = 0
    if "optimization_temp" not in st.session_state:
        st.session_state.optimization_temp = 0.0
    if "optimization_fitness" not in st.session_state:
        st.session_state.optimization_fitness = 0.0

    # Display current fitness
    current_fitness = calculate_fitness(grade_list)
    st.metric("Current Fitness Score", f"{current_fitness:.4f}")

    # Fitness breakdown expander
    with st.expander("📊 View Fitness Function Details", expanded=False):
        _render_fitness_details(grade_list)

    # Optimization controls
    st.subheader("Optimization Settings")

    opt_col1, opt_col2, opt_col3 = st.columns(3)

    with opt_col1:
        initial_temp = st.slider(
            "Initial Temperature",
            min_value=10.0,
            max_value=200.0,
            value=100.0,
            step=10.0,
            help="Higher values allow more exploration early on.",
        )

    with opt_col2:
        cooling_rate = st.slider(
            "Cooling Rate",
            min_value=0.95,
            max_value=0.999,
            value=0.995,
            step=0.001,
            format="%.3f",
            help="Rate at which temperature decreases. Higher = slower cooling.",
        )

    with opt_col3:
        max_iterations = st.slider(
            "Max Iterations",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000,
            help="Maximum number of iterations to run.",
        )

    # Fitness weights configuration
    with st.expander("⚖️ Configure Fitness Weights", expanded=False):
        st.write("Adjust the relative importance of each balancing factor:")

        weight_col1, weight_col2, weight_col3 = st.columns(3)

        with weight_col1:
            gender_weight = st.slider("Gender", 0.0, 5.0, 1.0, 0.5)
            math_weight = st.slider("Math", 0.0, 5.0, 0.5, 0.5)
            ela_weight = st.slider("ELA", 0.0, 5.0, 0.5, 0.5)

        with weight_col2:
            behavior_weight = st.slider("Behavior", 0.0, 5.0, 1.0, 0.5)
            class_size_weight = st.slider("Class Size", 0.0, 5.0, 1.0, 0.5)

        with weight_col3:
            resource_weight = st.slider("Resource", 0.0, 5.0, 0.5, 0.5)
            speech_weight = st.slider("Speech", 0.0, 5.0, 0.5, 0.5)

    # Check if we can run optimization
    unassigned_count = len(
        _get_unassigned_students(grade_list, _build_teacher_students_map(grade_list))
    )

    can_optimize = (
        len(grade_list.teachers) >= 2 and len(grade_list.students) > 0 and unassigned_count == 0
    )

    if not can_optimize:
        if len(grade_list.teachers) < 2:
            st.warning("Need at least 2 teachers to optimize.")
        elif len(grade_list.students) == 0:
            st.warning("No students to optimize.")
        elif unassigned_count > 0:
            st.warning(
                f"Please assign all {unassigned_count} unassigned students before optimizing."
            )

    # Run optimization button
    if st.button(
        "🚀 Run Simulated Annealing Optimization",
        type="primary",
        disabled=not can_optimize or st.session_state.optimization_running,
        use_container_width=True,
    ):
        weights = FitnessWeights(
            gender=gender_weight,
            math=math_weight,
            ela=ela_weight,
            behavior=behavior_weight,
            resource=resource_weight,
            speech=speech_weight,
            class_size=class_size_weight,
        )

        config = AnnealingConfig(
            initial_temperature=initial_temp,
            cooling_rate=cooling_rate,
            max_iterations=max_iterations,
        )

        _run_optimization(grade_list, weights, config)

    # Show results if optimization completed
    if st.session_state.get("optimization_complete"):
        st.success("✅ Optimization complete!")
        _render_optimization_results(grade_list)


def _render_fitness_details(grade_list: GradeList) -> None:
    """Render detailed information about the fitness function."""
    st.markdown("""
    ### Fitness Function Overview

    The fitness score ranges from **0.0 to 1.0**, where **1.0** represents a perfectly
    balanced class distribution. The score is computed as a weighted average of
    several component scores.
    """)

    # Get current breakdown
    breakdown = get_fitness_breakdown(grade_list)

    # Display component scores
    st.subheader("Component Scores")

    details_col1, details_col2 = st.columns(2)

    with details_col1:
        st.metric(
            "🎯 Cluster (Hard Constraint)",
            f"{breakdown['cluster']:.4f}",
            help="Binary score: 1.0 if all cluster students are with qualified teachers, "
            "0.0 if any violations exist. This is a hard constraint enforced by the algorithm.",
        )
        st.metric(
            "⚤ Gender Balance",
            f"{breakdown['gender']:.4f}",
            help="Measures how evenly male and female students are distributed across classrooms.",
        )
        st.metric(
            "📐 Math Balance",
            f"{breakdown['math']:.4f}",
            help="Measures how evenly math performance levels (High/Medium/Low) are distributed.",
        )
        st.metric(
            "📖 ELA Balance",
            f"{breakdown['ela']:.4f}",
            help="Measures how evenly ELA performance levels (High/Medium/Low) are distributed.",
        )
        st.metric(
            "🎓 Behavior Balance",
            f"{breakdown['behavior']:.4f}",
            help="Measures how evenly behavior ratings (High/Medium/Low) are distributed.",
        )

    with details_col2:
        st.metric(
            "🏥 Resource Services",
            f"{breakdown['resource']:.4f}",
            help="Measures how evenly students receiving resource services are distributed.",
        )
        st.metric(
            "🗣️ Speech Services",
            f"{breakdown['speech']:.4f}",
            help="Measures how evenly students receiving speech services are distributed.",
        )
        st.metric(
            "👥 Class Size Balance",
            f"{breakdown['class_size']:.4f}",
            help="Measures how evenly students are distributed across classroom sizes.",
        )
        st.metric(
            "📊 Overall Fitness",
            f"{breakdown['overall']:.4f}",
            help="Weighted average of all component scores (excluding cluster).",
        )

    st.markdown("""
    ### How Scores Are Calculated

    **Balance Metrics (Gender, Math, ELA, Behavior, Resource, Speech):**
    - Each metric measures how evenly the attribute is distributed across classrooms
    - Uses exponential decay: `score = exp(-average_deviation)`
    - A deviation of 0 (perfect balance) gives a score of 1.0
    - Higher deviations result in lower scores

    **Class Size Balance:**
    - Uses coefficient of variation (CV = std_dev / mean)
    - Score = `exp(-2 * CV)`
    - Perfectly equal class sizes give a score of 1.0

    **Cluster Constraint:**
    - This is a **hard constraint**, not a weighted component
    - If any student with a cluster assignment is placed with an unqualified teacher,
      the overall fitness score becomes **0.0**
    - The optimization algorithm actively prevents such moves

    **Final Score:**
    - Calculated as a weighted average: `(sum(weight_i * score_i)) / sum(weights)`
    - Cluster score acts as a binary multiplier: if 0.0, final score is 0.0
    - Result is clamped between 0.0 and 1.0
    """)


def _run_optimization(
    grade_list: GradeList, weights: FitnessWeights, config: AnnealingConfig
) -> None:
    """Run the simulated annealing optimization."""
    st.session_state.optimization_running = True
    st.session_state.optimization_complete = False

    # Progress placeholder
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    def progress_callback(iteration: int, temperature: float, fitness: float) -> None:
        """Update progress during optimization."""
        progress = min(100, int(100 * iteration / config.max_iterations))
        st.session_state.optimization_progress = progress
        st.session_state.optimization_temp = temperature
        st.session_state.optimization_fitness = fitness

        progress_placeholder.progress(progress / 100.0)
        status_placeholder.text(
            f"Iteration {iteration:,} | Temperature: {temperature:.4f} | Fitness: {fitness:.4f}"
        )

    # Store pre-optimization state
    st.session_state.pre_optimization_fitness = calculate_fitness(grade_list, weights)
    st.session_state.pre_optimization_breakdown = get_fitness_breakdown(grade_list, weights)

    # Run optimization
    optimized = optimize_grade_list(
        grade_list,
        weights=weights,
        config=config,
        progress_callback=progress_callback,
    )

    # Update grade list with optimized result
    st.session_state.grade_list = optimized

    # Store post-optimization results
    st.session_state.post_optimization_fitness = calculate_fitness(optimized, weights)
    st.session_state.post_optimization_breakdown = get_fitness_breakdown(optimized, weights)

    st.session_state.optimization_running = False
    st.session_state.optimization_complete = True

    progress_placeholder.empty()
    status_placeholder.empty()

    st.rerun()


def _render_optimization_results(grade_list: GradeList) -> None:
    """Render the optimization results comparison."""
    st.subheader("Optimization Results")

    pre_fitness = st.session_state.get("pre_optimization_fitness", 0.0)
    post_fitness = st.session_state.get("post_optimization_fitness", 0.0)
    pre_breakdown = st.session_state.get("pre_optimization_breakdown", {})
    post_breakdown = st.session_state.get("post_optimization_breakdown", {})

    # Overall improvement
    improvement_col1, improvement_col2, improvement_col3 = st.columns(3)

    with improvement_col1:
        st.metric("Before Optimization", f"{pre_fitness:.4f}")

    with improvement_col2:
        st.metric("After Optimization", f"{post_fitness:.4f}")

    with improvement_col3:
        improvement = post_fitness - pre_fitness
        improvement_pct = (improvement / pre_fitness * 100) if pre_fitness > 0 else 0
        st.metric(
            "Improvement",
            f"{improvement:.4f}",
            f"{improvement_pct:+.1f}%",
        )

    # Component comparison
    with st.expander("📊 Detailed Component Comparison"):
        comp_col1, comp_col2 = st.columns(2)

        with comp_col1:
            st.write("**Before Optimization:**")
            for key, value in pre_breakdown.items():
                st.write(f"- {key}: {value:.4f}")

        with comp_col2:
            st.write("**After Optimization:**")
            for key, value in post_breakdown.items():
                st.write(f"- {key}: {value:.4f}")

    # Clear results button
    if st.button("Clear Results", use_container_width=True):
        st.session_state.optimization_complete = False
        st.rerun()
