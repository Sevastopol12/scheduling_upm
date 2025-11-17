import random
import copy
from typing import Dict, Any, Tuple, List, Callable
from ..utils.operations import (
    generate_schedule,
    inter_machine_swap,
    random_move,
    shuffle_machine,
    intra_machine_swap,
    lookahead_insertion,
    partial_precedence_repair,
)


def random_explore(
    tasks: Dict[int, Any],
    schedule: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    operation_pool: List[Tuple[Callable, Dict]] = [
        (random_move, {"schedule": schedule}),
        (intra_machine_swap, {"schedule": schedule}),
        (inter_machine_swap, {"schedule": schedule}),
        (
            generate_schedule,
            {"tasks": tasks, "n_machines": len(schedule.keys())},
        ),
        (
            shuffle_machine,
            {
                "schedule": schedule,
                "n_machines": random.randint(1, max(1, len(schedule.keys()) // 2)),
            },
        ),
    ]

    operation, kwargs = random.choice(operation_pool)
    new_schedule = operation(**kwargs)
    return new_schedule


def discrete_spiral_update(
    schedule: Dict[int, List[int]],
    best_schedule: Dict[int, List[int]],
) -> Dict[int, List[int]]:
    """
    Design specifically for WOA. Moves the current schedule towards the best schedule by partially imitating best whale's task order
    """
    new_schedule = copy.deepcopy(schedule)
    machines_to_update = random.sample(
        list(schedule.keys()), k=random.randint(1, max(1, len(schedule.keys()) // 2))
    )

    for machine in machines_to_update:
        current_tasks = new_schedule[machine]
        best_tasks_on_machine = best_schedule.get(machine, [])
        priority = {task: idx for idx, task in enumerate(best_tasks_on_machine)}
        new_schedule[machine] = sorted(
            current_tasks, key=lambda task: priority.get(task, float("inf"))
        )

    return new_schedule


def discrete_shrinking_mechanism(
    best_schedule: Dict[int, List[int]],
    obj_function: callable,
    tasks: Dict[int, Any],
    setups: List[Tuple[int, int]],
    precedences: Dict[int, List[int]],
    energy_constraint: Dict[str, Any],
    total_resource: Dict[str, Any],
    n_moves: int = 2,
) -> Dict[int, List[int]]:
    """
    Design specifically for WOA. Creates a new schedule by making small random adjustments to the best schedule
    """
    new_schedule = copy.deepcopy(best_schedule)
    operation_pool: List[Callable] = [
        (intra_machine_swap, {"schedule": new_schedule}),
        (inter_machine_swap, {"schedule": new_schedule}),
        (
            lookahead_insertion,
            {
                "attempts": random.randint(20, 30),
                "schedule": new_schedule,
                "obj_function": obj_function,
                "tasks": tasks,
                "setups": setups,
                "precedences": precedences,
                "energy_constraint": energy_constraint,
                "total_resource": total_resource,
            },
        ),
    ]

    for _ in range(n_moves):
        operation, according_args = random.choice(operation_pool)
        new_schedule = operation(**according_args)

    if precedences is not None:
        # Partial fix
        new_schedule = partial_precedence_repair(
            schedule=new_schedule,
            tasks=tasks,
            precedences=precedences,
            setups=setups,
        )

    return new_schedule
