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

"""View for managing students."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from eagleclasslists.app.grade_list_model import GradeListModel
from eagleclasslists.classlist import Student


class StudentRow(QFrame):
    """Widget representing a single student row."""

    def __init__(self, student: Student, model: GradeListModel) -> None:
        super().__init__()
        self.student = student
        self.model = model
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        name_label = QLabel(f"{self.student.first_name} {self.student.last_name}")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(name_label)

        summary = self.student.summary_string(self.model.grade_list.students)
        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("font-size: 12px; color: #555;")
        left_layout.addWidget(summary_label)

        layout.addLayout(left_layout, stretch=1)

        button_layout = QHBoxLayout()

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit)
        button_layout.addWidget(edit_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._on_remove)
        button_layout.addWidget(remove_btn)

        layout.addLayout(button_layout)

    def _on_edit(self) -> None:
        QMessageBox.information(self, "Edit Student", "Edit functionality not yet implemented.")

    def _on_remove(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove {self.student.first_name} {self.student.last_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.model.remove_student(self.student.first_name, self.student.last_name)


class StudentsView(QWidget):
    """View for managing students."""

    def __init__(self, model: GradeListModel) -> None:
        super().__init__()
        self.model = model
        self._rows: list[QWidget] = []
        self._setup_ui()
        model.changed.connect(self._refresh)

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)

    def _refresh(self) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()

        students = self.model.grade_list.students

        if not students:
            label = QLabel("No students added yet.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #888; padding: 20px;")
            self.scroll_layout.addWidget(label)
            self._rows.append(label)  # type: ignore[arg-type]
            return

        for student in students:
            row = StudentRow(student, self.model)
            self.scroll_layout.addWidget(row)
            self._rows.append(row)
