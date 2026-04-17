Changelog
====================================================================================================

All notable changes to ``EagleClassLists`` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
