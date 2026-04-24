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

"""Dialog for configuring column mapping presets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from eagleclasslists.data.settings import (
    CLASSROOM_FIELDS,
    DEFAULT_PRESET,
    DEFAULT_PRESET_NAME,
    REQUIRED_CLASSROOM_FIELDS,
    REQUIRED_STUDENT_FIELDS,
    REQUIRED_TEACHER_FIELDS,
    STUDENT_FIELDS,
    TEACHER_FIELDS,
    ColumnMappingPreset,
    ColumnMappingStore,
)

_FIELD_LABELS: dict[str, str] = {
    "name": "Teacher Name",
    "clusters": "Cluster Qualifications",
    "first_name": "First Name",
    "last_name": "Last Name",
    "gender": "Gender",
    "math": "Math Level",
    "ela": "ELA Level",
    "behavior": "Behavior Level",
    "teacher": "Requested Teacher",
    "cluster": "Cluster/Program",
    "resource": "Resource",
    "speech": "Speech",
    "exclusions": "Exclusions (Cannot Be With)",
    "teacher_name": "Teacher Name",
    "student_first_name": "Student First Name",
    "student_last_name": "Student Last Name",
}

_SHEET_LABELS: dict[str, str] = {
    "teachers_sheet": "Teachers Sheet Name",
    "students_sheet": "Students Sheet Name",
    "classrooms_sheet": "Classrooms Sheet Name",
}


class ColumnMappingDialog(QDialog):
    """Dialog for managing column mapping presets.

    Left panel: list of preset names with add/delete buttons.
    Right panel: tab widget with Teachers/Students/Classrooms tabs,
    each containing a table mapping attributes to Excel column headers,
    plus sheet name configuration.
    """

    _teachers_sheet_edit: QLineEdit
    _students_sheet_edit: QLineEdit
    _classrooms_sheet_edit: QLineEdit
    _teachers_table: QTableWidget
    _students_table: QTableWidget
    _classrooms_table: QTableWidget
    _teachers_fields: list[str]
    _students_fields: list[str]
    _classrooms_fields: list[str]

    def __init__(
        self,
        store: ColumnMappingStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._presets: dict[str, ColumnMappingPreset] = {}
        self._current_preset_name: str | None = None

        self.setWindowTitle("Column Mapping Settings")
        self.setMinimumSize(800, 500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._load_presets()
        self._setup_ui()
        self._select_preset(self._store.active_preset_name)

    def _load_presets(self) -> None:
        """Load presets from the store into local state."""
        self._presets = {p.name: p.model_copy() for p in self._store.list_presets()}
        self._current_preset_name = self._store.active_preset_name

    def _setup_ui(self) -> None:
        """Create the dialog UI."""
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([200, 600])
        main_layout.addWidget(splitter)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with preset list and buttons."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Presets:"))

        self.preset_list = QListWidget()
        self.preset_list.currentItemChanged.connect(self._on_preset_selected)
        layout.addWidget(self.preset_list)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._on_add_preset)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._on_delete_preset)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)
        return widget

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with tabs for each entity type."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_entity_tab("teachers"), "Teachers")
        self.tab_widget.addTab(self._create_entity_tab("students"), "Students")
        self.tab_widget.addTab(self._create_entity_tab("classrooms"), "Classrooms")

        layout.addWidget(self.tab_widget)
        return widget

    def _create_entity_tab(self, entity: str) -> QWidget:
        """Create a tab for configuring a specific entity type.

        Args:
            entity: One of "teachers", "students", or "classrooms".

        Returns:
            A widget containing the sheet name field and column mapping table.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        if entity == "teachers":
            fields = TEACHER_FIELDS
            required = REQUIRED_TEACHER_FIELDS
            sheet_key = "teachers_sheet"
        elif entity == "students":
            fields = STUDENT_FIELDS
            required = REQUIRED_STUDENT_FIELDS
            sheet_key = "students_sheet"
        else:
            fields = CLASSROOM_FIELDS
            required = REQUIRED_CLASSROOM_FIELDS
            sheet_key = "classrooms_sheet"

        sheet_layout = QHBoxLayout()
        sheet_label = QLabel(f"{_SHEET_LABELS[sheet_key]}:")
        sheet_layout.addWidget(sheet_label)
        sheet_line = QLineEdit()
        sheet_line.setPlaceholderText(_SHEET_LABELS[sheet_key])
        sheet_layout.addWidget(sheet_line, stretch=1)
        layout.addLayout(sheet_layout)

        setattr(self, f"_{entity}_sheet_edit", sheet_line)

        table = QTableWidget(len(fields), 2)
        table.setHorizontalHeaderLabels(["Attribute", "Excel Column Header"])

        for row, field_name in enumerate(fields):
            label = _FIELD_LABELS.get(field_name, field_name)
            if field_name in required:
                label += " *"

            attr_item = QTableWidgetItem(label)
            attr_item.setFlags(attr_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, attr_item)

            value_item = QTableWidgetItem("")
            table.setItem(row, 1, value_item)

        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()
        layout.addWidget(table)

        setattr(self, f"_{entity}_table", table)
        setattr(self, f"_{entity}_fields", fields)

        hint = QLabel("* Required field")
        hint.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(hint)

        return widget

    def _populate_from_preset(self, preset: ColumnMappingPreset) -> None:
        """Fill all tabs from the given preset.

        Args:
            preset: The preset whose values should populate the dialog.
        """
        self._teachers_sheet_edit.setText(preset.teachers_sheet)
        self._students_sheet_edit.setText(preset.students_sheet)
        self._classrooms_sheet_edit.setText(preset.classrooms_sheet)

        self._populate_table("teachers", preset.teacher_columns)
        self._populate_table("students", preset.student_columns)
        self._populate_table("classrooms", preset.classroom_columns)

    def _populate_table(
        self, entity: str, columns: dict[str, str]
    ) -> None:
        """Fill a column mapping table from preset data.

        Args:
            entity: One of "teachers", "students", or "classrooms".
            columns: The column mapping from the preset.
        """
        table: QTableWidget = getattr(self, f"_{entity}_table")
        fields: list[str] = getattr(self, f"_{entity}_fields")

        for row, field_name in enumerate(fields):
            value = columns.get(field_name, "")
            item = table.item(row, 1)
            if item is not None:
                item.setText(value)

    def _collect_preset(self) -> ColumnMappingPreset:
        """Collect current dialog values into a ColumnMappingPreset.

        Returns:
            A new preset from the dialog values.
        """
        teacher_columns = self._collect_table("teachers")
        student_columns = self._collect_table("students")
        classroom_columns = self._collect_table("classrooms")

        return ColumnMappingPreset(
            name=self._current_preset_name or "New Preset",
            teachers_sheet=self._teachers_sheet_edit.text(),
            students_sheet=self._students_sheet_edit.text(),
            classrooms_sheet=self._classrooms_sheet_edit.text(),
            teacher_columns=teacher_columns,
            student_columns=student_columns,
            classroom_columns=classroom_columns,
        )

    def _collect_table(self, entity: str) -> dict[str, str]:
        """Extract column mapping from a table widget.

        Args:
            entity: One of "teachers", "students", or "classrooms".

        Returns:
            A dict mapping attribute names to column header strings.
        """
        table: QTableWidget = getattr(self, f"_{entity}_table")
        fields: list[str] = getattr(self, f"_{entity}_fields")
        result: dict[str, str] = {}
        for row, field_name in enumerate(fields):
            item = table.item(row, 1)
            value = item.text().strip() if item is not None else ""
            if value:
                result[field_name] = value
        return result

    def _select_preset(self, name: str) -> None:
        """Select a preset by name in the list widget.

        Args:
            name: The preset name to select.
        """
        for i in range(self.preset_list.count()):
            item = self.preset_list.item(i)
            if item.text() == name:
                self.preset_list.setCurrentItem(item)
                return

    def _on_preset_selected(self) -> None:
        """Handle preset selection change in the list widget."""
        self._save_current_preset()
        current_item = self.preset_list.currentItem()
        if current_item is None:
            return

        preset_name = current_item.text()
        self._current_preset_name = preset_name
        preset = self._presets.get(preset_name, DEFAULT_PRESET)
        self._populate_from_preset(preset)

        is_default = preset_name == DEFAULT_PRESET_NAME
        self.delete_button.setEnabled(not is_default)

    def _save_current_preset(self) -> None:
        """Save current dialog values into the local presets dict."""
        if self._current_preset_name is None:
            return
        preset = self._collect_preset()
        self._presets[self._current_preset_name] = preset

    def _refresh_preset_list(self) -> None:
        """Refresh the preset list without changing selection."""
        self.preset_list.blockSignals(True)
        current_name = self._current_preset_name
        self.preset_list.clear()
        for name in sorted(self._presets.keys()):
            self.preset_list.addItem(name)
        self._select_preset(current_name or DEFAULT_PRESET_NAME)
        self.preset_list.blockSignals(False)

    def _on_add_preset(self) -> None:
        """Handle the Add Preset button click."""
        name, ok = QInputDialog.getText(
            self, "New Preset", "Preset name:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._presets:
            QMessageBox.warning(
                self, "Duplicate Name", f"A preset named '{name}' already exists."
            )
            return

        new_preset = ColumnMappingPreset(name=name)
        self._presets[name] = new_preset
        self._refresh_preset_list()
        self._select_preset(name)

    def _on_delete_preset(self) -> None:
        """Handle the Delete Preset button click."""
        current_item = self.preset_list.currentItem()
        if current_item is None:
            return

        name = current_item.text()
        if name == DEFAULT_PRESET_NAME:
            QMessageBox.warning(
                self, "Cannot Delete", "The default preset cannot be deleted."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete the preset '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self._presets[name]
            if self._current_preset_name == name:
                self._current_preset_name = DEFAULT_PRESET_NAME
            self._refresh_preset_list()

    def _on_ok(self) -> None:
        """Handle the OK button — validate and accept."""
        self._save_current_preset()

        for name, preset in self._presets.items():
            validation_issues = self._validate_preset(preset)
            if validation_issues:
                QMessageBox.warning(
                    self,
                    f"Invalid Preset: {name}",
                    "\n".join(validation_issues),
                )
                return

        existing_names = {p.name for p in self._store.list_presets()}
        for name, preset in self._presets.items():
            if name == DEFAULT_PRESET_NAME:
                continue
            if name in existing_names:
                self._store.delete_preset(name)
            self._store.add_preset(preset)

        active = self._presets.get(
            self._current_preset_name or DEFAULT_PRESET_NAME, DEFAULT_PRESET
        )
        self._store.active_preset = active

        self.accept()

    def _validate_preset(self, preset: ColumnMappingPreset) -> list[str]:
        """Validate a preset and return a list of issues.

        Args:
            preset: The preset to validate.

        Returns:
            A list of validation issue strings. Empty if valid.
        """
        issues: list[str] = []

        for field in REQUIRED_TEACHER_FIELDS:
            if field not in preset.teacher_columns or not preset.teacher_columns[field]:
                label = _FIELD_LABELS.get(field, field)
                issues.append(f"Teachers: '{label}' is required")

        for field in REQUIRED_STUDENT_FIELDS:
            if field not in preset.student_columns or not preset.student_columns[field]:
                label = _FIELD_LABELS.get(field, field)
                issues.append(f"Students: '{label}' is required")

        for field in REQUIRED_CLASSROOM_FIELDS:
            if field not in preset.classroom_columns or not preset.classroom_columns[field]:
                label = _FIELD_LABELS.get(field, field)
                issues.append(f"Classrooms: '{label}' is required")

        if not preset.teachers_sheet.strip():
            issues.append("Teachers sheet name cannot be empty")
        if not preset.students_sheet.strip():
            issues.append("Students sheet name cannot be empty")
        if not preset.classrooms_sheet.strip():
            issues.append("Classrooms sheet name cannot be empty")

        return issues
