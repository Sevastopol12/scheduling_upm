import random
from typing import Dict, Any, Tuple, List
from ..utils.operations import (
    generate_schedule,
    inter_machine_swap,
    random_move,
    shuffle_machine,
    intra_machine_swap,
    critical_task_move,
    lookahead_insertion,
)


def random_explore(schedule: Dict[int, List[int]], tasks: Dict[int, Any]):
    # Early stage: Explore
    operation_pool: List[Tuple[callable, Dict]] = [
        (random_move, {"schedule": schedule, "n_moves": random.randint(1, 10)}),
        (generate_schedule, {"tasks": tasks, "n_machines": len(schedule.keys())}),
        (intra_machine_swap, {"schedule": schedule}),
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
    ]

    operation, kwargs = random.choice(operation_pool)
    schedule = operation(**kwargs)

    return schedule

def exploit(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    obj_function: callable,
    **kwargs,
):
    # Late stage: Exploit
    operation_pool: List[Tuple[callable, Dict]] = [
        (inter_machine_swap, {"schedule": schedule}),
        (intra_machine_swap, {"schedule": schedule}),
        (critical_task_move, {"schedule": schedule, "tasks": tasks}),
        (
            lookahead_insertion,
            {
                "schedule": schedule,
                "tasks": tasks,
                "attempts": random.randint(1, 10),
                "obj_function": obj_function,
                **kwargs,
            },
        ),
    ]

    operation, kwargs = random.choice(operation_pool)
    schedule = operation(**kwargs)

    return schedule