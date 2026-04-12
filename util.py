def calculate_unique_elements(reader):
    unique = set()
    for req in reader:
        unique.add(req.obj_id)
    return len(unique)
