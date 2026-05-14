def calculate_stack_distance(reader, include_cold_miss_flag=False):
    """
    Calculate stack distance for each request in the trace.

    Stack distance = number of unique objects accessed since the last access to this object.
    Cold miss (first access):
        - include_cold_miss_flag=True  → appends -1
        - include_cold_miss_flag=False → skips the entry

    Returns a list of stack_distance values.
    """
    results = []

    from sortedcontainers import SortedList

    lru = SortedList()
    last_time = {}

    time = 0
    for req in reader:
        obj_id = req.id

        if obj_id not in last_time:
            if include_cold_miss_flag:
                results.append(-1)
        else:
            t = last_time[obj_id]
            sd = lru.bisect_right(-t)
            results.append(sd)
            lru.remove(-t)

        last_time[obj_id] = time
        lru.add(-time)
        time += 1

    return results
