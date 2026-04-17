from util import calculate_unique_elements


def calculate_working_set(reader, percentage, total_unique=None, trim=True):
    from collections import deque

    if total_unique is None:
        total_unique = calculate_unique_elements(reader)

    window_size = max(1, int(total_unique * percentage / 100))

    results = []
    window = deque()
    window_set = {}  # obj_id -> count of occurrences in window

    for req in reader:
        obj_id = req.obj_id

        # Add new element to the right
        window.append(obj_id)
        window_set[obj_id] = window_set.get(obj_id, 0) + 1

        # Pop oldest element from the left if window exceeds size
        if len(window) > window_size:
            old = window.popleft()
            window_set[old] -= 1
            if window_set[old] == 0:
                del window_set[old]

        results.append(len(window_set))

    if trim:
        results = results[window_size:]

    return results
