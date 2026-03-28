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

"""Streamlit app for managing class lists.

This module provides a web interface for adding, editing, and assigning
students to teachers, with Excel file import/export functionality.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

import streamlit as st

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


def init_session_state() -> None:
    """Initialize session state variables."""
    if "grade_list" not in st.session_state:
        st.session_state.grade_list = GradeList(classes=[], teachers=[], students=[])
    if "current_file" not in st.session_state:
        st.session_state.current_file = None
    if "teacher_to_remove" not in st.session_state:
        st.session_state.teacher_to_remove = None
    if "student_to_remove" not in st.session_state:
        st.session_state.student_to_remove = None
    if "assignment_to_remove" not in st.session_state:
        st.session_state.assignment_to_remove = None


def render_teachers_page() -> None:
    """Render the teachers management page."""
    st.header("Teachers")
    st.write("Add, edit, or remove teachers from the grade list.")

    grade_list: GradeList = st.session_state.grade_list

    # Process any pending removals
    if st.session_state.teacher_to_remove is not None:
        teacher_name = st.session_state.teacher_to_remove
        grade_list.teachers = [t for t in grade_list.teachers if t.name != teacher_name]
        grade_list.classes = [c for c in grade_list.classes if c.teacher.name != teacher_name]
        for student in grade_list.students:
            if student.teacher and student.teacher.name == teacher_name:
                student.teacher = None
        st.session_state.teacher_to_remove = None
        st.success(f"Removed teacher: {teacher_name}")
        st.rerun()

    # Add new teacher form
    with st.expander("Add New Teacher", expanded=False):
        with st.form("add_teacher_form"):
            teacher_name = st.text_input("Teacher Name", key="new_teacher_name")

            available_clusters = list(Cluster)
            selected_clusters = st.multiselect(
                "Cluster Qualifications",
                options=available_clusters,
                format_func=lambda x: x.value,
                key="new_teacher_clusters",
            )

            submitted = st.form_submit_button("Add Teacher")
            if submitted:
                if not teacher_name.strip():
                    st.error("Teacher name is required!")
                else:
                    # Check for duplicate names
                    existing_names = {t.name for t in grade_list.teachers}
                    if teacher_name.strip() in existing_names:
                        st.error(f"Teacher '{teacher_name}' already exists!")
                    else:
                        new_teacher = Teacher(
                            name=teacher_name.strip(),
                            clusters=list(selected_clusters),
                        )
                        grade_list.teachers.append(new_teacher)
                        st.success(f"Added teacher: {teacher_name}")
                        st.rerun()

    # Display existing teachers
    st.subheader("Existing Teachers")

    if not grade_list.teachers:
        st.info("No teachers added yet. Use the form above to add teachers.")
    else:
        for idx, teacher in enumerate(grade_list.teachers):
            col1, col2, col3 = st.columns([4, 3, 2])

            with col1:
                st.write(f"**{teacher.name}**")

            with col2:
                if teacher.clusters:
                    clusters_str = ", ".join(c.value for c in teacher.clusters)
                    st.write(clusters_str)
                else:
                    st.write("—")

            with col3:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Edit", key=f"edit_teacher_{idx}"):
                        st.session_state[f"editing_teacher_{idx}"] = True

                with btn_col2:
                    if st.button("Remove", key=f"remove_teacher_{idx}"):
                        st.session_state.teacher_to_remove = teacher.name

            # Edit form
            if st.session_state.get(f"editing_teacher_{idx}", False):
                with st.form(f"edit_teacher_form_{idx}"):
                    new_name = st.text_input(
                        "Name", value=teacher.name, key=f"edit_teacher_name_{idx}"
                    )
                    new_clusters = st.multiselect(
                        "Clusters",
                        options=list(Cluster),
                        default=teacher.clusters,
                        format_func=lambda x: x.value,
                        key=f"edit_teacher_clusters_{idx}",
                    )

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.form_submit_button("Save Changes"):
                            teacher.name = new_name.strip()
                            teacher.clusters = list(new_clusters)
                            st.session_state[f"editing_teacher_{idx}"] = False
                            st.success("Teacher updated!")
                            st.rerun()

                    with btn_col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state[f"editing_teacher_{idx}"] = False
                            st.rerun()


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
                academics = st.selectbox(
                    "Academics",
                    options=list(Academics),
                    format_func=lambda x: x.value,
                    key="new_student_academics",
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
                            academics=academics,
                            behavior=behavior,
                            cluster=cluster if cluster else None,
                            resource=resource,
                            speech=speech,
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
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.write(f"**{student.first_name} {student.last_name}**")
                    st.write(f"Gender: {student.gender.value}")

                with col2:
                    st.write(f"Academics: {student.academics.value}")
                    st.write(f"Behavior: {student.behavior.value}")
                    if student.cluster:
                        st.write(f"Cluster: {student.cluster.value}")
                    if student.resource:
                        st.write("Resource: Yes")
                    if student.speech:
                        st.write("Speech: Yes")

                with col3:
                    if st.button("Edit", key=f"edit_student_{idx}"):
                        st.session_state[f"editing_student_{idx}"] = True

                    if st.button("Remove", key=f"remove_student_{idx}"):
                        st.session_state.student_to_remove = (student.first_name, student.last_name)

                # Edit form
                if st.session_state.get(f"editing_student_{idx}", False):
                    with st.form(f"edit_student_form_{idx}"):
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
                            new_academics = st.selectbox(
                                "Academics",
                                options=list(Academics),
                                index=list(Academics).index(student.academics),
                                format_func=lambda x: x.value,
                                key=f"edit_academics_{idx}",
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

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Save Changes"):
                                old_first, old_last = student.first_name, student.last_name
                                student.first_name = new_first.strip()
                                student.last_name = new_last.strip()
                                student.gender = new_gender
                                student.academics = new_academics
                                student.behavior = new_behavior
                                student.cluster = new_cluster if new_cluster else None
                                student.resource = new_resource
                                student.speech = new_speech

                                # Update references in classrooms
                                for classroom in grade_list.classes:
                                    for s in classroom.students:
                                        if s.first_name == old_first and s.last_name == old_last:
                                            s.first_name = new_first.strip()
                                            s.last_name = new_last.strip()

                                st.session_state[f"editing_student_{idx}"] = False
                                st.success("Student updated!")
                                st.rerun()

                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"editing_student_{idx}"] = False
                                st.rerun()

                st.divider()


def render_assignments_page() -> None:
    """Render the assignments page for managing student-teacher assignments."""
    st.header("Student Assignments")
    st.write("Assign students to teachers by selecting a teacher for each student.")

    grade_list: GradeList = st.session_state.grade_list

    # Process any pending assignment removals
    if st.session_state.assignment_to_remove is not None:
        teacher_name, first_name, last_name = st.session_state.assignment_to_remove
        for cls in grade_list.classes:
            if cls.teacher.name == teacher_name:
                cls.students = [
                    s
                    for s in cls.students
                    if not (s.first_name == first_name and s.last_name == last_name)
                ]
                for student in cls.students:
                    if student.first_name == first_name and student.last_name == last_name:
                        student.teacher = None
                break
        st.session_state.assignment_to_remove = None
        st.success(f"Removed {first_name} {last_name} from {teacher_name}")
        st.rerun()

    if not grade_list.teachers:
        st.warning("No teachers available. Add teachers first.")
        return

    if not grade_list.students:
        st.warning("No students available. Add students first.")
        return

    # Build classroom map for quick lookup
    teacher_students: dict[str, list[Student]] = {}
    for cls in grade_list.classes:
        teacher_students[cls.teacher.name] = cls.students.copy()

    # Students not assigned to any teacher
    assigned_students = set()
    for students in teacher_students.values():
        for s in students:
            assigned_students.add((s.first_name, s.last_name))

    unassigned = [
        s for s in grade_list.students if (s.first_name, s.last_name) not in assigned_students
    ]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Unassigned Students")
        st.write(f"Count: {len(unassigned)}")

        if unassigned:
            for student in unassigned:
                st.write(f"• {student.first_name} {student.last_name}")
        else:
            st.info("All students assigned!")

    with col2:
        st.subheader("Classroom Assignments")

        # Assignment controls
        with st.expander("Bulk Assign Students", expanded=True):
            available_teachers = [t.name for t in grade_list.teachers]
            selected_teacher = st.selectbox(
                "Select Teacher",
                options=available_teachers,
                key="bulk_assign_teacher",
            )

            # Get students not assigned to this teacher
            current_teacher_students = teacher_students.get(selected_teacher, [])
            current_names = {(s.first_name, s.last_name) for s in current_teacher_students}

            available_for_assignment = [
                f"{s.first_name} {s.last_name}"
                for s in grade_list.students
                if (s.first_name, s.last_name) not in current_names
            ]

            students_to_add = st.multiselect(
                "Select Students to Assign",
                options=available_for_assignment,
                key="students_to_assign",
            )

            if st.button("Assign Selected Students"):
                teacher = next(t for t in grade_list.teachers if t.name == selected_teacher)

                # Find or create classroom
                classroom: Classroom | None = next(
                    (c for c in grade_list.classes if c.teacher.name == selected_teacher),
                    None,
                )
                if classroom is None:
                    new_classroom = Classroom(teacher=teacher, students=[])
                    grade_list.classes.append(new_classroom)
                    classroom = new_classroom

                # Add students
                for student_str in students_to_add:
                    first, last = student_str.split(" ", 1)
                    student = next(
                        s
                        for s in grade_list.students
                        if s.first_name == first and s.last_name == last
                    )
                    classroom.students.append(student)
                    student.teacher = teacher

                st.success(f"Assigned {len(students_to_add)} students to {selected_teacher}")
                st.rerun()

        # Display current assignments
        st.write("---")
        for teacher in grade_list.teachers:
            with st.container():
                st.write(f"**{teacher.name}'s Classroom**")

                teacher_classroom: Classroom | None = next(
                    (c for c in grade_list.classes if c.teacher.name == teacher.name),
                    None,
                )

                if teacher_classroom is not None and teacher_classroom.students:
                    st.write(f"Students: {len(teacher_classroom.students)}")

                    # Show students with option to remove
                    for idx, student in enumerate(teacher_classroom.students):
                        cols = st.columns([3, 1])
                        with cols[0]:
                            st.write(f"• {student.first_name} {student.last_name}")
                        with cols[1]:
                            if st.button(
                                "Remove",
                                key=f"remove_assign_{teacher.name}_{idx}",
                            ):
                                st.session_state.assignment_to_remove = (
                                    teacher.name,
                                    student.first_name,
                                    student.last_name,
                                )
                else:
                    st.write("No students assigned")

                st.divider()


def render_save_load_page() -> None:
    """Render the save/load page for Excel file operations."""
    st.header("Save / Load")
    st.write("Save your grade list to an Excel file or load from an existing file.")

    grade_list: GradeList = st.session_state.grade_list

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Save to Excel")

        if not grade_list.teachers and not grade_list.students:
            st.info("No data to save yet. Add teachers and students first.")
        else:
            st.write(f"Teachers: {len(grade_list.teachers)}")
            st.write(f"Students: {len(grade_list.students)}")
            st.write(f"Classrooms: {len(grade_list.classes)}")

            filename = st.text_input(
                "Filename",
                value="grade_list.xlsx",
                key="save_filename",
            )

            if st.button("Save to Excel"):
                try:
                    grade_list.save_to_excel(filename)
                    st.session_state.current_file = filename
                    st.success(f"Saved to {filename}")
                except Exception as e:
                    st.error(f"Error saving file: {e}")

    with col2:
        st.subheader("Load from Excel")

        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=["xlsx"],
            key="upload_excel",
        )

        if uploaded_file is not None:
            if st.button("Load File"):
                try:
                    # Save uploaded file temporarily
                    temp_path = Path("temp_upload.xlsx")
                    temp_path.write_bytes(uploaded_file.getvalue())

                    # Load the grade list
                    loaded = GradeList.from_excel(temp_path)
                    st.session_state.grade_list = loaded
                    st.session_state.current_file = uploaded_file.name

                    # Clean up temp file
                    temp_path.unlink()

                    st.success(
                        f"Loaded {len(loaded.teachers)} teachers, {len(loaded.students)} students"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading file: {e}")


def st_app() -> None:
    """Main Streamlit application entry point.

    This function sets up the Streamlit app with sidebar navigation
    and renders the appropriate page based on user selection.
    """
    st.set_page_config(
        page_title="Eagle Class Lists",
        page_icon="📚",
        layout="wide",
    )

    init_session_state()

    st.title("📚 Eagle Class Lists")
    st.write("Manage students, teachers, and classroom assignments")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        options=["Teachers", "Students", "Assignments", "Save/Load"],
    )

    # Display current file info
    if st.session_state.current_file:
        st.sidebar.info(f"Current file: {st.session_state.current_file}")

    # Display stats
    grade_list: GradeList = st.session_state.grade_list
    st.sidebar.divider()
    st.sidebar.write("**Current Data**")
    st.sidebar.write(f"Teachers: {len(grade_list.teachers)}")
    st.sidebar.write(f"Students: {len(grade_list.students)}")
    st.sidebar.write(f"Classrooms: {len(grade_list.classes)}")

    # Shutdown button
    st.sidebar.divider()
    if st.sidebar.button("🛑 Shutdown Server", type="primary"):
        st.sidebar.warning("Shutting down server...")
        os.kill(os.getpid(), signal.SIGTERM)

    # Render selected page
    if page == "Teachers":
        render_teachers_page()
    elif page == "Students":
        render_students_page()
    elif page == "Assignments":
        render_assignments_page()
    elif page == "Save/Load":
        render_save_load_page()


def run_app() -> NoReturn:
    ret = subprocess.call(["streamlit", "run", __file__])
    sys.exit(ret)


if __name__ == "__main__":
    st_app()
