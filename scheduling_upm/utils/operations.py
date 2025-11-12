import random
from typing import List, Dict, Any


def random_move(
    schedule: Dict[int, List[Any]], n_moves: int = 1
) -> Dict[int, List[Any]]:
    """All. Move a task from one machine to another"""
    for _ in range(n_moves):
        machine_a, machine_b = random.sample(list(schedule.keys()), k=2)

        if len(schedule[machine_a]) < 2:
            continue

        job_idx = random.randrange(len(schedule[machine_a]))
        task = schedule[machine_a].pop(job_idx)

        pos = random.randrange(len(schedule[machine_b]) + 1)
        schedule[machine_b].insert(pos, task)

    return schedule


def inter_machine_swap(schedule: Dict[int, List[int]], n_swaps: int = 1):
    """
    All. Swap tasks between different machines:
    """
    for _ in range(n_swaps):
        machine_a, machine_b = random.sample(list(schedule.keys()), k=2)

        if len(schedule[machine_a]) < 1 or len(schedule[machine_b]) < 1:
            continue

        task_a = random.randrange(len(schedule[machine_a]))
        task_b = random.randrange(len(schedule[machine_b]))

        schedule[machine_a][task_a], schedule[machine_b][task_b] = (
            schedule[machine_b][task_b],
            schedule[machine_a][task_a],
        )

    return schedule


def generate_schedule(
    tasks: Dict[int, Any], n_machines: int = 4
) -> Dict[int, List[int]]:
    """Initial / Explore. Generate a whole new schedule"""
    schedule: Dict[int, List[int]] = {machine: [] for machine in range(n_machines)}
    shuffled_tasks = list(tasks.keys())
    random.shuffle(shuffled_tasks)

    for idx, task in enumerate(shuffled_tasks):
        schedule[idx % n_machines].append(task)

    return schedule


def shuffle_machine(
    schedule: Dict[int, List[Any]], n_machines: int = 1
) -> Dict[int, List[Any]]:
    """Explore. Shuffle task order on random machine."""
    machines = random.sample(list(schedule.keys()), n_machines)
    for machine in machines:
        if len(schedule[machine]) > 0:
            random.shuffle(schedule[machine])

    return schedule


def intra_machine_swap(schedule: Dict[int, List[Any]]) -> Dict[int, List[Any]]:
    """All. Swap two tasks within the same machine"""
    machine = random.choice(list(schedule.keys()))
    if len(schedule[machine]) > 1:
        task_a, task_b = random.sample(range(len(schedule[machine])), 2)
        schedule[machine][task_a], schedule[machine][task_b] = (
            schedule[machine][task_a],
            schedule[machine][task_b],
        )

    return schedule


def critical_task_move(schedule: Dict[int, List[int]], tasks: Dict[int, Any]):
    """Transition-Exploit stage. Move a longest-processing task from one machine to another"""
    machine_a, machine_b = random.sample(list(schedule.keys()), 2)
    if len(schedule[machine_a]) < 1:
        return schedule

    longest_task_idx: int = max(
        range(len(schedule[machine_a])),
        key=lambda task_idx: tasks[schedule[machine_a][task_idx]]["process_times"][
            machine_a
        ],
    )
    task = schedule[machine_a].pop(longest_task_idx)
    # insert near best position
    insert_position: int = random.randrange(len(schedule[machine_b]) + 1)
    schedule[machine_b].insert(insert_position, task)

    return schedule


def lookahead_insertion(
    schedule: Dict[int, List[int]], obj_function: callable, attempts: int = 10, **kwargs
):
    """Exploit. Attempt to find the best position to insert a task in"""
    new_schedule = {machine: sequence for machine, sequence in schedule.items()}
    current_cost: float = obj_function(schedule=new_schedule, **kwargs)

    for _ in range(attempts):
        # Randomly move task
        candidate = random_move(schedule=new_schedule)
        candidate_cost: float = obj_function(schedule=candidate, **kwargs)

        if candidate_cost < current_cost:
            return candidate

    return new_schedule



