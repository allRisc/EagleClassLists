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

"""View for managing classroom assignments and optimization."""

from __future__ import annotations

from PySide6.QtCore import QMutex, QObject, Qt, QThread, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from eagleclasslists.app.grade_list_model import GradeListModel
from eagleclasslists.classlist import GradeList, Student, Teacher
from eagleclasslists.fitness import FitnessWeights, calculate_fitness
from eagleclasslists.greedy_assignment import greedy_assign_students
from eagleclasslists.simulated_annealing import AnnealingConfig, optimize_grade_list

# ---------------------------------------------------------------------------
# OptimizationWorker (background thread)
# ---------------------------------------------------------------------------


class _OptimizationSignals(QObject):
    """Signals emitted by the optimization worker."""

    progress = Signal(int, float, float)
    finished = Signal(object)
    error = Signal(str)


class OptimizationWorker(QThread):
    """Run simulated annealing optimization in a background thread."""

    def __init__(
        self,
        grade_list: GradeList,
        weights: FitnessWeights,
        config: AnnealingConfig,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.grade_list = grade_list
        self.weights = weights
        self.config = config
        self.signals = _OptimizationSignals()
        self._mutex = QMutex()

    def run(self) -> None:
        try:
            result = optimize_grade_list(
                self.grade_list,
                weights=self.weights,
                config=self.config,
                progress_callback=self._on_progress,
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _on_progress(self, iteration: int, temperature: float, fitness: float) -> None:
        self.signals.progress.emit(iteration, temperature, fitness)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _get_student_display_name(student: Student) -> str:
    """Generate display name for a student with cluster/resource/speech flags."""
    attrs: list[str] = []
    if student.cluster:
        attrs.append(str(student.cluster))
    if student.resource:
        attrs.append("R")
    if student.speech:
        attrs.append("S")
    if attrs:
        return f"{student.first_name} {student.last_name} ({', '.join(attrs)})"
    return f"{student.first_name} {student.last_name}"


def _get_teacher_color(teacher: Teacher) -> tuple[str, str]:
    """Return (background_color, text_color) hex tuples based on teacher clusters."""
    if not teacher.clusters:
        return ("#6b7280", "#ffffff")
    cluster_colors: dict[str, tuple[str, str]] = {
        "AC": ("#1e40af", "#ffffff"),
        "GEM": ("#b45309", "#ffffff"),
        "EL": ("#047857", "#ffffff"),
    }
    return cluster_colors.get(str(teacher.clusters[0]), ("#6b7280", "#ffffff"))


def _build_teacher_students_map(grade_list: GradeList) -> dict[str, list[Student]]:
    """Build a map of teacher names to their assigned students."""
    teacher_students: dict[str, list[Student]] = {}
    for cls in grade_list.classes:
        teacher_students[cls.teacher.name] = cls.students.copy()
    return teacher_students


def _get_unassigned_students(
    grade_list: GradeList,
    teacher_students: dict[str, list[Student]],
) -> list[Student]:
    """Get students not assigned to any teacher."""
    assigned: set[tuple[str, str]] = set()
    for students in teacher_students.values():
        for s in students:
            assigned.add((s.first_name, s.last_name))
    return [s for s in grade_list.students if (s.first_name, s.last_name) not in assigned]


def _calculate_classroom_stats(students: list[Student]) -> dict[str, dict[str, int]]:
    """Calculate statistics for a classroom."""
    stats: dict[str, dict[str, int]] = {
        "gender": {"Male": 0, "Female": 0},
        "math": {"High": 0, "Medium": 0, "Low": 0},
        "ela": {"High": 0, "Medium": 0, "Low": 0},
        "behavior": {"High": 0, "Medium": 0, "Low": 0},
        "services": {"Resource": 0, "Speech": 0, "Both": 0, "Neither": 0},
        "clusters": {},
    }
    for student in students:
        if student.gender.value == "Male":
            stats["gender"]["Male"] += 1
        else:
            stats["gender"]["Female"] += 1
        stats["math"][student.math.value] += 1
        stats["ela"][student.ela.value] += 1
        stats["behavior"][student.behavior.value] += 1
        if student.resource and student.speech:
            stats["services"]["Both"] += 1
        elif student.resource:
            stats["services"]["Resource"] += 1
        elif student.speech:
            stats["services"]["Speech"] += 1
        else:
            stats["services"]["Neither"] += 1
        if student.cluster:
            cluster_str = str(student.cluster)
            if cluster_str not in stats["clusters"]:
                stats["clusters"][cluster_str] = 0
            stats["clusters"][cluster_str] += 1
    return stats


# ---------------------------------------------------------------------------
# StackedBarWidget
# ---------------------------------------------------------------------------


class StackedBarWidget(QWidget):
    """Custom widget that draws a percentage-stacked bar chart."""

    def __init__(
        self,
        segments: list[tuple[str, int, str]],
        total: int,
        height: int = 28,
    ) -> None:
        super().__init__()
        self.segments = segments
        self.total = total
        self._height = height
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_segments(self, segments: list[tuple[str, int, str]], total: int) -> None:
        """Update the segments and redraw."""
        self.segments = segments
        self.total = total
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.total == 0:
            painter.fillRect(self.rect(), QColor("#e5e7eb"))
            painter.setPen(QColor("#9ca3af"))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No students")
            return

        rect = self.rect()
        x = rect.x()
        bar_width = rect.width()
        bar_height = rect.height()

        for _idx, (label, count, color_hex) in enumerate(self.segments):
            if count == 0:
                continue
            pct = count / self.total
            seg_width = int(bar_width * pct)
            if seg_width < 1:
                continue
            painter.fillRect(x, 0, seg_width, bar_height, QColor(color_hex))
            if seg_width > 30:
                painter.setPen(QColor("#1f2937"))
                font = painter.font()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)
                pct_display = round(pct * 100)
                text = f"{label} {pct_display}%"
                fm = QFontMetrics(font)
                text_rect = fm.boundingRect(text)
                text_x = x + (seg_width - text_rect.width()) // 2
                text_y = (bar_height + text_rect.height()) // 2 - 1
                painter.drawText(text_x, text_y, text)
            x += seg_width


# ---------------------------------------------------------------------------
# ClassroomStatisticsWidget
# ---------------------------------------------------------------------------


class ClassroomStatisticsWidget(QWidget):
    """Displays side-by-side stacked bar statistics for all classrooms."""

    _CATEGORY_COLORS: dict[str, dict[str, str]] = {
        "gender": {"Male": "#bfdbfe", "Female": "#f9a8d4"},
        "math": {"High": "#bbf7d0", "Medium": "#fde68a", "Low": "#fecaca"},
        "ela": {"High": "#bbf7d0", "Medium": "#fde68a", "Low": "#fecaca"},
        "behavior": {"High": "#bbf7d0", "Medium": "#fde68a", "Low": "#fecaca"},
        "services": {
            "Neither": "#e5e7eb",
            "Resource": "#ddd6fe",
            "Speech": "#a5f3fc",
            "Both": "#c7d2fe",
        },
    }

    _CLUSTER_COLORS: dict[str, str] = {
        "AC": "#fed7aa",
        "GEM": "#e9d5ff",
        "EL": "#99f6e4",
    }

    def __init__(self, grade_list: GradeList) -> None:
        super().__init__()
        self.grade_list = grade_list
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._populate()

    def refresh(self, grade_list: GradeList) -> None:
        """Rebuild the statistics display for a new grade list."""
        self.grade_list = grade_list
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_sub_layout(item.layout())
        self._populate()

    def _clear_sub_layout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        """Recursively clear a sub-layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_sub_layout(item.layout())

    def _populate(self) -> None:
        classes = self.grade_list.classes
        if not classes:
            label = QLabel("No classrooms with assigned students yet.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 13px; color: #888; padding: 12px;")
            self._layout.addWidget(label)
            return

        # Collect all cluster types
        all_clusters: set[str] = set()
        for cls in classes:
            stats = _calculate_classroom_stats(cls.students)
            all_clusters.update(stats["clusters"].keys())

        # Header row
        header_layout = QHBoxLayout()
        for cls in classes:
            total = len(cls.students)
            name_label = QLabel(f"**{cls.teacher.name}** ({total} students)")
            name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(name_label)
        self._layout.addLayout(header_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #d1d5db;")
        self._layout.addWidget(divider)

        # Build rows
        colors = self._CATEGORY_COLORS
        rows = [
            ("Gender", "gender", ["Male", "Female"], colors["gender"]),
            ("Math", "math", ["High", "Medium", "Low"], colors["math"]),
            ("ELA", "ela", ["High", "Medium", "Low"], colors["ela"]),
            ("Behavior", "behavior", ["High", "Medium", "Low"], colors["behavior"]),
            (
                "Services",
                "services",
                ["Neither", "Resource", "Speech", "Both"],
                colors["services"],
            ),
        ]

        for row_label, stat_key, categories, color_map in rows:
            row_layout = QHBoxLayout()
            cat_label = QLabel(f"{row_label}:")
            cat_label.setStyleSheet("font-weight: bold; font-size: 11px;")
            cat_label.setFixedWidth(80)
            row_layout.addWidget(cat_label)

            for cls in classes:
                stats = _calculate_classroom_stats(cls.students)
                total = len(cls.students)
                segs = [
                    (cat, stats[stat_key][cat], color_map[cat])
                    for cat in categories
                ]
                bar = StackedBarWidget(segs, total)
                row_layout.addWidget(bar)
            self._layout.addLayout(row_layout)

        # Clusters row (if any)
        if all_clusters:
            row_layout = QHBoxLayout()
            cat_label = QLabel("Clusters:")
            cat_label.setStyleSheet("font-weight: bold; font-size: 11px;")
            cat_label.setFixedWidth(80)
            row_layout.addWidget(cat_label)

            for cls in classes:
                stats = _calculate_classroom_stats(cls.students)
                total = len(cls.students)
                segs = [
                    (
                        cluster,
                        stats["clusters"].get(cluster, 0),
                        self._CLUSTER_COLORS.get(cluster, "#d1d5db"),
                    )
                    for cluster in sorted(all_clusters)
                ]
                bar = StackedBarWidget(segs, total)
                row_layout.addWidget(bar)
            self._layout.addLayout(row_layout)


# ---------------------------------------------------------------------------
# UnassignedStudentRow
# ---------------------------------------------------------------------------


class UnassignedStudentRow(QFrame):
    """Row widget for an unassigned student with checkbox and quick-assign."""

    def __init__(
        self,
        student: Student,
        model: GradeListModel,
        target_teacher_combo: QComboBox,
    ) -> None:
        super().__init__()
        self.student = student
        self.model = model
        self.target_combo = target_teacher_combo
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self.checkbox = QCheckBox(_get_student_display_name(self.student))
        self.checkbox.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.checkbox, stretch=1)

        quick_add_btn = QPushButton("+")
        quick_add_btn.setFixedWidth(28)
        quick_add_btn.setToolTip(f"Quick assign {self.student.first_name} {self.student.last_name}")
        quick_add_btn.clicked.connect(self._on_quick_add)
        layout.addWidget(quick_add_btn)

    def _on_quick_add(self) -> None:
        teacher = self.target_combo.currentText()
        if teacher:
            self.model.add_student_to_classroom(
                teacher, self.student.first_name, self.student.last_name
            )


# ---------------------------------------------------------------------------
# UnassignedStudentsPanel
# ---------------------------------------------------------------------------


class UnassignedStudentsPanel(QWidget):
    """Panel showing unassigned students with bulk assignment controls."""

    def __init__(self, model: GradeListModel) -> None:
        super().__init__()
        self.model = model
        self.target_combo: QComboBox
        self._rows: list[UnassignedStudentRow] = []
        self._setup_ui()
        model.changed.connect(self._refresh)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.count_label = QLabel("Unassigned Students: 0")
        self.count_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.count_label)

        controls_layout = QHBoxLayout()
        self.target_combo = QComboBox()
        self._populate_teacher_combo()
        controls_layout.addWidget(QLabel("Assign to:"))
        controls_layout.addWidget(self.target_combo, stretch=1)

        self.assign_btn = QPushButton("Assign Selected")
        self.assign_btn.clicked.connect(self._on_assign_selected)
        controls_layout.addWidget(self.assign_btn)
        layout.addLayout(controls_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #d1d5db;")
        layout.addWidget(divider)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.scroll_content)
        layout.addWidget(scroll_area, stretch=1)

    def _populate_teacher_combo(self) -> None:
        self.target_combo.clear()
        for teacher in self.model.grade_list.teachers:
            self.target_combo.addItem(teacher.name)

    def _on_assign_selected(self) -> None:
        teacher = self.target_combo.currentText()
        if not teacher:
            QMessageBox.warning(self, "Warning", "No teacher selected.")
            return
        count = 0
        for row in self._rows:
            if row.checkbox.isChecked():
                self.model.add_student_to_classroom(
                    teacher, row.student.first_name, row.student.last_name
                )
                count += 1
        if count == 0:
            QMessageBox.information(self, "Info", "No students selected.")

    def _refresh(self) -> None:
        self._populate_teacher_combo()
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()

        teacher_students = _build_teacher_students_map(self.model.grade_list)
        unassigned = _get_unassigned_students(self.model.grade_list, teacher_students)
        self.count_label.setText(f"Unassigned Students: {len(unassigned)}")

        if not unassigned:
            label = QLabel("All students assigned!")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 13px; color: #047857; padding: 16px;")
            self.scroll_layout.addWidget(label)
            # type: ignore[arg-type]
            self._rows.append(type("LabelRow", (), {"deleteLater": label.deleteLater})())
            return

        for student in unassigned:
            row = UnassignedStudentRow(student, self.model, self.target_combo)
            self.scroll_layout.addWidget(row)
            self._rows.append(row)


# ---------------------------------------------------------------------------
# TeacherColumn
# ---------------------------------------------------------------------------


class TeacherStudentRow(QFrame):
    """Row for a student inside a teacher column with checkbox."""

    def __init__(self, student: Student, teacher_name: str, model: GradeListModel) -> None:
        super().__init__()
        self.student = student
        self.teacher_name = teacher_name
        self.model = model
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        self.checkbox = QCheckBox(_get_student_display_name(self.student))
        self.checkbox.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.checkbox, stretch=1)


class TeacherColumn(QFrame):
    """Column widget for a single teacher showing students and move controls."""

    def __init__(self, teacher: Teacher, model: GradeListModel) -> None:
        super().__init__()
        self.teacher = teacher
        self.model = model
        self._rows: list[TeacherStudentRow] = []
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Teacher header with color
        bg_color, text_color = _get_teacher_color(self.teacher)
        header = QLabel(self.teacher.name)
        header.setStyleSheet(
            f"background-color: {bg_color}; color: {text_color}; "
            f"font-weight: bold; font-size: 13px; padding: 4px 8px; "
            f"border-radius: 3px;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Cluster info
        if self.teacher.clusters:
            cluster_text = ", ".join(str(c) for c in self.teacher.clusters)
            cluster_label = QLabel(f"Clusters: {cluster_text}")
            cluster_label.setStyleSheet("font-size: 10px; color: #888;")
            cluster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(cluster_label)

        # Student count
        classroom = next(
            (c for c in self.model.grade_list.classes if c.teacher.name == self.teacher.name),
            None,
        )
        count = len(classroom.students) if classroom else 0
        self.count_label = QLabel(f"{count} student{'s' if count != 1 else ''}")
        self.count_label.setStyleSheet("font-size: 11px; color: #555;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        # Move combo
        move_layout = QHBoxLayout()
        self.move_combo = QComboBox()
        for t in self.model.grade_list.teachers:
            if t.name != self.teacher.name:
                self.move_combo.addItem(t.name)
        move_layout.addWidget(QLabel("Move to:"))
        move_layout.addWidget(self.move_combo, stretch=1)
        self.move_btn = QPushButton("Move Selected")
        self.move_btn.clicked.connect(self._on_move_selected)
        move_layout.addWidget(self.move_btn)
        layout.addLayout(move_layout)

        # Remove button
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._on_remove_selected)
        layout.addWidget(self.remove_btn)

        # Student rows
        if classroom:
            for student in classroom.students:
                row = TeacherStudentRow(student, self.teacher.name, self.model)
                layout.addWidget(row)
                self._rows.append(row)

    def _on_move_selected(self) -> None:
        target = self.move_combo.currentText()
        if not target:
            return
        for row in self._rows:
            if row.checkbox.isChecked():
                self.model.add_student_to_classroom(
                    target, row.student.first_name, row.student.last_name
                )
                self.model.remove_student_from_classroom(
                    self.teacher.name, row.student.first_name, row.student.last_name
                )

    def _on_remove_selected(self) -> None:
        for row in self._rows:
            if row.checkbox.isChecked():
                self.model.remove_student_from_classroom(
                    self.teacher.name, row.student.first_name, row.student.last_name
                )


# ---------------------------------------------------------------------------
# OptimizationSection
# ---------------------------------------------------------------------------


class OptimizationSection(QGroupBox):
    """Widget for configuring and running simulated annealing optimization."""

    def __init__(self, model: GradeListModel, parent: QWidget | None = None) -> None:
        super().__init__("Optimization", parent)
        self.model = model
        self._pre_fitness: float = 0.0
        self._post_fitness: float = 0.0
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Current fitness display
        fitness_layout = QHBoxLayout()
        self.fitness_label = QLabel("Current Fitness Score: 0.0000")
        self.fitness_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        fitness_layout.addWidget(self.fitness_label)
        layout.addLayout(fitness_layout)

        # Collapsible advanced settings group
        self._settings_collapsed = True
        self.settings_toggle = QToolButton()
        self.settings_toggle.setText("Advanced Optimization Settings")
        self.settings_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.settings_toggle.setCheckable(True)
        self.settings_toggle.setChecked(False)
        self.settings_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.settings_toggle.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; font-size: 13px; "
            "text-align: left; padding: 4px 0; }"
        )
        self.settings_toggle.clicked.connect(self._toggle_settings)
        layout.addWidget(self.settings_toggle)

        self.settings_group = QGroupBox()
        self.settings_layout = QVBoxLayout(self.settings_group)
        self.settings_group.hide()

        # Optimization settings
        opt_group = QGroupBox("Optimization Settings")
        opt_layout = QFormLayout(opt_group)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(10, 200)
        self.temp_slider.setValue(100)
        self.temp_label = QLabel("100.0")
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v:.1f}")
        )
        temp_row = QHBoxLayout()
        temp_row.addWidget(self.temp_slider)
        temp_row.addWidget(self.temp_label)
        opt_layout.addRow("Initial Temperature:", temp_row)

        self.cooling_slider = QSlider(Qt.Orientation.Horizontal)
        self.cooling_slider.setRange(950, 999)
        self.cooling_slider.setValue(995)
        self.cooling_label = QLabel("0.995")
        self.cooling_slider.valueChanged.connect(
            lambda v: self.cooling_label.setText(f"{v / 1000:.3f}")
        )
        cooling_row = QHBoxLayout()
        cooling_row.addWidget(self.cooling_slider)
        cooling_row.addWidget(self.cooling_label)
        opt_layout.addRow("Cooling Rate:", cooling_row)

        self.iter_slider = QSlider(Qt.Orientation.Horizontal)
        self.iter_slider.setRange(1, 50)
        self.iter_slider.setValue(10)
        self.iter_label = QLabel("10000")
        self.iter_slider.valueChanged.connect(
            lambda v: self.iter_label.setText(f"{v * 1000}")
        )
        iter_row = QHBoxLayout()
        iter_row.addWidget(self.iter_slider)
        iter_row.addWidget(self.iter_label)
        opt_layout.addRow("Max Iterations:", iter_row)

        self.settings_layout.addWidget(opt_group)

        # Fitness weights
        weights_group = QGroupBox("Fitness Weights")
        weights_layout = QFormLayout(weights_group)

        self.weight_sliders: dict[str, QDoubleSpinBox] = {}
        for name, default in [
            ("Gender", 1.0),
            ("Math", 0.5),
            ("ELA", 0.5),
            ("Behavior", 1.0),
            ("Class Size", 1.0),
            ("Resource", 0.5),
            ("Speech", 0.5),
        ]:
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 5.0)
            spin.setSingleStep(0.5)
            spin.setValue(default)
            self.weight_sliders[name] = spin
            weights_layout.addRow(f"{name}:", spin)

        self.settings_layout.addWidget(weights_group)
        layout.addWidget(self.settings_group)

        # Progress bar
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet("font-size: 11px; color: #555;")
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar, stretch=1)
        progress_layout.addWidget(self.progress_label)
        layout.addLayout(progress_layout)

        # Run button
        self.run_btn = QPushButton("Run Simulated Annealing Optimization")
        self.run_btn.clicked.connect(self._on_run_optimization)
        layout.addWidget(self.run_btn)

        # Results group
        self.results_group = QGroupBox("Optimization Results")
        self.results_group.hide()
        results_layout = QVBoxLayout(self.results_group)
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        results_layout.addWidget(self.results_label)

        self.clear_results_btn = QPushButton("Clear Results")
        self.clear_results_btn.clicked.connect(self._on_clear_results)
        results_layout.addWidget(self.clear_results_btn)
        layout.addWidget(self.results_group)

    def _get_weights(self) -> FitnessWeights:
        return FitnessWeights(
            gender=self.weight_sliders["Gender"].value(),
            math=self.weight_sliders["Math"].value(),
            ela=self.weight_sliders["ELA"].value(),
            behavior=self.weight_sliders["Behavior"].value(),
            class_size=self.weight_sliders["Class Size"].value(),
            resource=self.weight_sliders["Resource"].value(),
            speech=self.weight_sliders["Speech"].value(),
        )

    def _get_config(self) -> AnnealingConfig:
        return AnnealingConfig(
            initial_temperature=float(self.temp_slider.value()),
            cooling_rate=self.cooling_slider.value() / 1000,
            max_iterations=self.iter_slider.value() * 1000,
        )

    def _on_run_optimization(self) -> None:
        grade_list = self.model.grade_list
        unassigned = _get_unassigned_students(
            grade_list, _build_teacher_students_map(grade_list)
        )
        if len(grade_list.teachers) < 2:
            QMessageBox.warning(self, "Warning", "Need at least 2 teachers to optimize.")
            return
        if not grade_list.students:
            QMessageBox.warning(self, "Warning", "No students to optimize.")
            return
        if unassigned:
            QMessageBox.warning(
                self,
                "Warning",
                f"Please assign all {len(unassigned)} unassigned students before optimizing.",
            )
            return

        self._pre_fitness = calculate_fitness(grade_list, self._get_weights())
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Optimizing...")
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting optimization...")

        self.worker = OptimizationWorker(grade_list, self._get_weights(), self._get_config())
        self.worker.signals.progress.connect(self._on_progress)
        self.worker.signals.finished.connect(self._on_finished)
        self.worker.signals.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, iteration: int, temperature: float, fitness: float) -> None:
        config = self._get_config()
        pct = min(100, int(100 * iteration / config.max_iterations))
        self.progress_bar.setValue(pct)
        self.progress_label.setText(
            f"Iteration {iteration:,} | Temp: {temperature:.4f} | Fitness: {fitness:.4f}"
        )

    def _on_finished(self, optimized: GradeList) -> None:
        self._post_fitness = calculate_fitness(optimized, self._get_weights())
        self.model.set_grade_list(optimized)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Simulated Annealing Optimization")
        self.progress_bar.setValue(100)
        self.progress_label.setText("Optimization complete!")
        self._show_results()

    def _on_error(self, error: str) -> None:
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Simulated Annealing Optimization")
        self.progress_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Optimization Error", f"Optimization failed:\n{error}")

    def _show_results(self) -> None:
        improvement = self._post_fitness - self._pre_fitness
        improvement_pct = (
            (improvement / self._pre_fitness * 100) if self._pre_fitness > 0 else 0
        )
        text = (
            f"Before: {self._pre_fitness:.4f}\n"
            f"After:  {self._post_fitness:.4f}\n"
            f"Improvement: {improvement:+.4f} ({improvement_pct:+.1f}%)"
        )
        self.results_label.setText(text)
        self.results_group.show()

    def _on_clear_results(self) -> None:
        self.results_group.hide()

    def _toggle_settings(self) -> None:
        self._settings_collapsed = not self._settings_collapsed
        if self._settings_collapsed:
            self.settings_group.hide()
            self.settings_toggle.setArrowType(Qt.ArrowType.RightArrow)
        else:
            self.settings_group.show()
            self.settings_toggle.setArrowType(Qt.ArrowType.DownArrow)

    def refresh(self) -> None:
        fitness = calculate_fitness(self.model.grade_list, self._get_weights())
        self.fitness_label.setText(f"Current Fitness Score: {fitness:.4f}")


# ---------------------------------------------------------------------------
# ClassroomsView (main container)
# ---------------------------------------------------------------------------


class ClassroomsView(QWidget):
    """Main view for managing classroom assignments."""

    def __init__(self, model: GradeListModel) -> None:
        super().__init__()
        self.model = model
        self.stats_widget: ClassroomStatisticsWidget | None = None
        self._setup_ui()
        model.changed.connect(self._refresh)

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.unassign_btn = QPushButton("Unassign All")
        self.unassign_btn.clicked.connect(self._on_unassign_all)
        toolbar_layout.addWidget(self.unassign_btn)

        self.auto_balance_btn = QPushButton("Auto-Balance Classes")
        self.auto_balance_btn.clicked.connect(self._on_auto_balance)
        toolbar_layout.addWidget(self.auto_balance_btn)

        self.progress_label = QLabel("Progress: 0/0 assigned")
        self.progress_label.setStyleSheet("font-size: 12px; color: #555;")
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.progress_label)

        main_layout.addLayout(toolbar_layout)

        # Splitter: unassigned panel | teacher columns
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.unassigned_panel = UnassignedStudentsPanel(self.model)
        splitter.addWidget(self.unassigned_panel)

        # Teacher columns container
        teacher_container = QWidget()
        self.teacher_layout = QVBoxLayout(teacher_container)
        self.teacher_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        teacher_scroll = QScrollArea()
        teacher_scroll.setWidgetResizable(True)
        teacher_scroll.setWidget(teacher_container)
        splitter.addWidget(teacher_scroll)

        splitter.setSizes([250, 500])
        main_layout.addWidget(splitter, stretch=1)

        # Statistics section
        stats_group = QGroupBox("Classroom Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_widget = ClassroomStatisticsWidget(self.model.grade_list)
        stats_layout.addWidget(self.stats_widget)
        main_layout.addWidget(stats_group)

        # Optimization section
        self.optimization_section = OptimizationSection(self.model)
        main_layout.addWidget(self.optimization_section)

    def _on_unassign_all(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Unassign All",
            "Remove all students from all classrooms?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.model.unassign_all_students()

    def _on_auto_balance(self) -> None:
        grade_list = self.model.grade_list
        teacher_students = _build_teacher_students_map(grade_list)
        unassigned = _get_unassigned_students(grade_list, teacher_students)

        if not unassigned:
            QMessageBox.information(self, "Info", "No unassigned students to auto-balance.")
            return
        if not grade_list.teachers:
            QMessageBox.warning(self, "Warning", "No teachers available.")
            return

        weights = FitnessWeights(
            gender=1.0,
            math=0.5,
            ela=0.5,
            behavior=1.0,
            resource=0.5,
            speech=0.5,
            class_size=1.0,
        )

        try:
            assigned = greedy_assign_students(grade_list, students=unassigned, weights=weights)
            self.model.set_grade_list(assigned)
            QMessageBox.information(
                self,
                "Auto-Balance Complete",
                f"Assigned {len(unassigned)} students.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Auto-Balance Failed", f"Error: {e}")

    def _refresh(self) -> None:
        grade_list = self.model.grade_list
        teacher_students = _build_teacher_students_map(grade_list)
        unassigned = _get_unassigned_students(grade_list, teacher_students)
        total = len(grade_list.students)
        assigned_count = total - len(unassigned)
        self.progress_label.setText(f"Progress: {assigned_count}/{total} assigned")

        # Rebuild teacher columns
        self._rebuild_teacher_columns()

        # Refresh statistics
        if self.stats_widget is not None:
            self.stats_widget.refresh(grade_list)

        # Refresh optimization fitness
        if self.optimization_section is not None:
            self.optimization_section.refresh()

    def _rebuild_teacher_columns(self) -> None:
        """Clear and rebuild all teacher columns."""
        self._clear_layout(self.teacher_layout)

        grade_list = self.model.grade_list
        if not grade_list.teachers:
            if self.model.classrooms_loaded:
                msg = "No classrooms in the loaded file."
            else:
                msg = "No classrooms loaded. Use File > Open Classrooms to load."
            label = QLabel(msg)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #888; padding: 20px;")
            self.teacher_layout.addWidget(label)
        else:
            num_teachers = len(grade_list.teachers)
            cols = min(num_teachers, 4)
            rows = (num_teachers + cols - 1) // cols

            grid = QVBoxLayout()
            for row_idx in range(rows):
                row_layout = QHBoxLayout()
                for col_idx in range(cols):
                    idx = row_idx * cols + col_idx
                    if idx < num_teachers:
                        teacher = grade_list.teachers[idx]
                        col = TeacherColumn(teacher, self.model)
                        row_layout.addWidget(col, stretch=1)
                    else:
                        row_layout.addStretch()
                grid.addLayout(row_layout)
            self.teacher_layout.addLayout(grid)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        """Remove all items from a layout, including nested layouts."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())
