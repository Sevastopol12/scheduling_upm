import random
import copy
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

    if probability < 0.4 * (1 - progress):
        # Early stage operations
        operation_pool: List[Tuple[callable, Dict]] = [
            (inter_machine_swap, {"schedule": schedule}),
            (random_move, {"schedule": schedule}),
            (
                shuffle_machine,
                {
                    "schedule": schedule,
                    "n_machines": random.randrange(1, len(schedule.keys())),
                },
            ),
            (generate_schedule, {"tasks": tasks, "n_machines": len(schedule.keys())}),
        ]
    elif probability < 0.7:
        # Mid stage operations
        operation_pool: List[Tuple[callable, Dict]] = [
            (inter_machine_swap, {"schedule": schedule}),
            (random_move, {"schedule": schedule}),
            (intra_machine_swap, {"schedule": schedule}),
            (critical_task_move, {"schedule": schedule, "tasks": tasks}),
        ]
    else:
        # Late stage operations
        operation_pool: List[Tuple[callable, Dict]] = [
            (
                inter_machine_swap,
                {"schedule": schedule, "tasks": tasks, "strategy": "longest"},
            ),
            (intra_machine_swap, {"schedule": schedule}),
            (critical_task_move, {"schedule": schedule, "tasks": tasks}),
        ]

    operation, kwargs = random.choice(operation_pool)
    new_schedule = operation(**kwargs)

    # Precedence constraint: Repair schedule's if violated
    # TODO

    return new_schedule


def random_move(schedule: Dict[int, List[Any]]) -> Dict[int, List[Any]]:
    """Early-Mid stage. Move a task from one machine to another"""
    machine_a, machine_b = random.sample(list(schedule.keys()), k=2)
    if len(schedule[machine_a]) < 1:
        return schedule
    task_idx = random.randrange(len(schedule[machine_a]))
    task = schedule[machine_a].pop(task_idx)

    position = (
        random.randrange(len(schedule[machine_b]))
        if len(schedule[machine_b]) > 0
        else 0
    )
    schedule[machine_b].insert(position, task)

    return schedule


def inter_machine_swap(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any] = None,
    strategy: str = "random",
):
    """
    Early-Late stage. Swap tasks between different machines. Randomly or select longest task
    Args:
         strategy: ["random", "longest"]

    """
    machine_a, machine_b = random.sample(list(schedule.keys()), k=2)
    if len(schedule[machine_a]) > 0 and len(schedule[machine_b]) > 0:
        if strategy == "random":
            task_a = random.randrange(len(schedule[machine_a]))
            task_b = random.randrange(len(schedule[machine_b]))

        elif strategy == "longest":
            task_a = max(
                range(len(schedule[machine_a])),
                key=lambda task_idx: tasks[schedule[machine_a][task_idx]][
                    "process_times"
                ][machine_a],
            )
            task_b = max(
                range(len(schedule[machine_b])),
                key=lambda task_idx: tasks[schedule[machine_b][task_idx]][
                    "process_times"
                ][machine_b],
            )

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


def shuffle_machine(
    schedule: Dict[int, List[Any]], n_machines: int = 1
) -> Dict[int, List[Any]]:
    """Early stage. Shuffle task order on random machine"""
    machines = random.sample(list(schedule.keys()), n_machines)
    for machine in machines:
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
    insert_position: int = (
        random.randrange(len(schedule[machine_b]))
        if len(schedule[machine_b]) > 0
        else 0
    )
    schedule[machine_b].insert(insert_position, task)

    return schedule


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
) -> Tuple:
    """Objective: Minimize makespan"""

    # Compute milestones of task's completion time . Accouns for setups
    task_completion_milestones = compute_base_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )
    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    if precedences:
        penalty, task_completion_milestones = precedence_constraint(
            schedule=schedule,
            task_completion_milestones=task_completion_milestones,
            setups=setups,
            precedences=precedences,
        )
        if penalty > 0:
            return penalty

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


def precedence_constraint(
    schedule: Dict[int, List[int]],
    task_completion_milestones: Dict[int, int],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
):
    # Đầu tiên t sẽ check các máy đang làm những task nào, là cơ sở cho pre vs post để check ràng buộc
    # t cũng tạo 1 bản chép, và bản chép này là để t ghi lại thời gian thực tế nó làm, nhưng vẫn có bản cũ giữ lại thời gian làm
    # ví dụ task 1 2s, task 2 3s, thì sau khi xong t vẫn có dữ liệu là task 1 2s, task 2 3s và dữ liệu làm thực tế là task 1 2s task 2 5s.
    task_to_machine = {task: m for m, seq in schedule.items() for task in seq}
    actual_completion_times = copy.deepcopy(task_completion_milestones)

    # chọn phương án pen nếu vi phạm
    PENALTY_VALUE = 10**6

    # xong phần chuẩn bị r, h t vô thì t sẽ check precedence
    # t giải quyết 2 vấn đề: nếu task k cs ràng buộc, nếu các task trên cùng máy - khác máy
    # nếu cùng, thì cứ cộng bthg, nhưng nếu trái ràng buộc thì cũng cộng bthg r cộng thêm pen
    # nếu khác, t phải cho nó chờ
    for pre, posts in precedences.items():
        for post in posts:
            if pre not in task_to_machine or post not in task_to_machine:
                continue

            machine_pre = task_to_machine[pre]
            machine_post = task_to_machine[post]

            if machine_pre == machine_post:
                seq = schedule[machine_pre]
                idx_pre = seq.index(pre)
                idx_post = seq.index(post)

                if idx_pre > idx_post:
                    return PENALTY_VALUE, actual_completion_times

            else:
                finish_pre = actual_completion_times[pre]

                seq_post = schedule[machine_post]
                idx_post = seq_post.index(post)

                if idx_post == 0:
                    start_post = 0
                else:
                    prev_task = seq_post[idx_post - 1]
                    setup_time = setups.get((prev_task, post), 0)
                    start_post = actual_completion_times[prev_task] + setup_time

                if start_post < finish_pre:
                    delay = finish_pre - start_post
                    for k in range(idx_post, len(seq_post)):
                        cur_task = seq_post[k]
                        actual_completion_times[cur_task] += delay

    return 0, actual_completion_times
