

# =====================================
# TaskFlow Algorithm Benchmark
# =====================================

from algorithms import insertion_sort


# =====================================
# Test record
# =====================================

class TestTask:
    def __init__(self, task_id, title):
        self.id = task_id
        self.title = title


# =====================================
# Insertion Sort with comparison count
# =====================================

def insertion_sort_count(records):
    records = records.copy()
    comparisons = 0

    for i in range(1, len(records)):

        current = records[i]
        j = i - 1

        while j >= 0:
            comparisons += 1

            if records[j].id <= current.id:
                break

            records[j + 1] = records[j]
            j -= 1

        records[j + 1] = current

    return records, comparisons


# =====================================
# Linear Search with comparison count
# =====================================

def linear_search_count(records, target):
    comparisons = 0

    for record in records:

        comparisons += 1

        if record.id == target:
            return record, comparisons

    return None, comparisons


# =====================================
# Binary Search with comparison count
# =====================================

def binary_search_count(records, target):
    left = 0
    right = len(records) - 1
    comparisons = 0

    while left <= right:

        middle = (left + right) // 2

        # Compare target with middle value
        comparisons += 1

        if records[middle].id == target:
            return records[middle], comparisons

        # Second comparison only when needed
        comparisons += 1

        if records[middle].id < target:
            left = middle + 1
        else:
            right = middle - 1

    return None, comparisons


# =====================================
# Run benchmark
# =====================================

dataset_sizes = [10, 500, 3000]

print("TaskFlow Algorithm Benchmark")
print("=" * 70)

for size in dataset_sizes:

    # Create reverse-ordered data
    tasks = [
        TestTask(i, f"Task {i}")
        for i in range(size, 0, -1)
    ]

    # ---------------------------------
    # Insertion Sort
    # ---------------------------------

    _, insertion_comparisons = insertion_sort_count(tasks)

    # ---------------------------------
    # Sort data for searching
    # ---------------------------------

    sorted_tasks = sorted(
        tasks,
        key=lambda task: task.id
    )

    # ---------------------------------
    # Search targets
    # ---------------------------------

    targets = {
        "Beginning": 1,
        "Middle": size // 2,
        "End": size
    }

    print(f"\nDataset size: {size}")
    print(f"Insertion Sort comparisons: {insertion_comparisons}")

    # ---------------------------------
    # Search benchmark
    # ---------------------------------

    for position, target in targets.items():

        _, linear_comparisons = linear_search_count(
            sorted_tasks,
            target
        )

        _, binary_comparisons = binary_search_count(
            sorted_tasks,
            target
        )

        print(f"\n{position} target: {target}")
        print(f"Linear Search comparisons: {linear_comparisons}")
        print(f"Binary Search comparisons: {binary_comparisons}")
