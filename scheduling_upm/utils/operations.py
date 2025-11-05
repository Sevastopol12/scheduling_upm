import random
from typing import List, Tuple, Dict, Any


def rescheduling(
    tasks: Dict[int, Any],
    schedule: Dict[int, List[int]],
    current_iteration: int,
    total_iteration: int,
) -> Dict[int, List[int]]:
    """Adaptive schedule adjustment, Choose operation that accounts for the current state of progress"""

    new_schedule = {m: list(tasks) for m, tasks in schedule.items()}
    probability: float = random.random()

    # Keep track of iteration progess, affect adjusting behavior
    progress: float = current_iteration / total_iteration

    if probability < 0.7 * (1 - progress):
        # Early stage operations
        operation_pool: List[Tuple[callable, Dict]] = [
            (inter_machine_swap, {"schedule": schedule}),
            (random_move, {"schedule": schedule}),
            (shuffle_machine, {"schedule": schedule}),
            (generate_schedule, {"tasks": tasks, "n_machines": len(schedule.keys())}),
        ]
    else:
        # Mid stage operations
        operation_pool: List[Tuple[callable, Dict]] = [
            (inter_machine_swap, {"schedule": schedule}),
            (intra_machine_swap, {"schedule": schedule}),
            (critical_task_move, {"schedule": schedule, "tasks": tasks}),
        ]

    operation, kwargs = random.choice(operation_pool)
    new_schedule = operation(**kwargs)
    # Precedence constraint: Repair schedule's if violated
    # TODO

    return new_schedule


def random_move(schedule: Dict[int, List[Any]]) -> Dict[int, List[Any]]:
    """Early stage. Move a task from one machine to another"""
    machine_a, machine_b = random.sample(list(schedule.keys()), k=2)
    if schedule[machine_a]:
        job_idx = random.randrange(len(schedule[machine_a]))
        task = schedule[machine_a].pop(job_idx)

        pos = random.randrange(len(schedule[machine_b]) + 1)
        schedule[machine_b].insert(pos, task)

    return schedule


def inter_machine_swap(schedule: Dict[int, List[int]]):
    """
    Early stage. Swap tasks between different machines:
    """
    machine_a, machine_b = random.sample(list(schedule.keys()), k=2)
    if schedule[machine_a] and schedule[machine_b]:
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
    """Initial/ Early stage. Generate a whole new schedule"""
    schedule: Dict[int, List[int]] = {machine: [] for machine in range(n_machines)}
    shuffled_tasks = list(tasks.keys())
    random.shuffle(shuffled_tasks)

    for idx, task in enumerate(shuffled_tasks):
        schedule[idx % n_machines].append(task)
    return schedule


def shuffle_machine(schedule: Dict[int, List[Any]]) -> Dict[int, List[Any]]:
    """Early stage. Shuffle task order on random machine"""
    machine = random.choice(list(schedule.keys()))
    random.shuffle(schedule[machine])
    return schedule


def intra_machine_swap(schedule: Dict[int, List[Any]]) -> Dict[int, List[Any]]:
    """Mid stage. Swap two tasks within the same machine"""
    machine = random.choice(list(schedule.keys()))
    if len(schedule[machine]) > 1:
        task_a, task_b = random.sample(range(len(schedule[machine])), 2)
        schedule[machine][task_a], schedule[machine][task_b] = (
            schedule[machine][task_a],
            schedule[machine][task_b],
        )

    return schedule


def critical_task_move(schedule: Dict[int, List[int]], tasks: Dict[int, Any]):
    """Mid-Late stage. Move a longest-processing task from one machine to another"""
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


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
) -> Tuple:
    """Objective: Minimize makespan"""

    # Compute milestones of task's completion time . Accouns for setups
    task_completion_milestones = compute_base_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )

    # TODO
    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task

    # TODO
    # Áp dụng ràng buộc resource để tính thời gian hoàn thành thực tế của từng task

    # Makespan
    makespan = max(task_completion_milestones.values())

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Cost
    cost = makespan
    return cost


def compute_base_milestones(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
):
    # Lưu trữ thời gian hoàn thành của mỗi task
    task_completion_milestones: Dict[int, int] = {}

    # Lưu trữ các mốc thời gian của mỗi máy khi hoàn thành 1 task
    machine_completion_milestone: Dict[int, int] = {
        machine: 0 for machine in schedule.keys()
    }

    for machine, sequence in schedule.items():
        for idx in range(len(sequence)):
            # task's process time
            task = sequence[idx]
            process_time = tasks[task]["process_times"][machine]
            setup_time = 0 if idx < 1 else setups[sequence[idx - 1], sequence[idx]]

            machine_completion_milestone[machine] += process_time + setup_time
            task_completion_milestones[task] = machine_completion_milestone[machine]

    return task_completion_milestones
