from HLL import HyperLogLog


def calculate_cardinality(reader):
    """Calculate the cardinality of the trace using HyperLogLog."""

    hll = HyperLogLog()
    s = set()

    for req in reader:
        hll.add(str(req.obj_id))
        s.add(req.obj_id)

    return hll.cardinality()
