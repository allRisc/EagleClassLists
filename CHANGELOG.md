Changelog
====================================================================================================

All notable changes to ``EagleClassLists`` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Unreleased
----------------------------------------------------------------------

### Fixed
- **Stopped setting student teacher attribute during auto-balance** - The ``teacher``
  field on students is now only set when creating/editing students in the Streamlit
  UI or importing from Excel. Previously, the teacher attribute was being incorrectly
  assigned when students were assigned to classrooms via auto-balance or manual
  assignment operations.

### Added
- **Greedy assignment algorithm** - New ``greedy_assignment`` module for sequential student assignment
  - ``greedy_assign_students()`` function assigns students one-by-one to maximize fitness
  - Always assigns to the classroom that yields the highest overall fitness score
  - Respects hard constraints: cluster assignments and teacher requests
  - Students with constraints (teacher requests, then clusters) are assigned first
  - Supports custom ``FitnessWeights`` for controlling assignment priorities
  - Progress callback support for real-time assignment feedback
  - Returns a new ``GradeList`` with all students assigned (original unchanged)
- **Improved Excel error reporting** - Better error messages when loading poorly formatted Excel files
  - New ``ExcelImportError`` exception with user-friendly messages and detailed suggestions
  - Helpful error messages for missing sheets, invalid data, and validation failures
  - Streamlit UI now shows detailed guidance in expandable sections
  - Common issues are explained (missing columns, invalid enum values, etc.)

0.4.0
----------------------------------------------------------------------

### Changed
- **BREAKING**: Split ``Academics`` enum into separate ``Math`` and ``ELA`` enums
  - Replaced single ``academics`` field on ``Student`` with ``math`` and ``ela`` fields
  - Updated ``FitnessWeights`` to use separate ``math`` (0.5) and ``ela`` (0.5) weights
    instead of single ``academics`` (1.0) weight
  - Math and ELA contribute equally to fitness (combined weight of 1.0)
  - Updated fitness breakdown to show ``math`` and ``ela`` scores separately
  - Updated all test files, examples, and Streamlit UI to use new fields
  - Excel import/export now expects "Math" and "ELA" columns instead of "Academics"

### Added
- **Teacher request hard constraint** - Simulated annealing now treats
  teacher requests as hard constraints (like cluster assignments)
  - Students with a teacher request are never moved from their requested teacher
  - Neighbor generation automatically skips students with teacher requests
  - Fitness function returns 0.0 if any student with a request is not with
    their requested teacher (all-or-nothing constraint)
  - New ``teacher_request`` field in fitness breakdown

0.3.0
----------------------------------------------------------------------

### Added
- **Simulated Annealing optimization** for automatic grade list optimization
  - New ``fitness`` module for computing fairness scores (0-1 scale)
  - New ``simulated_annealing`` module for smart optimization
  - ``FitnessWeights`` dataclass with configurable weights for gender, academics,
    behavior, resource, speech, and class_size metrics
  - **Cluster as hard constraint**: cluster correctness is binary (1.0 if all
    correct, 0.0 if any violation) and enforced by the algorithm, not weights
  - Smart neighbor generation that **never proposes invalid cluster moves**
  - ``optimize_grade_list()`` function for single optimization run
  - ``optimize_multiple_times()`` function for multiple runs to find best result
  - Progress callback support for real-time optimization feedback

0.2.0
----------------------------------------------------------------------

### Added
- Streamlit app now has a "Shutdown Server" button in the sidebar for clean shutdown
- Signal handlers for graceful shutdown on SIGINT (Ctrl+C) and SIGTERM
- **Redesigned Assignments page** with visual student cards and teacher columns
  - Click-to-select students with visual feedback
  - Quick assign buttons for each student
  - Move students between teachers with dropdown selection
  - Auto-balance feature to evenly distribute unassigned students
  - Progress bar showing assignment completion
  - Visual teacher columns with cluster-based color coding

### Changed
- Improved teachers list layout in Streamlit app to be more compact with horizontal button layout
- Improved students list layout to be more compact with consolidated attributes display

0.1.0
----------------------------------------------------------------------

### Added
- Initial creation of the tool
