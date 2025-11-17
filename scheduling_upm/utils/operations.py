import random
import copy
from typing import List, Dict, Any, Tuple, Set
from .evaluation import record_milestones


def random_move(
    schedule: Dict[int, List[Any]],
    specified_task: Dict[str, int] = None,
) -> Dict[int, List[Any]]:
    """
    All. Move a task from one machine to another. Dynamically receive a specific task to be moved.
    Specified task must cover "running-machine" and "index on that machine"
    """
    if specified_task is not None:
        current_machine = specified_task["machine"]
        job_idx = specified_task["idx"]
        new_machine = random.randrange(len(schedule.keys()))

    else:
        while True:
            current_machine, new_machine = random.sample(list(schedule.keys()), k=2)

            if len(schedule[current_machine]) > 0:
                break

        job_idx = random.randrange(len(schedule[current_machine]))

    # Get task
    task = schedule[current_machine].pop(job_idx)
    pos = random.randrange(max(1, len(schedule[new_machine])))
    schedule[new_machine].insert(pos, task)

    return schedule


def inter_machine_swap(schedule: Dict[int, List[int]]):
    """
    All. Swap tasks between different machines:
    """
    while True:
        machine_a, machine_b = random.sample(list(schedule.keys()), k=2)

        if len(schedule[machine_a]) > 0 and len(schedule[machine_b]) > 0:
            break

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
    """
    All. Swap two tasks within the same machine.
    """
    while True:
        machine = random.choice(list(schedule.keys()))
        if len(schedule[machine]) > 1:
            break

    task_a, task_b = random.sample(range(len(schedule[machine])), 2)

    schedule[machine][task_a], schedule[machine][task_b] = (
        schedule[machine][task_b],
        schedule[machine][task_a],
    )

    return schedule


def lookahead_insertion(
    schedule: Dict[int, List[int]],
    obj_function: callable,
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Set[int]] = None,
    resources: Dict[str, Any] = None,
    attempts: int = 10,
):
    """Exploit. Attempt to find the best position to insert a task in"""
    new_schedule = copy.deepcopy(schedule)
    current_cost: float = obj_function(
        schedule=new_schedule,
        tasks=tasks,
        precedences=precedences,
        setups=setups,
        resources=resources,
    )

    machine = random.choice(
        [machine for machine in schedule.keys() if len(new_schedule[machine]) > 0]
    )

    job_idx = random.randrange(len(new_schedule[machine]))

    for _ in range(attempts):
        # Randomly move task
        candidate = random_move(
            schedule=copy.deepcopy(new_schedule),
            specified_task={"machine": machine, "idx": job_idx},
        )
        candidate_cost: float = obj_function(
            schedule=candidate,
            tasks=tasks,
            precedences=precedences,
            setups=setups,
            resources=resources,
        )

        if candidate_cost["total_cost"] < current_cost["total_cost"]:
            return candidate

    return new_schedule


def partial_precedence_repair(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Set[int]] = None,
):
    new_schedule = copy.deepcopy(schedule)

    temp_milestones: Dict[int, Any] = record_milestones(
        schedule=new_schedule, tasks=tasks, setups=setups
    )

    for task, sequence in precedences.items():
        task_machine = temp_milestones[task]["process_machine"]
        for precedence_task in sequence:
            if temp_milestones[precedence_task]["process_machine"] != task_machine:
                continue

            # Infeasible solution
            task_idx: int = new_schedule[task_machine].index(task)
            precedence_task_idx: int = new_schedule[task_machine].index(precedence_task)

            if task_idx < precedence_task_idx:
                # Move violated precedence up to right before its precedence
                precedence = new_schedule[task_machine].pop(precedence_task_idx)
                new_schedule[task_machine].insert(task_idx, precedence)

    return new_schedule
