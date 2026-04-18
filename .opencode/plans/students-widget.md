# Students Widget Implementation Plan

## Overview
Build a functional students widget for the desktop app (`eagleclasslists.app`) with a scrollable list showing student names, summary strings, and action buttons. Refactor the summary string logic from the Streamlit app into the Student class for reuse.

## Changes

### 1. Add `summary_string()` method to Student class (`src/eagleclasslists/classlist.py`)

Add a new method to the `Student` class that generates a display summary string:

```python
def summary_string(self, all_students: list[Student] | None = None) -> str:
    """Generate a summary string for display in UI components."""
```

- Generates emoji-rich summary matching Streamlit format
- Format: `"Gender • 🔢 Math • 📚 ELA • 😊 Behavior • [🎯 Cluster] • [🔧 Resource] • [🗣️ Speech] • [👨‍🏫 Teacher] • [🚫 Exclusions]"`
- Includes orphaned exclusion detection when `all_students` is provided
- Add private helper `_get_valid_exclusions()` for reuse

### 2. Add `remove_student()` method to GradeListModel (`src/eagleclasslists/app/grade_list_model.py`)

Add method to remove a student from the grade list:

```python
def remove_student(self, first_name: str, last_name: str) -> None:
    """Remove a student and emit changed signal."""
```

- Removes student from `grade_list.students`
- Removes student from all classrooms in `grade_list.classes`
- Emits `changed` signal after removal

### 3. Implement StudentsView widget (`src/eagleclasslists/app/widgets/students_view.py`)

Replace the stub with a fully functional widget:

**Layout:**
- QScrollArea containing a QVBoxLayout of student rows
- Each row is a QFrame with horizontal layout:
  - Left side: Student name (bold) + summary string (below name)
  - Right side: Edit button + Remove button

**StudentRow widget:**
- Custom QWidget for each student
- Shows name prominently with summary below
- Edit button: shows "Not implemented yet" QMessageBox
- Remove button: shows confirmation QMessageBox, calls `model.remove_student()`

**Reactive updates:**
- Connect to `model.changed` signal
- Rebuild student list on refresh

### 4. Update widgets `__init__.py` exports (if needed)

Ensure the new StudentRow class is exported if it's a standalone component.

## Design Decisions

- **Emojis included**: Match Streamlit format with emoji icons for visual consistency
- **Inline layout**: Name + summary shown together in each row, not expandable
- **Confirmation dialog**: QMessageBox confirmation before removing students
- **Simple QWidget list**: Use QScrollArea + QVBoxLayout instead of QListView for flexibility

## Testing

- Add unit tests for `Student.summary_string()` method
- Test orphaned exclusion detection
- Test GradeListModel.remove_student() removes from both students list and classrooms
- Verify existing tests still pass
