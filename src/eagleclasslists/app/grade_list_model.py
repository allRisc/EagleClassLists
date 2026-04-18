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

from PySide6.QtCore import QObject, Signal

from eagleclasslists.classlist import GradeList, Student


class GradeListModel(QObject):
    """Wraps a GradeList and emits signals when data changes.

    Views connect to the ``changed`` signal to react to updates.
    """

    changed = Signal()

    def __init__(self, grade_list: GradeList) -> None:
        super().__init__()
        self._grade_list = grade_list

    @property
    def grade_list(self) -> GradeList:
        """Access the underlying GradeList without emitting a signal."""
        return self._grade_list

    def set_grade_list(self, grade_list: GradeList) -> None:
        """Replace the entire GradeList and notify all connected views."""
        self._grade_list = grade_list
        self.changed.emit()

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
