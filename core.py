import numpy as np


def five_number_summary(values: list):
    min = np.min(values)
    q1 = np.percentile(values, 25)
    median = np.median(values)
    q3 = np.percentile(values, 75)
    max = np.max(values)
    return {
        "min": min,
        "q1": q1,
        "median": median,
        "q3": q3,
        "max": max
    }

