import random
import copy
from typing import List, Dict, Any, Tuple, Set
from .evaluation import compute_base_milestones


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


def block_move(schedule: Dict[int, Any]) -> Dict[int, List[Any]]:
    """Explore. Move a block of tasks from one machine to another"""
    new_schedule = copy.deepcopy(schedule)

    # Filter out valid machine
    valid_machines: List[int] = [
        machine for machine in new_schedule.keys() if len(new_schedule[machine]) > 1
    ]

    if len(valid_machines) < 2:
        return random_move(schedule=new_schedule)
    # Target machine
    move_machine = random.choice(valid_machines)
    # Remove to avoid being pick again
    valid_machines.remove(move_machine)
    receive_machine = random.choice(valid_machines)

    # Target schedule
    move_schedule = new_schedule[move_machine]
    receive_schedule = new_schedule[receive_machine]

    # Block idx
    end = random.randrange(1, len(new_schedule[move_machine]) + 1)
    start = random.randrange(0, end)

    # Position on new machine
    new_position = random.randrange(0, max(1, len(new_schedule[receive_machine])))
    targeted_block = move_schedule[start:end]
    move_schedule = move_schedule[0:start] + move_schedule[end:]

    # Insert
    for task in targeted_block[::-1]:
        receive_schedule.insert(new_position, task)

    new_schedule[move_machine] = move_schedule
    new_schedule[receive_machine] = receive_schedule

    del valid_machines
    return new_schedule


def inter_machine_swap(schedule: Dict[int, List[int]]):
    """
    All. Swap tasks between different machines:
    """
    # Filter out valid machines
    valid_machines: List[int] = [
        machine for machine in schedule.keys() if len(schedule[machine]) > 0
    ]

    if len(valid_machines) < 2:
        return random_move(schedule=schedule)

    machine_a = random.choice(valid_machines)

    # Remove to avoid being pick again
    valid_machines.remove(machine_a)

    machine_b = random.choice(valid_machines)

    task_a = random.randrange(len(schedule[machine_a]))
    task_b = random.randrange(len(schedule[machine_b]))

    schedule[machine_a][task_a], schedule[machine_b][task_b] = (
        schedule[machine_b][task_b],
        schedule[machine_a][task_a],
    )

    del valid_machines
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
    alpha_energy: float,
    alpha_load: float,
    energy_constraint: Dict[str, Any] = None,
    precedences: Dict[int, Set[int]] = None,
    total_resource: int = None,
    attempts: int = 10,
):
    """Exploit. Attempt to find the best position to insert a task in"""
    new_schedule = copy.deepcopy(schedule)
    current_cost: float = obj_function(
        schedule=new_schedule,
        tasks=tasks,
        setups=setups,
        precedences=precedences,
        energy_constraint=energy_constraint,
        total_resource=total_resource,
        alpha_load=alpha_load,
        alpha_energy=alpha_energy,
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
            setups=setups,
            precedences=precedences,
            energy_constraint=energy_constraint,
            total_resource=total_resource,
            alpha_load=alpha_load,
            alpha_energy=alpha_energy,
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

    temp_milestones: Dict[int, Any] = compute_base_milestones(
        schedule=new_schedule, tasks=tasks, setups=setups
    )

    for precedence_task, sequence in precedences.items():
        precedence_machine = temp_milestones[precedence_task]["machine"]
        for posterior_task in sequence:
            if temp_milestones[posterior_task]["machine"] != precedence_machine:
                continue

            # Infeasible solution
            precedence_idx: int = new_schedule[precedence_machine].index(
                precedence_task
            )
            posterior_idx: int = new_schedule[precedence_machine].index(posterior_task)

            if posterior_idx < precedence_idx:
                # Move violated precedence up to right before its precedence
                precedence_task = new_schedule[precedence_machine].pop(precedence_idx)
                new_schedule[precedence_machine].insert(posterior_idx, precedence_task)

    return new_schedule
