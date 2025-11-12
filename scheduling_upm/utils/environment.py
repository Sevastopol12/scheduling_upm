from typing import List, Dict, Any, Tuple, Set
import random


def generate_environment(
    n_tasks: int = 15, n_machines: int = 4, seed=None
) -> Dict[str, Any]:
    """Generate tasks, setup time of each task and precedence
       Khởi tạo các task, thời gian setup và thứ tự ưu tiên cho từng task

    Args:
        n_tasks (int, optional): number of task. Defaults to 15.
        n_machines (int, optional): number of machine. Defaults to 4.

    Returns:
        Dictionary of:

        1. tasks: dict: task_id -> {
            "proc_times": Thời gian để thực hiện task này, khác nhau với mỗi máy
            "resource": lượng tài nguyên cần để thực hiện task
        }
        2. setups: dict of (task, task): Thời gian setup để chuẩn bị cho task tiếp theo, setup time sẽ khác nhau với mỗi task
        VD: setup_time từ task a->b, được biểu diễn là (a,b) sẽ khác setup_time từ task a->c (a,c) và ngược lại
    """
    if seed is not None:
        random.seed(seed)

    # Generate tasks
    tasks: Dict[int, Any] = {}
    for t in range(n_tasks):
        times: List[int] = process_time_on_each_machine(n_machines=n_machines)

        tasks[t] = {
            "process_times": times,
        }

    # Sequence-dependent setup times between tasks
    setup_time = generate_sequence_dependent_constraint(n_tasks=n_tasks)
    precedences = generate_precedences_constraint(n_tasks=n_tasks)
    resources = generate_resource_constraint(n_machines=n_machines, n_tasks=n_tasks)

    return {
        "n_tasks": n_tasks,
        "n_machines": n_machines,
        "tasks": tasks,
        "setups": setup_time,
        "precedences": precedences,
        "resources": resources,
    }


def process_time_on_each_machine(n_machines: int) -> List[int]:
    times: List[int] = []
    for _ in range(n_machines):
        # Performance coefficient
        modifier: float = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        base_process_time: int = random.randint(5, 30)
        times.append(max(1, int(base_process_time * modifier)))
    return times


def resource_usage_on_each_machine(n_machines: int) -> Tuple[List[int], List[int]]:
    setup_usages: List[int] = []
    process_usages: List[int] = []

    for _ in range(n_machines):
        # Performance coefficient
        modifier: float = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        process_resource: int = int(random.randint(5, 20) * modifier)
        setup_resource: int = int(random.randint(5, 20) * modifier)

        setup_usages.append(int(setup_resource * modifier))
        process_usages.append(int(process_resource * modifier))

    return setup_usages, process_usages


def generate_sequence_dependent_constraint(n_tasks: int) -> Dict[Tuple[int, int], int]:
    """
    Khởi tạo mối quan hệ thứ tự của từng công việc.
    Tham số mẫu {
        (task_a, task_b): setup_time,
        (task_a, task_c): setup_time,
        ...
    }
    """
    setup_time = {}
    for task_a in range(n_tasks):
        for task_b in range(n_tasks):
            setup_time[(task_a, task_b)] = (
                0 if task_a == task_b else random.randint(0, 10)
            )
    return setup_time


def generate_precedences_constraint(n_tasks: int):
    """Generate precedences constraint

    Args:
        n_tasks (int): number of tasks
    Return:
        precedences (Dict): task_a and its precedence:
        sample: {
            task_a: Set[task_b, task_c,...]
        }
    """
    n_precedences = random.randint(1, int(n_tasks * 0.5))
    samples = range(n_tasks)
    precedences: Dict[int, Set[int]] = {}

    for _ in range(n_precedences):
        task_a, task_a_precedence = random.sample(samples, 2)

        # If task_a's precedence were including it as its precedence, move on to the next iteration
        if (
            precedences.get(task_a_precedence, None) is not None
            and task_a in precedences[task_a_precedence]
        ):
            continue

        if precedences.get(task_a, None) is None:
            precedences[task_a] = set()
        precedences[task_a].add(task_a_precedence)

    return precedences


def generate_resource_constraint(
    n_machines: int = 2, n_tasks: int = 4
) -> Dict[str, Any]:
    max_process_resource = int(n_machines * 10)  # random.choice([0.7, 0.8, 0.9, 1.0])
    max_setup_resource = int(n_machines * 10)  # random.choice([0.7, 0.8, 0.9, 1.0])

    resources: Dict[str, Any] = {
        "max_process_resource": max_process_resource,
        "max_setup_resource": max_setup_resource,
        "task_resources": {},
    }

    for task in range(n_tasks):
        setup_usage, process_usage = resource_usage_on_each_machine(
            n_machines=n_machines
        )
        resources["task_resources"][task] = {
            "process_usage": process_usage,
            "setup_usage": setup_usage,
        }

    return resources


if __name__ == "__main__":
    generate_environment()
