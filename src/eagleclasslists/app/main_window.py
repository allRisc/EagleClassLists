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

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
)

from eagleclasslists.app.grade_list_model import GradeListModel
from eagleclasslists.app.widgets import (
    ClassroomsView,
    StudentsView,
    TeachersView,
)
from eagleclasslists.classlist import ExcelImportError, GradeList


class MainWindow(QMainWindow):
    def __init__(self, model: GradeListModel):
        super().__init__()
        self.model = model
        self.setWindowTitle("Eagle Class Lists")

        self._create_menu_bar()
        self._create_sidebar_and_views()

        self.show()

    def _create_menu_bar(self) -> None:
        """Create the application menu bar with File menu."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_grade_list)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._load_grade_list)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_grade_list)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _create_sidebar_and_views(self) -> None:
        """Create the sidebar navigation and stacked views."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        sidebar = QListWidget()
        sidebar.addItems(["Teachers", "Students", "Classrooms"])

        stack = QStackedWidget()
        stack.addWidget(TeachersView(self.model))
        stack.addWidget(StudentsView(self.model))
        stack.addWidget(ClassroomsView(self.model))

        sidebar.currentRowChanged.connect(stack.setCurrentIndex)

        splitter.addWidget(sidebar)
        splitter.addWidget(stack)
        splitter.setSizes([150, 500])

        self.setCentralWidget(splitter)

    def _new_grade_list(self) -> None:
        """Create a new empty grade list."""
        self.model.set_grade_list(GradeList(teachers=[], students=[]))

    def _load_grade_list(self) -> None:
        """Load a grade list from an Excel file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Grade List",
            "",
            "Excel Files (*.xlsx *.xls)",
        )
        if not filepath:
            return

        try:
            grade_list = GradeList.from_excel(Path(filepath))
            self.model.set_grade_list(grade_list)
        except ExcelImportError as e:
            QMessageBox.critical(self, "Open Failed", f"{e.message}\n\n{e.details or ''}")
        except Exception as e:
            QMessageBox.critical(self, "Open Failed", f"Unexpected error: {e}")

    def _save_grade_list(self) -> None:
        """Save the current grade list to an Excel file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Grade List",
            "",
            "Excel Files (*.xlsx)",
        )
        if not filepath:
            return

        try:
            self.model.grade_list.save_to_excel(Path(filepath))
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Failed to save: {e}")
