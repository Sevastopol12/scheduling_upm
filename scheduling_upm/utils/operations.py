import random
import copy
from typing import List, Tuple, Dict, Any


def swap_task(schedule) -> Dict[int, List[int]]:
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
    machine_resources: Dict[int, int] = None, #thêm machine_resource
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
    if machine_resources:
        task_completion_milestones = apply_resource_constraints(
            schedule=schedule,
            tasks=tasks,
            task_completion_milestones=task_completion_milestones,
            machine_resources=machine_resources
        )

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

def apply_resource_constraints(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    task_completion_milestones: Dict[int, int],
    machine_resources: Dict[int, int],
) -> Dict[int, int]:
    

    # Sao chép milestone gốc (thời gian hoàn thành ban đầu)
    adjusted = copy.deepcopy(task_completion_milestones)

    # Lưu trạng thái tài nguyên và thời gian của từng máy
    machine_available = {m: machine_resources[m] for m in schedule.keys()}
    machine_time = {m: 0 for m in schedule.keys()}

    # Duyệt qua từng máy trong lịch
    for machine, sequence in schedule.items():
        for task in sequence:
            task_resource = tasks[task]["resource"]
            process_time = tasks[task]["process_times"][machine]

            # Tính tổng tài nguyên còn trống trong hệ thống
            total_available = sum(machine_available.values())

            # Nếu chưa đủ tài nguyên, đợi máy có task hoàn thành sớm nhất
            if total_available < task_resource:
                # Tìm thời điểm sớm nhất mà 1 task khác đã xong
                min_finish = min(adjusted.values()) if adjusted else 0

                # Reset lại tài nguyên của các máy (máy rảnh)
                for m in machine_available:
                    machine_time[m] = max(machine_time[m], min_finish)
                    machine_available[m] = machine_resources[m]

            # Bắt đầu phân bổ tài nguyên cho task này
            remaining = task_resource
            for m in machine_available:
                if remaining <= 0:
                    break
                alloc = min(machine_available[m], remaining)
                machine_available[m] -= alloc
                remaining -= alloc

            # Khi đủ resource → bắt đầu xử lý task
            start_time = max(machine_time.values())
            finish_time = start_time + process_time
            adjusted[task] = finish_time

            # Sau khi xong, hoàn trả tài nguyên
            for m in machine_available:
                machine_available[m] = machine_resources[m]

            # Cập nhật thời gian máy
            for m in machine_time:
                machine_time[m] = finish_time

    return adjusted
