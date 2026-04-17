"""Example usage of the fitness and simulated annealing modules."""

from eagleclasslists.classlist import (
    ELA,
    Behavior,
    Classroom,
    Gender,
    GradeList,
    Math,
    Student,
    Teacher,
)
from eagleclasslists.fitness import FitnessWeights, get_fitness_breakdown
from eagleclasslists.simulated_annealing import AnnealingConfig, optimize_grade_list

# Create a grade list with imbalanced gender distribution
teacher1 = Teacher(name="Ms. Smith", clusters=[])
teacher2 = Teacher(name="Mr. Jones", clusters=[])

# All males in one class, all females in another (imbalanced)
male_students = [
    Student(
        first_name=f"Boy{i}",
        last_name=f"Name{i}",
        gender=Gender.MALE,
        math=Math.MEDIUM,
        ela=ELA.MEDIUM,
        behavior=Behavior.MEDIUM,
    )
    for i in range(8)
]
female_students = [
    Student(
        first_name=f"Girl{i}",
        last_name=f"Name{i}",
        gender=Gender.FEMALE,
        math=Math.MEDIUM,
        ela=ELA.MEDIUM,
        behavior=Behavior.MEDIUM,
    )
    for i in range(8)
]

classroom1 = Classroom(teacher=teacher1, students=male_students)
classroom2 = Classroom(teacher=teacher2, students=female_students)

grade_list = GradeList(
    classes=[classroom1, classroom2],
    teachers=[teacher1, teacher2],
    students=male_students + female_students,
)

# Check initial fitness
print("Initial fitness breakdown:")
breakdown = get_fitness_breakdown(grade_list)
for metric, score in breakdown.items():
    print(f"  {metric}: {score:.3f}")

# Optimize with custom weights
weights = FitnessWeights(gender=5.0)  # Prioritize gender balance
config = AnnealingConfig(
    initial_temperature=10.0,
    cooling_rate=0.95,
    max_iterations=1000,
    random_seed=42,
)

optimized = optimize_grade_list(grade_list, weights=weights, config=config)

# Check optimized fitness
print("\nOptimized fitness breakdown:")
breakdown = get_fitness_breakdown(optimized)
for metric, score in breakdown.items():
    print(f"  {metric}: {score:.3f}")
