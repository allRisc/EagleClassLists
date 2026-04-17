# Exclusions Feature Implementation Plan

## Phase 1: Core Data Model + Excel Support
**Goal**: Add exclusions field to Student model with full Excel import/export

**Deliverables**:
- [ ] Add `exclusions: list[str]` field to `Student` class in `classlist.py`
  - Default: empty list
  - Pydantic field alias: "Exclusions"
  - Field validator: parse comma-separated string from Excel
  - Field serializer: convert list to comma-separated string for Excel
- [ ] Update `GradeList.from_excel()` error messages to mention Exclusions column
- [ ] Add tests for Excel import/export with exclusions
- [ ] Update CHANGELOG.md

**Testing**: Verify students can be loaded/saved with exclusions via Excel

---

## Phase 2: UI - Students Page Integration
**Goal**: Add exclusions editor to student form with searchable multi-select

**Deliverables**:
- [ ] Add `🚫 N` indicator to student summary display in `students.py`
  - Only show if exclusions list is non-empty
  - Show count (N = len(exclusions))
- [ ] Add exclusions field to "Add New Student" form
  - Searchable/autocomplete multi-select widget
  - Options: all existing students (excluding current student being created)
  - Selected values stored as "FirstName LastName" strings
- [ ] Add exclusions field to "Edit Student" form
  - Same widget as above
  - Pre-populated with current exclusions
  - Options update when student list changes
- [ ] Add tests for UI functionality

**Testing**: Manually verify exclusions can be added/removed via UI

---

## Phase 3: Greedy Algorithm Integration
**Goal**: Enforce exclusions as hard constraint in greedy assignment

**Deliverables**:
- [ ] Add `_has_exclusion_conflict()` helper in `greedy_assignment.py`
  - Check if classroom contains any student in given student's exclusions list
- [ ] Modify `_is_valid_assignment()` to reject classrooms with excluded students
- [ ] Modify `_sort_by_constraints()` to prioritize students with exclusions
  - Priority order: teacher request > exclusions > cluster > none
- [ ] Add error handling for impossible constraints
  - Raise clear error message listing which exclusions couldn't be satisfied
- [ ] Add tests for exclusion constraint enforcement

**Testing**: Verify greedy assignment respects exclusions; verify error on impossible constraints

---

## Phase 4: Simulated Annealing Integration
**Goal**: Enforce exclusions as hard constraint in simulated annealing

**Deliverables**:
- [ ] Add exclusion conflict check to `_is_swap_valid()` in `simulated_annealing.py`
  - Verify swap doesn't place either student with someone they exclude
- [ ] Add exclusion conflict check to `_generate_move_neighbor()`
  - Filter out moves that would place student with excluded peer
- [ ] Update neighbor generation to skip students with exclusion conflicts
- [ ] Add error/warning if optimization finds no valid solution
- [ ] Add tests for exclusion constraint in annealing

**Testing**: Verify simulated annealing respects exclusions across multiple runs

---

## Phase 5: Validation & Edge Cases
**Goal**: Handle edge cases and improve robustness

**Deliverables**:
- [ ] Add validation for exclusion name references
  - On student edit: warn if excluded student name doesn't exist
  - On Excel load: log warning for unknown exclusion names
- [ ] Handle name changes (graceful degradation)
  - Document that exclusions break if names change
  - Optionally: show "⚠️ Orphaned exclusions" warning in edit form
- [ ] Test with real-world scenarios
  - Multiple exclusions per student
  - Circular exclusion chains (A→B, B→C, C→A)
  - Impossible configurations
- [ ] Update documentation

**Testing**: Full integration test with sample data

---

## Implementation Notes

### Student Model Change
```python
exclusions: list[str] = pydantic.Field(alias="Exclusions", default_factory=list)
"""List of student names (FirstName LastName) this student cannot be with."""
```

### Excel Format
```
Teachers sheet: Unchanged
Students sheet: Add "Exclusions" column (comma-separated names)
Classrooms sheet: Unchanged
```

### UI Mockup
```
Existing Student Summary:
John Doe • Male • 🔢 High • 📚 High • 😊 High • 🚫 2  ← NEW

Edit Form:
[First Name    ] [Last Name    ]
[Gender ▼      ] [Behavior ▼   ]
[Math ▼        ] [ELA ▼        ]
[Cluster ▼     ] [Resource □   ]
[Speech ▼      ] [Teacher ▼    ]
Exclusions: [Alice Smith, Bob Jones] [x]  ← NEW (tag-style input)
           [Type to search...]
```

### Algorithm Pseudocode
```python
def _is_valid_assignment(classroom, student):
    # ... existing checks ...
    
    # NEW: Check exclusions
    classroom_student_names = {f"{s.first_name} {s.last_name}" for s in classroom.students}
    for excluded_name in student.exclusions:
        if excluded_name in classroom_student_names:
            return False
    
    return True
```

## Success Criteria
1. ✅ Can add exclusions via UI
2. ✅ Can import/export exclusions via Excel
3. ✅ 🚫 indicator appears with correct count
4. ✅ Greedy algorithm respects exclusions (hard constraint)
5. ✅ Simulated annealing respects exclusions (hard constraint)
6. ✅ Clear error on impossible configurations
7. ✅ All tests pass
