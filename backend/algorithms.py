
# =====================================
# Short Tasks algorithm
# =====================================

def priority_value(priority: str) -> int:
    """
    Convert task priority into a number.

    Higher number = higher priority.
    """

    priority = priority.lower()

    if priority == "high":
        return 3

    if priority == "medium":
        return 2

    if priority == "low":
        return 1

    return 0

# ====== Using Merge Sort to sort tasks by priority ======

def sort_tasks_by_priority(tasks: list) -> list:
    """
    Sort tasks from High → Medium → Low
    using the Merge Sort algorithm.
    """

    priority_order = {
        "High": 1,
        "Medium": 2,
        "Low": 3
    }

    def merge_sort(items):
        # Base case: 0 or 1 item is already sorted
        if len(items) <= 1:
            return items

        # Find the middle
        middle = len(items) // 2

        # Divide the list into two parts
        left = merge_sort(items[:middle])
        right = merge_sort(items[middle:])

        # Merge the sorted parts
        result = []
        i = 0
        j = 0

        while i < len(left) and j < len(right):

            left_priority = priority_order.get(
                left[i].priority,
                99
            )

            right_priority = priority_order.get(
                right[j].priority,
                99
            )

            if left_priority <= right_priority:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        # Add remaining left items
        result.extend(left[i:])

        # Add remaining right items
        result.extend(right[j:])

        return result

    return merge_sort(tasks)


    print("\nTasks sorted by priority:")

    for task in sorted_tasks:
        print(f"{task.priority}: {task.title}")


# ==========================================
# Insertion Sort
# ==========================================

def insertion_sort(items: list, key=lambda item: item):
    """
    Sort a list using the Insertion Sort algorithm.

    The original list is not modified.

    key:
        Function used to determine the value
        that should be compared.
    """

    result = items.copy()

    for i in range(1, len(result)):

        current_item = result[i]
        current_value = key(current_item)

        j = i - 1

        while j >= 0 and key(result[j]) > current_value:

            result[j + 1] = result[j]
            j -= 1

        result[j + 1] = current_item

    return result


# ==========================================
# Linear Search
# ==========================================

def linear_search(
    items: list,
    target,
    key=lambda item: item
):
    """
    Search for a value using Linear Search.

    Returns the first matching item.
    Returns None when no match is found.
    """

    for item in items:

        if key(item) == target:
            return item

    return None


# ============================
# Binary Search by id ascending
# ============================
# Binary Search
# ============================

def binary_search_task(
    tasks: list,
    target_value,
    key=lambda task: task.id
):
    """
    Find a task using Binary Search.

    The tasks must already be sorted according
    to the same key used for searching.

    By default, the task ID is used.

    Example:
        binary_search_task(tasks, 4)

    For title searching:
        binary_search_task(
            tasks,
            "Learn FastAPI CRUD",
            key=lambda task: task.title
        )
    """

    left = 0
    right = len(tasks) - 1

    while left <= right:

        middle = (left + right) // 2

        current_value = key(tasks[middle])

        if current_value == target_value:
            return tasks[middle]

        elif current_value < target_value:
            left = middle + 1

        else:
            right = middle - 1

    return None



# ============================
# Temporary Binary Search test
# ============================

# class TestTask:
    # def __init__(self, task_id):
        # self.id = task_id


# test_tasks = [
    # TestTask(1),
    # TestTask(2),
    # TestTask(3),
    # TestTask(4),
    # TestTask(5)
# ]

# result = binary_search_task(test_tasks, 4)

# if result:
    # print("Task found:", result.id)
# else:
    # print("Task not found")



# ============================
# Adding task status counting algorithm
# =====================================

def count_tasks_by_status(tasks: list) -> dict:
    """
    Count tasks according to their status.
    """

    counts = {
        "Pending": 0,
        "In Progress": 0,
        "Completed": 0
    }

    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1

    counts["Total"] = len(tasks)

    return counts
