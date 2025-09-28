from typing import List, Dict, Optional, Any
import random
import numpy as np


def generate_environment(n_tasks: int = 15, n_machines: int = 4) -> Dict[str, Any]:
    """Generate tasks, setup time of each task and precedence
       Khởi tạo các task, thời gian setup và thứ tự ưu tiên cho từng task 

    Args:
        n_tasks (int, optional): number of task. Defaults to 15.
        n_machines (int, optional): number of machine. Defaults to 4.

    Returns:
        tasks: dict: task_id -> {
            "proc_times": time needed to perform this task on i'th machine: list[int], 
            Thời gian để thực hiện task này, khác nhau với mỗi máy

            "preferred_start_time": int, 
            "weight": task importance: float
        }
        setup: dict of (task, task) of len 2 -> setup_time when changing task, differences for each pair of tasks
        Thời gian setup để chuẩn bị cho task tiếp theo, setup time sẽ khác nhau với mỗi task 
        VD: setup_time từ task a->b, được biểu diễn là (a,b) sẽ khác setup_time từ task a->c (a,c) và ngược lại

        precedences: list of (task, task) denote that, say task a must be finished before task b starts
        Thứ tự ưu tiên của từng task
        VD: (a,b) có nghĩa là a bắt buộc phải được hoàn thành trước khi b được thực thi, xét trên toàn bộ máy
    """
    tasks: Dict[str, Any] = {}
    # Base processing for each task
    base_proc = [random.randint(5, 30) for _ in range(n_tasks)]

    for t in range(n_tasks):
        times: List[int] = []

        for _ in range(n_machines):
            # Performance coefficient
            modifier: float = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
            times.append(
                max(1, int(base_proc[t] * modifier)))

        preferred_start_time: int = random.randint(0, 120)
        weight: float = random.uniform(1.0, 3.0)
        tasks[t] = {
            "proc_times": times,
            "preferred_start": preferred_start_time,
            "weight": weight  # Task's importance
        }

    # Ý tưởng cho setup time và precedence, tạm thời lược bớt để đơn giản hóa khâu chuẩn bị objective function.
    # Sẽ được chỉnh sửa và thêm lại từ t ừ

    # # Sequence-dependent setup times between tasks
    # setup_time = {}
    # for task_a in range(n_tasks):
    #     for task_b in range(n_tasks):
    #         setup_time[(task_a, task_b)
    #                    ] = 0 if task_a == task_b else random.randint(0, 10)

    # # Precedence constraint
    # precedences = []
    # # Randomly pairwise precedence relations
    # for _ in range(max(1, n_tasks // 5)):
    #     task_a, task_b = random.randrange(n_tasks), random.randrange(n_tasks)
    #     if task_a != task_b:
    #         precedences.append((task_a, task_b))

    # return tasks, setup_time, precedences
    return tasks


def generate_schedule(tasks: Dict[str, Any], n_machines: int = 4) -> Dict[int, List[int]]:
    """Perform Round-robin scheduling method to initialize schedule"""
    schedule: Dict[int, List[int]] = {machine: []
                                      for machine in range(n_machines)}

    for task in tasks.keys():
        schedule[task % n_machines].append(task)
    return schedule


def objective_function(schedule: Dict[int, List[int]], tasks: Dict[str, Any]):
    # Calculate total-process time of each machine
    machine_makespan: Dict[int, int] = {
        machine: 0 for machine in schedule.keys()}

    for machine, task_sequence in schedule.items():
        for task in task_sequence:
            machine_makespan[machine] += tasks[task]['proc_times'][machine]
    return machine_makespan


if __name__ == "__main__":
    tasks = generate_environment(n_tasks=4, n_machines=2)
    schedule = generate_schedule(tasks=tasks, n_machines=2)
    makespan = objective_function(schedule, tasks)

    for key, item in tasks.items():
        print(f"{key}: {item['proc_times']}\n")

    for key, item in schedule.items():
        print(f"{key}: {item}\n")

    for key, item in makespan.items():
        print(f"{key}: {item}\n")
