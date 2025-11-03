import random
import copy
from typing import List, Tuple, Dict, Any


def swap_task(schedule) -> Dict[int, List[int]]:
    """Adjustment in schedule, aims to minimize makespan"""
    """Adjustment in schedule, aims to minimize makespan"""
    new_schedule = copy.deepcopy(schedule)
    machines: List[int] = list(new_schedule.keys())
    probability: float = random.random()

    # Swap task between 2 machines
    if probability < 0.4:
        machine_a, machine_b = random.sample(machines, k=2)
        if new_schedule[machine_a] and new_schedule[machine_b]:
            task_a = random.randrange(len(new_schedule[machine_a]))
            task_b = random.randrange(len(new_schedule[machine_b]))

            new_schedule[machine_a][task_a], new_schedule[machine_b][task_b] = (
                new_schedule[machine_b][task_b],
                new_schedule[machine_a][task_a],
            )

    # Move a task from 1 machine to another
    elif probability < 0.8:
        machine_a, machine_b = random.sample(machines, k=2)
        if new_schedule[machine_a]:
            job_idx = random.randrange(len(new_schedule[machine_a]))
            task = new_schedule[machine_a].pop(job_idx)

            pos = random.randrange(len(new_schedule[machine_b]) + 1)
            new_schedule[machine_b].insert(pos, task)
    # Swap 2 tasks on same machine
    else:
        machine = random.choice(machines)
        if len(new_schedule[machine]) > 1:
            task_a, task_b = random.sample(range(len(new_schedule[machine])), 2)
            new_schedule[machine][task_a], new_schedule[machine][task_b] = (
                new_schedule[machine][task_a],
                new_schedule[machine][task_b],
            )
    return new_schedule


def initial_schedule(
    tasks: Dict[int, Any], n_machines: int = 4
) -> Dict[int, List[int]]:
    """Perform Round-robin scheduling method to initialize schedule"""
    schedule: Dict[int, List[int]] = {machine: [] for machine in range(n_machines)}

    for task in tasks.keys():
        schedule[task % n_machines].append(task)
    return schedule


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict [int, List[int]]
) -> Tuple:
    """Objective: Minimize makespan"""

    # Compute milestones of task's completion time . Accouns for setups
    task_completion_milestones = compute_base_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )

    # TODO
    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task

    # hướng làm ở đây thì t sẽ nạp cái ràng buộc từ bên enviroment trước
    #sau đó t sẽ duyệt hết các cái quan hệ có thể được sinh ra để xếp xếp lại thứ tự các task
    # rồi cập nhập thời gian hoàn thành khi áp dụng ràng buộc
    # à t có thắc mắc là t tưởng k tài tuple nx chớ, do ở trong hàm t vẫn thấy sài Tuple ở setup á phúc

    actual_start_times = {task: 0 for task in task_completion_milestones.keys()}
    actual_completion_times = copy.deepcopy(task_completion_milestones)

    changed = True
    while changed:
        changed = False
        for pre, posts in precedences.items():
            for post in posts:
                pre_finish = actual_completion_times[pre]
                post_proc_time = tasks[post]["process_times"][0]  
                if actual_start_times[post] < pre_finish:
                    actual_start_times[post] = pre_finish
                    actual_completion_times[post] = actual_start_times[post] + post_proc_time
                    changed = True
    task_completion_milestones = actual_completion_times
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
