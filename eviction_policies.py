import libcachesim as lcs


def calculate_miss_ratio(cache: lcs.CacheBase, cache_size, reader):
    """
    Calculate the miss ratio of a cache for a given trace.

    Returns the miss ratio as a float.
    """

    c = cache(cache_size=cache_size, reader=reader)
    return c.process_trace(reader)
