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

"""Students management page for the Streamlit app."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

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


def _get_valid_exclusions(student: Student, all_students: list[Student]) -> list[str]:
    """Get list of valid exclusions (students that actually exist).

    Args:
        student: The student whose exclusions to check.
        all_students: List of all students in the grade.

    Returns:
        List of exclusion names that correspond to existing students.
    """
    existing_names = {f"{s.first_name} {s.last_name}" for s in all_students}
    return [ex for ex in student.exclusions if ex in existing_names]


def _get_orphaned_exclusions(student: Student, all_students: list[Student]) -> list[str]:
    """Get list of orphaned exclusions (students that no longer exist).

    Args:
        student: The student whose exclusions to check.
        all_students: List of all students in the grade.

    Returns:
        List of exclusion names that don't correspond to any existing student.
    """
    existing_names = {f"{s.first_name} {s.last_name}" for s in all_students}
    return [ex for ex in student.exclusions if ex not in existing_names]


def render_students_page() -> None:
    """Render the students management page."""
    st.header("Students")
    st.write("Add, edit, or remove students from the grade list.")

    grade_list: GradeList = st.session_state.grade_list

    # Process any pending student removals
    if st.session_state.student_to_remove is not None:
        first_name, last_name = st.session_state.student_to_remove
        grade_list.students = [
            s
            for s in grade_list.students
            if not (s.first_name == first_name and s.last_name == last_name)
        ]
        for classroom in grade_list.classes:
            classroom.students = [
                s
                for s in classroom.students
                if not (s.first_name == first_name and s.last_name == last_name)
            ]
        st.session_state.student_to_remove = None
        st.success(f"Removed student: {first_name} {last_name}")
        st.rerun()

    # Add new student form
    with st.expander("Add New Student", expanded=False):
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name", key="new_student_first")
                gender = st.selectbox(
                    "Gender",
                    options=list(Gender),
                    format_func=lambda x: x.value,
                    key="new_student_gender",
                )
                math = st.selectbox(
                    "Math",
                    options=list(Math),
                    format_func=lambda x: x.value,
                    key="new_student_math",
                )
                ela = st.selectbox(
                    "ELA",
                    options=list(ELA),
                    format_func=lambda x: x.value,
                    key="new_student_ela",
                )
                cluster = st.selectbox(
                    "Cluster (optional)",
                    options=[None] + list(Cluster),
                    format_func=lambda x: x.value if x else "None",
                    key="new_student_cluster",
                )

            with col2:
                last_name = st.text_input("Last Name", key="new_student_last")
                behavior = st.selectbox(
                    "Behavior",
                    options=list(Behavior),
                    format_func=lambda x: x.value,
                    key="new_student_behavior",
                )
                resource = st.checkbox("Resource Services", key="new_student_resource")
                speech = st.checkbox("Speech Services", key="new_student_speech")

                # Teacher assignment (optional)
                teacher_options: list[Teacher | None] = [None, *grade_list.teachers]
                selected_teacher = st.selectbox(
                    "Teacher (optional)",
                    options=teacher_options,
                    format_func=lambda x: x.name if x else "None",
                    key="new_student_teacher",
                )

                # Exclusions (optional)
                exclusion_options = [f"{s.first_name} {s.last_name}" for s in grade_list.students]
                selected_exclusions = st.multiselect(
                    "Exclusions (cannot be with these students)",
                    options=exclusion_options,
                    default=[],
                    key="new_student_exclusions",
                )

            submitted = st.form_submit_button("Add Student")
            if submitted:
                if not first_name.strip():
                    st.error("First name is required!")
                elif not last_name.strip():
                    st.error("Last name is required!")
                else:
                    # Check for duplicates
                    existing = {(s.first_name, s.last_name) for s in grade_list.students}
                    if (first_name.strip(), last_name.strip()) in existing:
                        st.error(f"Student '{first_name} {last_name}' already exists!")
                    else:
                        new_student = Student(
                            first_name=first_name.strip(),
                            last_name=last_name.strip(),
                            gender=gender,
                            math=math,
                            ela=ela,
                            behavior=behavior,
                            cluster=cluster if cluster else None,
                            resource=resource,
                            speech=speech,
                            teacher=selected_teacher.name if selected_teacher else None,
                            exclusions=selected_exclusions,
                        )
                        grade_list.students.append(new_student)
                    st.success(f"Added student: {first_name} {last_name}")
                    st.rerun()

    # Display existing students
    st.subheader("Existing Students")

    if not grade_list.students:
        st.info("No students added yet. Use the form above to add students.")
    else:
        for idx, student in enumerate(grade_list.students):
            col1, col2, col3 = st.columns([3, 4, 2])

            with col1:
                st.write(f"**{student.first_name} {student.last_name}**")

            with col2:
                attrs = [
                    student.gender.value,
                    f"🔢 {student.math.value}",
                    f"📚 {student.ela.value}",
                    f"😊 {student.behavior.value}",
                ]
                if student.cluster:
                    attrs.append(f"🎯 {student.cluster.value}")
                if student.resource:
                    attrs.append("🔧 Resource")
                if student.speech:
                    attrs.append("🗣️ Speech")
                if student.teacher:
                    attrs.append(f"👨‍🏫 {student.teacher}")
                if student.exclusions:
                    # Check for orphaned exclusions
                    valid_exclusions = _get_valid_exclusions(student, grade_list.students)
                    orphaned_count = len(student.exclusions) - len(valid_exclusions)
                    if orphaned_count > 0:
                        attrs.append(f"🚫 {len(student.exclusions)} ({orphaned_count} orphaned)")
                    else:
                        attrs.append(f"🚫 {len(student.exclusions)}")
                st.write(" • ".join(attrs))

            with col3:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Edit", key=f"edit_student_{idx}"):
                        st.session_state[f"editing_student_{idx}"] = True

                with btn_col2:
                    if st.button("Remove", key=f"remove_student_{idx}"):
                        st.session_state.student_to_remove = (student.first_name, student.last_name)

            # Edit form
            if st.session_state.get(f"editing_student_{idx}", False):
                with st.form(f"edit_student_form_{idx}"):
                    # Check for orphaned exclusions (inside form)
                    orphaned = _get_orphaned_exclusions(student, grade_list.students)
                    if orphaned:
                        st.warning(f"⚠️ Orphaned exclusions will be removed: {', '.join(orphaned)}")

                    c1, c2 = st.columns(2)

                    with c1:
                        new_first = st.text_input(
                            "First Name",
                            value=student.first_name,
                            key=f"edit_first_{idx}",
                        )
                        new_gender = st.selectbox(
                            "Gender",
                            options=list(Gender),
                            index=list(Gender).index(student.gender),
                            format_func=lambda x: x.value,
                            key=f"edit_gender_{idx}",
                        )
                        new_math = st.selectbox(
                            "Math",
                            options=list(Math),
                            index=list(Math).index(student.math),
                            format_func=lambda x: x.value,
                            key=f"edit_math_{idx}",
                        )
                        new_ela = st.selectbox(
                            "ELA",
                            options=list(ELA),
                            index=list(ELA).index(student.ela),
                            format_func=lambda x: x.value,
                            key=f"edit_ela_{idx}",
                        )
                        cluster_options: Sequence[Cluster | None] = [None, *list(Cluster)]
                        new_cluster = st.selectbox(
                            "Cluster",
                            options=list(cluster_options),
                            index=cluster_options.index(student.cluster)
                            if student.cluster in cluster_options
                            else 0,
                            format_func=lambda x: x.value if x else "None",
                            key=f"edit_cluster_{idx}",
                        )

                    with c2:
                        new_last = st.text_input(
                            "Last Name",
                            value=student.last_name,
                            key=f"edit_last_{idx}",
                        )
                        new_behavior = st.selectbox(
                            "Behavior",
                            options=list(Behavior),
                            index=list(Behavior).index(student.behavior),
                            format_func=lambda x: x.value,
                            key=f"edit_behavior_{idx}",
                        )
                        new_resource = st.checkbox(
                            "Resource",
                            value=student.resource,
                            key=f"edit_resource_{idx}",
                        )
                        new_speech = st.checkbox(
                            "Speech",
                            value=student.speech,
                            key=f"edit_speech_{idx}",
                        )

                        # Teacher assignment (optional)
                        edit_teacher_options: list[Teacher | None] = [
                            None,
                            *grade_list.teachers,
                        ]
                        # Find current teacher index
                        current_teacher_idx = 0
                        if student.teacher:
                            for i, t in enumerate(edit_teacher_options):
                                if t and t.name == student.teacher:
                                    current_teacher_idx = i
                                    break
                        new_teacher = st.selectbox(
                            "Teacher",
                            options=edit_teacher_options,
                            index=current_teacher_idx,
                            format_func=lambda x: x.name if x else "None",
                            key=f"edit_teacher_{idx}",
                        )

                        # Exclusions (optional)
                        edit_exclusion_options = [
                            f"{s.first_name} {s.last_name}"
                            for s in grade_list.students
                            if s.first_name != student.first_name
                            or s.last_name != student.last_name
                        ]
                        # Only show valid exclusions as default (filter out orphaned)
                        valid_current_exclusions = [
                            ex for ex in student.exclusions if ex in edit_exclusion_options
                        ]
                        new_exclusions = st.multiselect(
                            "Exclusions",
                            options=edit_exclusion_options,
                            default=valid_current_exclusions,
                            key=f"edit_exclusions_{idx}",
                        )

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.form_submit_button("Save Changes"):
                            old_first, old_last = student.first_name, student.last_name
                            student.first_name = new_first.strip()
                            student.last_name = new_last.strip()
                            student.gender = new_gender
                            student.math = new_math
                            student.ela = new_ela
                            student.behavior = new_behavior
                            student.cluster = new_cluster if new_cluster else None
                            student.resource = new_resource
                            student.speech = new_speech
                            student.teacher = new_teacher.name if new_teacher else None
                            # Clean up orphaned exclusions on save
                            # Get all existing student names from grade list
                            existing_names = {
                                f"{s.first_name} {s.last_name}" for s in grade_list.students
                            }
                            # Filter new exclusions to only include valid ones
                            student.exclusions = [
                                ex for ex in new_exclusions if ex in existing_names
                            ]

                            # Update references in classrooms
                            for classroom in grade_list.classes:
                                for s in classroom.students:
                                    if s.first_name == old_first and s.last_name == old_last:
                                        s.first_name = new_first.strip()
                                        s.last_name = new_last.strip()
                                        s.teacher = new_teacher.name if new_teacher else None

                            st.session_state[f"editing_student_{idx}"] = False
                            st.success("Student updated!")
                            st.rerun()

                    with btn_col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state[f"editing_student_{idx}"] = False
                            st.rerun()
