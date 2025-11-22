import random
from typing import Dict, Any, Tuple, List
from ..utils.operations import (
    generate_schedule,
    inter_machine_swap,
    block_move,
    random_move,
    shuffle_machine,
    intra_machine_swap,
    lookahead_insertion,
    partial_precedence_repair,
)


def random_explore(
    schedule: Dict[int, List[int]], tasks: Dict[int, Any], n_ops: int = 1
):
    # Explore
    operation_pool: List[Tuple[callable, Dict]] = [
        (random_move, {"schedule": schedule}),
        (block_move, {"schedule": schedule}),
        (generate_schedule, {"tasks": tasks, "n_machines": len(schedule.keys())}),
        (inter_machine_swap, {"schedule": schedule}),
        (intra_machine_swap, {"schedule": schedule}),
        (
            shuffle_machine,
            {
                "schedule": schedule,
                "n_machines": random.randint(1, len(schedule.keys()) // 2),
            },
        ),
    ]
    for _ in range(n_ops):
        operation, kwargs = random.choice(operation_pool)
        new_schedule = operation(**kwargs)

    return new_schedule


def exploit(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    obj_function: callable,
    n_ops: int = 1,
    energy_constraint: Dict[str, Any] = None,
    precedences: Dict[int, List[int]] = None,
    setups: List[Tuple[int, int]] = None,
    total_resource: Dict[int, Any] = None,
    alpha_energy: float = 0.25,
    alpha_load: float = 0.25,
):
    # Exploit
    operation_pool: List[Tuple[callable, Dict]] = [
        (intra_machine_swap, {"schedule": schedule}),
        (inter_machine_swap, {"schedule": schedule}),
        (
            lookahead_insertion,
            {
                "schedule": schedule,
                "tasks": tasks,
                "attempts": random.randint(20, 30),
                "obj_function": obj_function,
                "energy_constraint": energy_constraint,
                "precedences": precedences,
                "setups": setups,
                "total_resource": total_resource,
                "alpha_energy": alpha_energy,
                "alpha_load": alpha_load,
            },
        ),
    ]

    for _ in range(n_ops):
        operation, kwargs = random.choice(operation_pool)
        new_schedule = operation(**kwargs)

    # Partial fix
    if precedences is not None:
        new_schedule = partial_precedence_repair(
            schedule=new_schedule,
            tasks=tasks,
            precedences=precedences,
            setups=setups,
        )

    return new_schedule
