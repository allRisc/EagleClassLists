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

"""Streamlit app for managing class lists.

This module provides a web interface for adding, editing, and assigning
students to teachers, with Excel file import/export functionality.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from typing import NoReturn

import streamlit as st

from eagleclasslists.classlist import GradeList
from eagleclasslists.streamlit_app.pages import (
    render_assignments_page,
    render_save_load_page,
    render_students_page,
    render_teachers_page,
)


def init_session_state() -> None:
    """Initialize session state variables."""
    if "grade_list" not in st.session_state:
        st.session_state.grade_list = GradeList(classes=[], teachers=[], students=[])
    if "current_file" not in st.session_state:
        st.session_state.current_file = None
    if "teacher_to_remove" not in st.session_state:
        st.session_state.teacher_to_remove = None
    if "student_to_remove" not in st.session_state:
        st.session_state.student_to_remove = None


def st_app() -> None:
    """Main Streamlit application entry point.

    This function sets up the Streamlit app with sidebar navigation
    and renders the appropriate page based on user selection.
    """
    st.set_page_config(
        page_title="Eagle Class Lists",
        page_icon="📚",
        layout="wide",
    )

    # Hide default Streamlit page navigation from sidebar
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_session_state()

    st.title("📚 Eagle Class Lists")
    st.write("Manage students, teachers, and classroom assignments")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        options=["Teachers", "Students", "Assignments", "Download / Load"],
    )

    # Display current file info
    if st.session_state.current_file:
        st.sidebar.info(f"Current file: {st.session_state.current_file}")

    # Display stats
    grade_list: GradeList = st.session_state.grade_list
    st.sidebar.divider()
    st.sidebar.write("**Current Data**")
    st.sidebar.write(f"Teachers: {len(grade_list.teachers)}")
    st.sidebar.write(f"Students: {len(grade_list.students)}")
    st.sidebar.write(f"Classrooms: {len(grade_list.classes)}")

    # Shutdown button
    st.sidebar.divider()
    if st.sidebar.button("🛑 Shutdown Server", type="primary"):
        st.sidebar.warning("Shutting down server...")
        os.kill(os.getpid(), signal.SIGTERM)

    # Render selected page
    if page == "Teachers":
        render_teachers_page()
    elif page == "Students":
        render_students_page()
    elif page == "Assignments":
        render_assignments_page()
    elif page == "Download / Load":
        render_save_load_page()


def run_app() -> NoReturn:
    ret = subprocess.call(["streamlit", "run", __file__])
    sys.exit(ret)


if __name__ == "__main__":
    st_app()
