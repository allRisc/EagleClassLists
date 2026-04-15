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
        student.teacher = teacher.name


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
