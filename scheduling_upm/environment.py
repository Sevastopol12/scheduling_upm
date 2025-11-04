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
            "proc_times": Thời gian để thực hiện task này, khác nhau với mỗi máy
            "resource": lượng tài nguyên cần để thực hiện task
        }
        setup: dict of (task, task): Thời gian setup để chuẩn bị cho task tiếp theo, setup time sẽ khác nhau với mỗi task
        VD: setup_time từ task a->b, được biểu diễn là (a,b) sẽ khác setup_time từ task a->c (a,c) và ngược lại
    """

    # Generate tasks
    tasks: Dict[int, Any] = {}
    for t in range(n_tasks):
        times: List[int] = process_time_on_each_machine(n_machines=n_machines)
        resource: int = random.randint(0, 120)
        tasks[t] = {
            "process_times": times,
            "resource": resource,
        }

    # Sequence-dependent setup times between tasks
    setup_time = generate_sequence_dependent_constraint(n_tasks=n_tasks)

    
    total_resource = 200 #resource ban đầu của pool (phải để total_resource lớn hơn resource lớn nhất của task)
  
    return {
        "n_tasks": n_tasks,
        "n_machines": n_machines,
        "tasks": tasks,
        "setups": setup_time,
        "total_resource": total_resource, #thêm total resource
    }


def process_time_on_each_machine(n_machines: int) -> List[int]:
    times: List[int] = []
    for _ in range(n_machines):
        # Performance coefficient
        modifier: float = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        base_process_time: int = random.randint(5, 30)
        times.append(max(1, int(base_process_time * modifier)))
    return times


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



if __name__ == "__main__":
    generate_environment()
