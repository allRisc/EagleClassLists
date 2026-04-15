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

"""Teachers management page for the Streamlit app."""

from __future__ import annotations

import streamlit as st

from eagleclasslists.classlist import Cluster, GradeList, Teacher


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
            if student.teacher and student.teacher == teacher_name:
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
