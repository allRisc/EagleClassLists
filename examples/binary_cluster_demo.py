"""Demonstration of binary cluster scoring."""

from eagleclasslists.classlist import (
    ELA,
    Behavior,
    Classroom,
    Cluster,
    Gender,
    GradeList,
    Math,
    Student,
    Teacher,
)
from eagleclasslists.fitness import get_fitness_breakdown

# Create scenario with 3 GEM students, 1 with wrong teacher
teacher1 = Teacher(name="Ms. Smith", clusters=[Cluster.GEM])  # Qualified
teacher2 = Teacher(name="Mr. Jones", clusters=[])  # Not qualified

students = [
    Student(
        first_name="Alice",
        last_name="Anderson",
        gender=Gender.FEMALE,
        math=Math.HIGH,
        ela=ELA.HIGH,
        behavior=Behavior.HIGH,
        cluster=Cluster.GEM,
    ),
    Student(
        first_name="Bob",
        last_name="Brown",
        gender=Gender.MALE,
        math=Math.HIGH,
        ela=ELA.HIGH,
        behavior=Behavior.HIGH,
        cluster=Cluster.GEM,
    ),
    Student(
        first_name="Charlie",
        last_name="Clark",
        gender=Gender.MALE,
        math=Math.HIGH,
        ela=ELA.HIGH,
        behavior=Behavior.HIGH,
        cluster=Cluster.GEM,
    ),
]

# Put 2 GEM students with qualified teacher, 1 with unqualified
classroom1 = Classroom(teacher=teacher1, students=students[:2])  # Correct
classroom2 = Classroom(teacher=teacher2, students=students[2:])  # 1 wrong

grade_list = GradeList(
    classes=[classroom1, classroom2],
    teachers=[teacher1, teacher2],
    students=students,
)

print("Scenario: 3 GEM students, 1 with wrong teacher")
print("(With proportional scoring, this would be 0.667)")
print()
breakdown = get_fitness_breakdown(grade_list)
for metric, score in breakdown.items():
    print(f"  {metric}: {score:.3f}")
