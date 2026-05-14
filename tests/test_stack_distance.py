from dataclasses import dataclass

import pytest

from stack_distance import calculate_stack_distance


@dataclass
class Req:
    id: object


def make_reader(ids):
    return [Req(id=x) for x in ids]


@pytest.mark.parametrize(
    "ids,include_cold_miss_flag,expected",
    [
        ([], False, []),
        ([], True, []),
        ([1, 2, 3], False, []),
        ([1, 2, 3], True, [-1, -1, -1]),
        ([1, 1, 1], False, [1, 1]),
        ([1, 1, 1], True, [-1, 1, 1]),
        ([1, 2, 1, 3, 1, 2], False, [2, 2, 3]),
        ([1, 2, 1, 3, 1, 2], True, [-1, -1, 2, -1, 2, 3]),
        ([1, 2, 3, 2, 1, 2, 3], False, [2, 3, 2, 3]),
        ([1, 2, 3, 2, 1, 2, 3], True, [-1, -1, -1, 2, 3, 2, 3]),
        (["a", "b", "a"], False, [2]),
        (["a", "b", "a"], True, [-1, -1, 2]),
    ],
)
def test_calculate_stack_distance_cases(ids, include_cold_miss_flag, expected):
    reader = make_reader(ids)
    got = calculate_stack_distance(
        reader, include_cold_miss_flag=include_cold_miss_flag
    )
    assert got == expected


def test_cold_miss_skipped_when_flag_false_does_not_raise():
    reader = make_reader([1])
    got = calculate_stack_distance(reader, include_cold_miss_flag=False)
    assert got == []


def _reference_stack_distance(ids, include_cold_miss_flag):
    # Independent reference model: maintain an MRU stack of unique ids.
    stack = []
    in_stack = set()
    out = []

    for obj_id in ids:
        if obj_id not in in_stack:
            if include_cold_miss_flag:
                out.append(-1)
            stack.insert(0, obj_id)
            in_stack.add(obj_id)
            continue

        sd = stack.index(obj_id) + 1
        out.append(sd)
        stack.remove(obj_id)
        stack.insert(0, obj_id)

    return out


@pytest.mark.parametrize("include_cold_miss_flag", [False, True])
def test_calculate_stack_distance_very_long_single_case(include_cold_miss_flag):
    ids = (
        list(range(5000))
        + [i % 700 for i in range(20000)]
        + (list(range(699, -1, -1)) * 5)
    )
    reader = make_reader(ids)

    expected = _reference_stack_distance(ids, include_cold_miss_flag)
    got = calculate_stack_distance(
        reader, include_cold_miss_flag=include_cold_miss_flag
    )

    assert got == expected
