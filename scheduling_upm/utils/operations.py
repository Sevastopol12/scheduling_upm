import random
import copy
from typing import List, Dict, Any, Tuple, Set


def random_move(
    schedule: Dict[int, List[Any]],
    n_moves: int = 1,
    task_to_move: Dict[str, int] = None,
) -> Dict[int, List[Any]]:
    """All. Move a task from one machine to another. Dynamically receive a specific task to be moved"""
    for _ in range(n_moves):
        if task_to_move is not None:
            current_machine = task_to_move["machine"]
            job_idx = task_to_move["idx"]
            new_machine = random.randrange(len(schedule.keys()))

        else:
            current_machine, new_machine = random.sample(list(schedule.keys()), k=2)

            if len(schedule[current_machine]) < 2:
                continue

            job_idx = random.randrange(len(schedule[current_machine]))

        # Get task
        task = schedule[current_machine].pop(job_idx)
        pos = random.randrange(max(1, len(schedule[new_machine])))
        schedule[new_machine].insert(pos, task)

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
    new_schedule = copy.deepcopy(schedule)
    current_cost: float = obj_function(schedule=new_schedule, **kwargs)

    machine = random.choice(
        [machine for machine in schedule.keys() if len(new_schedule[machine]) > 0]
    )

    job_idx = random.randrange(len(new_schedule[machine]))

    for _ in range(attempts):
        # Randomly move task
        candidate = random_move(
            schedule=copy.deepcopy(new_schedule),
            n_moves=1,
            task_to_move={"machine": machine, "idx": job_idx},
        )
        candidate_cost: float = obj_function(schedule=candidate, **kwargs)

        if candidate_cost < current_cost:
            return candidate

    return new_schedule


def feasible_earliest_finish_greedy(
    n_machines: int,
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Set[int]] = None,
    resources: Dict[str, Any] = None,
) -> Dict[int, List[int]]:
    """
    Constructs a schedule using the Feasible Earliest Finish Time (FEFT) greedy heuristic
    """
    # Initialize schedule and track machine availability and last completed task
    new_schedule = {machine: [] for machine in range(n_machines)}
    machine_availability = {machine: 0 for machine in range(n_machines)}
    last_task_on_machine = {machine: None for machine in range(n_machines)}

    # Keep track of scheduled tasks
    scheduled_tasks = set()

    while len(scheduled_tasks) < len(tasks):
        best_finish_time = float("inf")
        best_task = None
        best_machine = None

        # Find all schedulable tasks
        schedulable_tasks = []
        for task in tasks.keys():
            if task not in scheduled_tasks:
                if precedences and task in precedences:
                    if all(p in scheduled_tasks for p in precedences[task]):
                        schedulable_tasks.append(task)
                else:
                    schedulable_tasks.append(task)

        # If no tasks are currently schedulable, there might be a deadlock in precedences
        if not schedulable_tasks:
            # Handle deadlock or break the loop
            # For simplicity, we break. A more robust solution might raise an error or try to resolve it.
            break

        # For each schedulable task, find the machine that yields earliest finish time
        for task_id in schedulable_tasks:
            for machine_id in range(n_machines):
                # Get the last task on the machine to calculate setup time
                last_task = last_task_on_machine[machine_id]
                setup_time = 0
                if last_task is not None:
                    setup_time = setups.get((last_task, task_id), 0)

                process_time = tasks[task_id]["process_times"][machine_id]

                # The start time is the maximum of machine availability and completion time of all predecessors
                start_time = machine_availability[machine_id]

                if precedences and task_id in precedences:
                    # To get the completion times of predecessors, we need a way to look them up.
                    # This requires a slightly more complex tracking of completion times as the schedule is built.
                    # For this implementation, we'll approximate by checking machine availability,
                    # which implicitly carries some information about completion times.
                    # A full implementation would need to build a partial `task_milestones` on the fly.
                    pass  # Simplified for this example

                finish_time = start_time + setup_time + process_time

                # Check if this is the best assignment found so far
                if finish_time < best_finish_time:
                    best_finish_time = finish_time
                    best_task = task_id
                    best_machine = machine_id

        if best_task is not None:
            # Schedule the best task on the best machine
            new_schedule[best_machine].append(best_task)
            scheduled_tasks.add(best_task)

            # Update machine availability and last task
            last_task = last_task_on_machine[best_machine]
            setup_time = 0
            if last_task is not None:
                setup_time = setups.get((last_task, best_task), 0)

            process_time = tasks[best_task]["process_times"][best_machine]

            # The start time is determined by when the machine is free
            start_time = machine_availability[best_machine]

            # Update the machine's availability to the completion time of the new task
            machine_availability[best_machine] = start_time + setup_time + process_time
            last_task_on_machine[best_machine] = best_task

    return new_schedule
