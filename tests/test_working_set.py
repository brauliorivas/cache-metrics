from dataclasses import dataclass

import pytest

from working_set import calculate_working_set


@dataclass
class Req:
    obj_id: object


def make_reader(ids):
    return [Req(obj_id=x) for x in ids]


def reference_working_set(ids, window_size):
    out = []
    for i in range(len(ids)):
        left = max(0, i - window_size + 1)
        out.append(len(set(ids[left : i + 1])))
    return out


@pytest.mark.parametrize(
    "ids,percentage,total_unique,trim,expected",
    [
        ([], 1, None, True, []),
        ([1], 100, None, True, []),
        ([1, 2, 3], 100, None, True, []),
        ([1, 2, 1, 3, 1, 2], 50, None, True, [1, 1, 1, 1, 1]),
        ([1, 2, 1, 3, 1, 2], 50, None, False, [1, 1, 1, 1, 1, 1]),
        ([1, 2, 1, 3, 1, 2], 100, None, True, [3, 2, 3]),
        ([1, 2, 1, 3, 1, 2], 100, None, False, [1, 2, 2, 3, 2, 3]),
        ([1, 1, 1, 1], 10, None, True, [1, 1, 1]),
        ([1, 2, 3, 4], 0, None, True, [1, 1, 1]),
        ([1, 2, 3, 4], 200, None, True, []),
        ([1, 2, 1, 2], 50, 10, True, []),
        ([1, 2, 1, 2], 50, 1, True, [1, 1, 1]),
    ],
)
def test_calculate_working_set_cases(ids, percentage, total_unique, trim, expected):
    reader = make_reader(ids)
    got = calculate_working_set(
        reader,
        percentage,
        total_unique=total_unique,
        trim=trim,
    )
    assert got == expected


@pytest.mark.parametrize("trim", [False, True])
def test_calculate_working_set_very_long_single_case(trim):
    ids = (
        list(range(5000))
        + [i % 700 for i in range(20000)]
        + (list(range(699, -1, -1)) * 5)
    )
    percentage = 7
    total_unique = len(set(ids))
    window_size = max(1, int(total_unique * percentage / 100))

    expected = reference_working_set(ids, window_size)
    if trim:
        expected = expected[window_size:]

    reader = make_reader(ids)
    got = calculate_working_set(
        reader,
        percentage,
        total_unique=total_unique,
        trim=trim,
    )

    assert got == expected
