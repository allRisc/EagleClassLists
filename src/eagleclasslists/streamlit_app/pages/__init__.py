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

"""Page modules for the Streamlit application."""

from eagleclasslists.streamlit_app.pages.assignments import render_assignments_page
from eagleclasslists.streamlit_app.pages.save_load import render_save_load_page
from eagleclasslists.streamlit_app.pages.students import render_students_page
from eagleclasslists.streamlit_app.pages.teachers import render_teachers_page

__all__ = [
    "render_assignments_page",
    "render_save_load_page",
    "render_students_page",
    "render_teachers_page",
]
