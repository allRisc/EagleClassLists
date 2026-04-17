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

"""Save/Load page for the Streamlit app."""

from __future__ import annotations

import io
from pathlib import Path

import streamlit as st

from eagleclasslists.classlist import ExcelImportError, GradeList


def render_save_load_page() -> None:
    """Render the download/load page for Excel file operations."""
    st.header("Download / Load")
    st.write("Download your grade list as an Excel file or load from an existing file.")

    grade_list: GradeList = st.session_state.grade_list

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Download Excel")

        if not grade_list.teachers and not grade_list.students:
            st.info("No data to download yet. Add teachers and students first.")
        else:
            st.write(f"Teachers: {len(grade_list.teachers)}")
            st.write(f"Students: {len(grade_list.students)}")
            st.write(f"Classrooms: {len(grade_list.classes)}")

            filename = st.text_input(
                "Filename",
                value="grade_list.xlsx",
                key="save_filename",
            )

            # Prepare the Excel data for download
            try:
                buffer = io.BytesIO()
                grade_list.save_to_excel(buffer)
                buffer.seek(0)
                excel_data = buffer.getvalue()

                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error preparing file: {e}")

    with col2:
        st.subheader("Upload Excel")

        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=["xlsx"],
            key="upload_excel",
        )

        if uploaded_file is not None:
            if st.button("Load File"):
                try:
                    # Save uploaded file temporarily
                    temp_path = Path("temp_upload.xlsx")
                    temp_path.write_bytes(uploaded_file.getvalue())

                    # Load the grade list
                    loaded = GradeList.from_excel(temp_path)
                    st.session_state.grade_list = loaded
                    st.session_state.current_file = uploaded_file.name

                    # Clean up temp file
                    temp_path.unlink()

                    st.success(
                        f"Loaded {len(loaded.teachers)} teachers, {len(loaded.students)} students"
                    )
                    st.rerun()
                except ExcelImportError as e:
                    # Clean up temp file if it exists
                    if temp_path.exists():
                        temp_path.unlink()

                    # Show user-friendly error message
                    st.error(f"**{e.message}**")
                    if e.details:
                        with st.expander("Show details and suggestions"):
                            st.markdown(f"```\n{e.details}\n```")
                except Exception as e:
                    # Clean up temp file if it exists
                    if temp_path.exists():
                        temp_path.unlink()

                    st.error(f"**Error loading file:** {e}")
                    with st.expander("Show technical details"):
                        st.exception(e)
