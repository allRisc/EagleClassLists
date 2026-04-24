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

"""View for managing teachers."""

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
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from eagleclasslists.app.grade_list_model import GradeListModel
from eagleclasslists.data.classlist import Cluster, Teacher


class TeacherFormDialog(QDialog):
    """Dialog form for creating or editing a teacher."""

    def __init__(
        self,
        model: GradeListModel,
        teacher: Teacher | None = None,
    ) -> None:
        super().__init__()
        self.model = model
        self.editing_teacher = teacher
        self.setWindowTitle("Edit Teacher" if teacher else "Add New Teacher")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(350)
        self._setup_ui()
        if teacher:
            self._populate_fields(teacher)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        info_group = QGroupBox("Teacher Information")
        info_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.grade_combo = QComboBox()
        self.grade_combo.setEditable(True)
        self.grade_combo.addItem("")
        for grade in self.model.available_grades:
            self.grade_combo.addItem(grade)

        self.cluster_checks: dict[Cluster, QCheckBox] = {}
        cluster_layout = QVBoxLayout()
        for cluster in Cluster:
            check = QCheckBox(cluster.value)
            self.cluster_checks[cluster] = check
            cluster_layout.addWidget(check)

        info_layout.addRow("Name:", self.name_edit)
        info_layout.addRow("Grade:", self.grade_combo)
        info_layout.addRow("Cluster Qualifications:", cluster_layout)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save" if self.editing_teacher else "Add Teacher")
        self.save_button.clicked.connect(self._on_save)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def _populate_fields(self, teacher: Teacher) -> None:
        self.name_edit.setText(teacher.name)
        if teacher.grade is not None:
            grade_index = self.grade_combo.findText(teacher.grade)
            if grade_index >= 0:
                self.grade_combo.setCurrentIndex(grade_index)
            else:
                self.grade_combo.setEditText(teacher.grade)
        for cluster in teacher.clusters:
            if cluster in self.cluster_checks:
                self.cluster_checks[cluster].setChecked(True)

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Teacher name is required.")
            return

        existing = {
            t.name for t in self.model.grade_list.teachers if t is not self.editing_teacher
        }
        if name in existing:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Teacher '{name}' already exists.",
            )
            return

        clusters = [
            cluster for cluster, check in self.cluster_checks.items() if check.isChecked()
        ]

        grade_value = self.grade_combo.currentText().strip()
        grade = grade_value if grade_value else None

        teacher = Teacher(name=name, grade=grade, clusters=clusters)

        if self.editing_teacher:
            self.model.update_teacher(self.editing_teacher.name, teacher)
            QMessageBox.information(self, "Success", f"Updated teacher: {name}")
        else:
            self.model.grade_list.teachers.append(teacher)
            self.model.changed.emit()
            QMessageBox.information(self, "Success", f"Added teacher: {name}")
        self.accept()


class TeacherRow(QFrame):
    """Widget representing a single teacher row."""

    def __init__(self, teacher: Teacher, model: GradeListModel) -> None:
        super().__init__()
        self.teacher = teacher
        self.model = model
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        name_label = QLabel(self.teacher.name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(name_label)

        if self.teacher.clusters:
            cluster_str = ", ".join(c.value for c in self.teacher.clusters)
            cluster_label = QLabel(f"Clusters: {cluster_str}")
            cluster_label.setStyleSheet("font-size: 12px; color: #555;")
            left_layout.addWidget(cluster_label)
        else:
            no_cluster_label = QLabel("No cluster qualifications")
            no_cluster_label.setStyleSheet("font-size: 12px; color: #888;")
            left_layout.addWidget(no_cluster_label)

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
        dialog = TeacherFormDialog(self.model, self.teacher)
        dialog.exec()

    def _on_remove(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove {self.teacher.name}? This will also remove the teacher from all classrooms "
            f"and unassign any students.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.model.remove_teacher(self.teacher.name)


class TeachersView(QWidget):
    """View for managing teachers."""

    def __init__(self, model: GradeListModel) -> None:
        super().__init__()
        self.model = model
        self._rows: list[QWidget] = []
        self._setup_ui()
        model.changed.connect(self._refresh)

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        toolbar_layout = QHBoxLayout()

        self.new_teacher_button = QPushButton("Add New Teacher")
        self.new_teacher_button.clicked.connect(self._show_add_teacher_form)
        toolbar_layout.addWidget(self.new_teacher_button)
        toolbar_layout.addStretch()

        main_layout.addLayout(toolbar_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)

    def _show_add_teacher_form(self) -> None:
        dialog = TeacherFormDialog(self.model)
        dialog.exec()

    def _refresh(self) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()

        teachers = self.model.grade_list.teachers

        if not teachers:
            if self.model.teachers_loaded:
                msg = "No teachers in the loaded file."
            else:
                msg = "No teachers loaded. Use File > Open Teachers to load."
            label = QLabel(msg)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #888; padding: 20px;")
            self.scroll_layout.addWidget(label)
            self._rows.append(label)
            return

        for teacher in teachers:
            row = TeacherRow(teacher, self.model)
            self.scroll_layout.addWidget(row)
            self._rows.append(row)
