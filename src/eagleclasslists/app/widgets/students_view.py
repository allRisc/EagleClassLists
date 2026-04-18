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
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from eagleclasslists.app.grade_list_model import GradeListModel
from eagleclasslists.classlist import ELA, Behavior, Cluster, Gender, Math, Student


class StudentFormDialog(QDialog):
    """Dialog form for creating or editing a student."""

    def __init__(
        self,
        model: GradeListModel,
        student: Student | None = None,
    ) -> None:
        super().__init__()
        self.model = model
        self.editing_student = student
        self.setWindowTitle("Edit Student" if student else "Add New Student")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(400)
        self._setup_ui()
        if student:
            self._populate_fields(student)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        columns_layout = QHBoxLayout()

        left_column = QVBoxLayout()

        personal_group = QGroupBox("Personal Information")
        personal_layout = QFormLayout()

        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.gender_combo = QComboBox()
        for gender in Gender:
            self.gender_combo.addItem(gender.value)

        personal_layout.addRow("First Name:", self.first_name_edit)
        personal_layout.addRow("Last Name:", self.last_name_edit)
        personal_layout.addRow("Gender:", self.gender_combo)
        personal_group.setLayout(personal_layout)
        left_column.addWidget(personal_group)

        academic_group = QGroupBox("Academic Information")
        academic_layout = QFormLayout()

        self.math_combo = QComboBox()
        for math_level in Math:
            self.math_combo.addItem(math_level.value)

        self.ela_combo = QComboBox()
        for ela_level in ELA:
            self.ela_combo.addItem(ela_level.value)

        self.behavior_combo = QComboBox()
        for behavior_level in Behavior:
            self.behavior_combo.addItem(behavior_level.value)

        self.cluster_combo = QComboBox()
        self.cluster_combo.addItem("None")
        for cluster in Cluster:
            self.cluster_combo.addItem(cluster.value)

        academic_layout.addRow("Math:", self.math_combo)
        academic_layout.addRow("ELA:", self.ela_combo)
        academic_layout.addRow("Behavior:", self.behavior_combo)
        academic_layout.addRow("Cluster:", self.cluster_combo)
        academic_group.setLayout(academic_layout)
        left_column.addWidget(academic_group)

        services_group = QGroupBox("Services")
        services_layout = QVBoxLayout()

        self.resource_checkbox = QCheckBox("Resource Services")
        self.speech_checkbox = QCheckBox("Speech Services")

        services_layout.addWidget(self.resource_checkbox)
        services_layout.addWidget(self.speech_checkbox)
        services_group.setLayout(services_layout)
        left_column.addWidget(services_group)

        left_column.addStretch()
        columns_layout.addLayout(left_column)

        right_column = QVBoxLayout()

        assignment_group = QGroupBox("Assignment")
        assignment_layout = QFormLayout()

        self.teacher_combo = QComboBox()
        self.teacher_combo.addItem("None")
        for teacher in self.model.grade_list.teachers:
            self.teacher_combo.addItem(teacher.name)

        assignment_layout.addRow("Teacher:", self.teacher_combo)
        assignment_group.setLayout(assignment_layout)
        right_column.addWidget(assignment_group)

        exclusions_group = QGroupBox("Exclusions")
        exclusions_layout = QVBoxLayout()

        self.exclusions_list = QListWidget()
        self.exclusions_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        for student in self.model.grade_list.students:
            name = f"{student.first_name} {student.last_name}"
            self.exclusions_list.addItem(name)

        exclusions_label = QLabel("Select students this student cannot be placed with:")
        exclusions_layout.addWidget(exclusions_label)
        exclusions_layout.addWidget(self.exclusions_list)
        exclusions_group.setLayout(exclusions_layout)
        right_column.addWidget(exclusions_group)

        right_column.addStretch()
        columns_layout.addLayout(right_column)

        layout.addLayout(columns_layout)

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save" if self.editing_student else "Add Student")
        self.save_button.clicked.connect(self._on_save)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def _populate_fields(self, student: Student) -> None:
        self.first_name_edit.setText(student.first_name)
        self.last_name_edit.setText(student.last_name)

        self.gender_combo.setCurrentIndex(list(Gender).index(student.gender))
        self.math_combo.setCurrentIndex(list(Math).index(student.math))
        self.ela_combo.setCurrentIndex(list(ELA).index(student.ela))
        self.behavior_combo.setCurrentIndex(list(Behavior).index(student.behavior))

        if student.cluster:
            cluster_index = list(Cluster).index(student.cluster) + 1
        else:
            cluster_index = 0
        self.cluster_combo.setCurrentIndex(cluster_index)

        self.resource_checkbox.setChecked(student.resource)
        self.speech_checkbox.setChecked(student.speech)

        if student.teacher:
            teacher_index = self.teacher_combo.findText(student.teacher)
            if teacher_index >= 0:
                self.teacher_combo.setCurrentIndex(teacher_index)

        for i in range(self.exclusions_list.count()):
            item = self.exclusions_list.item(i)
            if item.text() in student.exclusions:
                item.setSelected(True)

    def _on_save(self) -> None:
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()

        if not first_name:
            QMessageBox.warning(self, "Validation Error", "First name is required.")
            return

        if not last_name:
            QMessageBox.warning(self, "Validation Error", "Last name is required.")
            return

        existing = {
            (s.first_name, s.last_name)
            for s in self.model.grade_list.students
            if s is not self.editing_student
        }
        if (first_name, last_name) in existing:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Student '{first_name} {last_name}' already exists.",
            )
            return

        cluster_value = self.cluster_combo.currentText()
        cluster = None
        for c in Cluster:
            if c.value == cluster_value:
                cluster = c
                break

        teacher_value = self.teacher_combo.currentText()
        teacher = None if teacher_value == "None" else teacher_value

        exclusions = []
        for i in range(self.exclusions_list.count()):
            item = self.exclusions_list.item(i)
            if item.isSelected():
                exclusions.append(item.text())

        student = Student(
            first_name=first_name,
            last_name=last_name,
            gender=list(Gender)[self.gender_combo.currentIndex()],
            math=list(Math)[self.math_combo.currentIndex()],
            ela=list(ELA)[self.ela_combo.currentIndex()],
            behavior=list(Behavior)[self.behavior_combo.currentIndex()],
            cluster=cluster,
            resource=self.resource_checkbox.isChecked(),
            speech=self.speech_checkbox.isChecked(),
            teacher=teacher,
            exclusions=exclusions,
        )

        if self.editing_student:
            self.model.update_student(
                self.editing_student.first_name,
                self.editing_student.last_name,
                student,
            )
            QMessageBox.information(self, "Success", f"Updated student: {first_name} {last_name}")
        else:
            self.model.grade_list.students.append(student)
            self.model.changed.emit()
            QMessageBox.information(self, "Success", f"Added student: {first_name} {last_name}")
        self.accept()


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
        dialog = StudentFormDialog(self.model, self.student)
        dialog.exec()

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

        toolbar_layout = QHBoxLayout()

        self.new_student_button = QPushButton("Add New Student")
        self.new_student_button.clicked.connect(self._show_add_student_form)
        toolbar_layout.addWidget(self.new_student_button)
        toolbar_layout.addStretch()

        main_layout.addLayout(toolbar_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)

    def _show_add_student_form(self) -> None:
        dialog = StudentFormDialog(self.model)
        dialog.exec()

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
            self._rows.append(label)
            return

        for student in students:
            row = StudentRow(student, self.model)
            self.scroll_layout.addWidget(row)
            self._rows.append(row)
