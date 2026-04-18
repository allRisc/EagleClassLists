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

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from eagleclasslists.app.grade_list_model import GradeListModel


class TeachersView(QWidget):
    """View for managing teachers."""

    def __init__(self, model: GradeListModel) -> None:
        super().__init__()
        self.model = model
        self._setup_ui()
        model.changed.connect(self._refresh)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.label = QLabel("Teachers View - Manage teacher information")
        layout.addWidget(self.label)

    def _refresh(self) -> None:
        teachers = self.model.grade_list.teachers
        count = len(teachers)
        self.label.setText(f"Teachers View - {count} teacher(s)")
