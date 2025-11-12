import random
from typing import Dict, Any, Tuple, List
from ..utils.operations import (
    generate_schedule,
    inter_machine_swap,
    random_move,
    shuffle_machine,
    intra_machine_swap,
    lookahead_insertion,
)


def random_explore(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    obj_function: callable,
    **kwargs,
):
    # Explore
    operation_pool: List[Tuple[callable, Dict]] = [
        (random_move, {"schedule": schedule, "n_moves": random.randint(1, 10)}),
        (intra_machine_swap, {"schedule": schedule}),
        (generate_schedule, {"tasks": tasks, "n_machines": len(schedule.keys())}),
        (
            inter_machine_swap,
            {"schedule": schedule, "n_swaps": random.randint(1, 10)},
        ),
        (
            shuffle_machine,
            {
                "schedule": schedule,
                "n_machines": random.randint(1, len(schedule.keys()) // 2),
            },
        ),
        (
            lookahead_insertion,
            {
                "schedule": schedule,
                "tasks": tasks,
                "attempts": random.randint(10, 20),
                "obj_function": obj_function,
                **kwargs,
            },
        ),
    ]

    operation, kwargs = random.choice(operation_pool)
    new_schedule = operation(**kwargs)

    return new_schedule


def exploit(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    obj_function: callable,
    **kwargs,
):
    # Exploit
    operation_pool: List[Tuple[callable, Dict]] = [
        (random_move, {"schedule": schedule, "n_moves": random.randint(1, 3)}),
        (intra_machine_swap, {"schedule": schedule}),
        (
            inter_machine_swap,
            {"schedule": schedule, "n_swaps": random.randint(1, 3)},
        ),
        (
            lookahead_insertion,
            {
                "schedule": schedule,
                "tasks": tasks,
                "attempts": random.randint(10, 20),
                "obj_function": obj_function,
                **kwargs,
            },
        ),
    ]

    operation, kwargs = random.choice(operation_pool)
    new_schedule = operation(**kwargs)

    return new_schedule
