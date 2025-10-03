from typing import List, Dict, Any, Tuple
import random


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

            "resource": int,
            lượng tài nguyên cần để thực hiện task

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
            times.append(max(1, int(base_proc[t] * modifier)))

        resource: int = random.randint(0, 120)
        weight: float = random.uniform(1.0, 3.0)
        tasks[t] = {
            "proc_times": times,
            "resource": resource,
            "weight": weight,  # Task's importance
        }

    # Sequence-dependent setup times between tasks
    setup_time = {}
    for task_a in range(n_tasks):
        for task_b in range(n_tasks):
            setup_time[(task_a, task_b)] = (
                0 if task_a == task_b else random.randint(0, 10)
            )

    return tasks, setup_time


def generate_schedule(
    tasks: Dict[str, Any], n_machines: int = 4
) -> Dict[int, List[int]]:
    """Perform Round-robin scheduling method to initialize schedule"""
    schedule: Dict[int, List[int]] = {machine: [] for machine in range(n_machines)}

    for task in tasks.keys():
        schedule[task % n_machines].append(task)
    return schedule


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[str, Any],
    setups: Dict[Tuple[int, int], int],
) -> Tuple:
    """Objective: Minimize makespan"""
    # Calculate total-process time of each machine. Accounts for setup time
    machine_makespan: Dict[int, int] = {machine: 0 for machine in schedule.keys()}

    for machine, task_sequence in schedule.items():
        for idx in range(len(task_sequence)):
            # task's process time
            task = task_sequence[idx]
            process_time = tasks[task]["proc_times"][machine]
            # setup time when changing task
            setup_time = (
                0 if idx < 1 else setups[task_sequence[idx - 1], task_sequence[idx]]
            )
            machine_makespan[machine] += process_time + setup_time

    makespan = max(
        [total_process_time for total_process_time in machine_makespan.values()]
    )

    return makespan


if __name__ == "__main__":
    generate_environment()
