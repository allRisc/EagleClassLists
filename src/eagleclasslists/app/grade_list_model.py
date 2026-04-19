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

"""Qt-compatible model wrapper around GradeList for shared app state."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from eagleclasslists.classlist import (
    Classroom,
    GradeList,
    Student,
    Teacher,
)


class GradeListModel(QObject):
    """Wraps a GradeList and emits signals when data changes.

    Views connect to the ``changed`` signal to react to updates.
    """

    changed = Signal()

    def __init__(self, grade_list: GradeList) -> None:
        super().__init__()
        self._grade_list = grade_list
        self._teachers_loaded = False
        self._students_loaded = False
        self._classrooms_loaded = False

    @property
    def grade_list(self) -> GradeList:
        """Access the underlying GradeList without emitting a signal."""
        return self._grade_list

    @property
    def teachers_loaded(self) -> bool:
        """Whether teachers have been loaded from a file."""
        return self._teachers_loaded

    @property
    def students_loaded(self) -> bool:
        """Whether students have been loaded from a file."""
        return self._students_loaded

    @property
    def classrooms_loaded(self) -> bool:
        """Whether classrooms have been loaded from a file."""
        return self._classrooms_loaded

    def set_grade_list(self, grade_list: GradeList) -> None:
        """Replace the entire GradeList and notify all connected views."""
        self._grade_list = grade_list
        self._reset_loaded_flags()
        self.changed.emit()

    def _reset_loaded_flags(self) -> None:
        """Reset all loaded-state tracking flags."""
        self._teachers_loaded = False
        self._students_loaded = False
        self._classrooms_loaded = False

    # ------------------------------------------------------------------
    # Per-entity load
    # ------------------------------------------------------------------

    def load_teachers(self, filepath: str | Path) -> None:
        """Load teachers from an Excel file and replace the current list.

        Args:
            filepath: Path to the teachers Excel file.

        Raises:
            ExcelImportError: If the file cannot be read or validated.
        """
        teachers = GradeList.load_teachers_from_excel(filepath)
        self._grade_list.teachers = teachers
        self._teachers_loaded = True
        self.changed.emit()

    def load_students(self, filepath: str | Path) -> None:
        """Load students from an Excel file and replace the current list.

        Args:
            filepath: Path to the students Excel file.

        Raises:
            ExcelImportError: If the file cannot be read or validated.
        """
        students = GradeList.load_students_from_excel(filepath)
        self._grade_list.students = students
        self._students_loaded = True
        self.changed.emit()

    def load_classrooms(self, filepath: str | Path) -> None:
        """Load classroom assignments from an Excel file.

        Requires that teachers and students are already loaded.

        Args:
            filepath: Path to the classrooms Excel file.

        Raises:
            ExcelImportError: If the file cannot be read, validated,
                or if teacher/student references are missing.
        """
        classrooms = GradeList.load_classrooms_from_excel(
            filepath,
            self._grade_list.teachers,
            self._grade_list.students,
        )
        self._grade_list.classes = classrooms
        self._classrooms_loaded = True
        self.changed.emit()

    # ------------------------------------------------------------------
    # Per-entity save
    # ------------------------------------------------------------------

    def save_teachers(self, filepath: str | Path) -> None:
        """Save teachers to an Excel file.

        Args:
            filepath: Path to write the teachers Excel file.
        """
        self._grade_list.save_teachers_to_excel(filepath)

    def save_students(self, filepath: str | Path) -> None:
        """Save students to an Excel file.

        Args:
            filepath: Path to write the students Excel file.
        """
        self._grade_list.save_students_to_excel(filepath)

    def save_classrooms(self, filepath: str | Path) -> None:
        """Save classroom assignments to an Excel file.

        Args:
            filepath: Path to write the classrooms Excel file.
        """
        self._grade_list.save_classrooms_to_excel(filepath)

    def remove_student(self, first_name: str, last_name: str) -> None:
        """Remove a student from the grade list and all classrooms.

        Args:
            first_name: The student's first name.
            last_name: The student's last name.
        """
        self._grade_list.students = [
            s
            for s in self._grade_list.students
            if not (s.first_name == first_name and s.last_name == last_name)
        ]
        for classroom in self._grade_list.classes:
            classroom.students = [
                s
                for s in classroom.students
                if not (s.first_name == first_name and s.last_name == last_name)
            ]
        self.changed.emit()

    def update_student(
        self,
        old_first_name: str,
        old_last_name: str,
        new_student: Student,
    ) -> None:
        """Update a student's information in the grade list and classrooms.

        Args:
            old_first_name: The student's original first name.
            old_last_name: The student's original last name.
            new_student: The updated Student object.
        """
        for i, student in enumerate(self._grade_list.students):
            if student.first_name == old_first_name and student.last_name == old_last_name:
                self._grade_list.students[i] = new_student
                break

        for classroom in self._grade_list.classes:
            for i, student in enumerate(classroom.students):
                if student.first_name == old_first_name and student.last_name == old_last_name:
                    classroom.students[i] = new_student
                    break

        self.changed.emit()

    def remove_teacher(self, name: str) -> None:
        """Remove a teacher from the grade list and all classrooms.

        Args:
            name: The teacher's name.
        """
        self._grade_list.teachers = [
            t for t in self._grade_list.teachers if t.name != name
        ]
        self._grade_list.classes = [
            c for c in self._grade_list.classes if c.teacher.name != name
        ]
        for student in self._grade_list.students:
            if student.teacher == name:
                student.teacher = None
        self.changed.emit()

    def update_teacher(self, old_name: str, new_teacher: Teacher) -> None:
        """Update a teacher's information in the grade list and classrooms.

        Args:
            old_name: The teacher's original name.
            new_teacher: The updated Teacher object.
        """
        for i, teacher in enumerate(self._grade_list.teachers):
            if teacher.name == old_name:
                self._grade_list.teachers[i] = new_teacher
                break

        for classroom in self._grade_list.classes:
            if classroom.teacher.name == old_name:
                classroom.teacher = new_teacher
                break

        for student in self._grade_list.students:
            if student.teacher == old_name:
                student.teacher = new_teacher.name

        self.changed.emit()

    def add_student_to_classroom(self, teacher_name: str, first_name: str, last_name: str) -> None:
        """Add a student to a teacher's classroom, creating it if needed.

        Args:
            teacher_name: The teacher's name.
            first_name: The student's first name.
            last_name: The student's last name.
        """
        teacher = next(
            (t for t in self._grade_list.teachers if t.name == teacher_name), None
        )
        if teacher is None:
            return

        student = next(
            (
                s
                for s in self._grade_list.students
                if s.first_name == first_name and s.last_name == last_name
            ),
            None,
        )
        if student is None:
            return

        classroom: Classroom | None = next(
            (c for c in self._grade_list.classes if c.teacher.name == teacher_name),
            None,
        )
        if classroom is None:
            classroom = Classroom(teacher=teacher, students=[])
            self._grade_list.classes.append(classroom)

        already_assigned = any(
            s.first_name == first_name and s.last_name == last_name
            for s in classroom.students
        )
        if not already_assigned:
            classroom.students.append(student)
            self.changed.emit()

    def remove_student_from_classroom(
        self, teacher_name: str, first_name: str, last_name: str
    ) -> None:
        """Remove a student from a specific classroom.

        Args:
            teacher_name: The teacher's name.
            first_name: The student's first name.
            last_name: The student's last name.
        """
        for classroom in self._grade_list.classes:
            if classroom.teacher.name == teacher_name:
                classroom.students = [
                    s
                    for s in classroom.students
                    if not (s.first_name == first_name and s.last_name == last_name)
                ]
                self.changed.emit()
                return

    def unassign_all_students(self) -> None:
        """Remove all students from all classrooms."""
        for classroom in self._grade_list.classes:
            classroom.students.clear()
        self.changed.emit()
