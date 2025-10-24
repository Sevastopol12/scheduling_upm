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

 # ràng buộc thứ tự trước sau ehehehe        
    precedences = []
    max_relations = (n_tasks*(n_tasks-1))/2 # này là công thức số lượng quan hệ tối đa có thể có
    num_relations = random.randint(1, max_relations) # cho random số lượng quan hệ trước sau, không nhất thiết tất cả phải có
    for checkvar in range(num_relations): # ở đây t check 1 tí, để không bị kiểu 1 trước 2, 2 trước 3 nhưng 3 lại trước 1
        a, b = random.sample(range(n_tasks),2)
        if a > b:
            a, b = b, a
        if (a, b) not in precedences:
            precedences.append((a, b))
     
    return tasks, setup_time, precedences

   

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
    precedences: List[Tuple[int, int]], # này là danh sách  thứ tự trước sau, kiểu a, b thì a làm trước b
    penalty_point: int = 1000 # đây là hình phạt, phải cho 1 số lớn hẳng để khi mà nó sai là cái thời gian tính ra của nó lớn để nó chắc chắn bị loại

) -> Tuple:
    """Objective: Minimize makespan"""
    # Calculate total-process time of each machine. Accounts for setup time
    machine_makespan: Dict[int, int] = {machine: 0 for machine in schedule.keys()}
    time_finish_task: Dict [int, int] = {} # đây chính là nơi lưu thời gian hoàn thành. ví dụ như là task a, b thì thời gian b nó phải lớn hơn a, ngược lại là sai

    for machine, task_sequence in schedule.items():
        current_time = 0 # đặt cái thời gian ban đầu, chưa chạy task nào của máy là 0
        for idx in range(len(task_sequence)):
            # task's process time
            task = task_sequence[idx]
            process_time = tasks[task]["proc_times"][machine]
            # setup time when changing task
            setup_time = (
                0 if idx < 1 else setups[task_sequence[idx - 1], task_sequence[idx]]
            )
            machine_makespan[machine] += process_time + setup_time
            current_time += process_time + setup_time # cái current time lúc này phải tính bằng công thức là thời gian chạy task đó và thời gian chạy của task trước đó
            time_finish_task[task] = current_time # từ đó t ra được cái thời điểm task hoàn thành theo cái ý ở trên 

    makespan = max(
        [total_process_time for total_process_time in machine_makespan.values()]
    )
# check var 1 tí thôi, kiểm tra ràng buộc trước sau thông qua cái thời gian hoàn thành task.
    penalty = 0
    for a, b in precedences:
         if time_finish_task.get(a, float('inf')) > time_finish_task.get(b, 0):
            penalty += penalty_point
        
    return makespan + penalty


if __name__ == "__main__":
    generate_environment()
