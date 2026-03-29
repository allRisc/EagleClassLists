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

"""Student assignments page for the Streamlit app."""

from __future__ import annotations

import streamlit as st

from eagleclasslists.classlist import Classroom, GradeList, Student


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
