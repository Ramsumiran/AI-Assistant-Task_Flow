
# =====================================
# TaskFlow Algorithm Correctness Check
# =====================================

from algorithms import (
    insertion_sort,
    linear_search,
    binary_search_task,
    sort_tasks_by_priority,
    count_tasks_by_status
)


# =====================================
# Simple test record
# =====================================

class TestTask:
    def __init__(self, task_id, title, priority):
        self.id = task_id
        self.title = title
        self.priority = priority


# =====================================
# Test data
# =====================================

tasks = [
    TestTask(3, "Task C", "Low"),
    TestTask(1, "Task A", "High"),
    TestTask(4, "Task D", "Medium"),
    TestTask(2, "Task B", "High")
]


# =====================================
# Insertion Sort test
# =====================================

sorted_tasks = insertion_sort(
    tasks,
    key=lambda task: task.id
)

ids = [task.id for task in sorted_tasks]

if ids == [1, 2, 3, 4]:
    print("PASS: insertion_sort")
else:
    print("FAIL: insertion_sort")


# =====================================
# Binary Search test
# =====================================

found_task = binary_search_task(
    sorted_tasks,
    3
)

if found_task is not None and found_task.id == 3:
    print("PASS: binary_search")
else:
    print("FAIL: binary_search")


# =====================================
# Linear Search test
# =====================================

found_task = linear_search(
    tasks,
    "Task D",
    key=lambda task: task.title
)

if found_task is not None and found_task.id == 4:
    print("PASS: linear_search")
else:
    print("FAIL: linear_search")


# =====================================
# Priority sorting test
# =====================================

priority_tasks = sort_tasks_by_priority(tasks)

priorities = [
    task.priority
    for task in priority_tasks
]

if priorities == [
    "High",
    "High",
    "Medium",
    "Low"
]:
    print("PASS: priority sorting")
else:
    print("FAIL: priority sorting")


# =====================================
# Empty list tests
# =====================================

if insertion_sort([], key=lambda task: task.id) == []:
    print("PASS: empty insertion_sort")
else:
    print("FAIL: empty insertion_sort")


if linear_search(
    [],
    "Task",
    key=lambda task: task.title
) is None:
    print("PASS: empty linear_search")
else:
    print("FAIL: empty linear_search")


print("\nAlgorithm checks completed.")
