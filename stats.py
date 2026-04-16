from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class SummaryStats:
    min: float = 0
    q1: float = 0
    q2: float = 0
    q3: float = 0
    max: float = 0
    skewness: float = 0


def five_number_summary(data: list[float] | np.ndarray) -> SummaryStats:
    arr = np.asarray(data, dtype=np.float64)
    q1, q2, q3 = np.percentile(arr, [25, 50, 75])

    return SummaryStats(
        min=arr.min(),
        q1=q1,
        q2=q2,
        q3=q3,
        max=arr.max(),
        skewness=stats.skew(arr),
    )
