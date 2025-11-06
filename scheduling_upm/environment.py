from typing import List, Dict, Any, Tuple
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
        tasks: dict: task_id -> {
            "proc_times": Thời gian để thực hiện task này, khác nhau với mỗi máy
            "resource": lượng tài nguyên cần để thực hiện task
        }
        setup: dict of (task, task): Thời gian setup để chuẩn bị cho task tiếp theo, setup time sẽ khác nhau với mỗi task
        VD: setup_time từ task a->b, được biểu diễn là (a,b) sẽ khác setup_time từ task a->c (a,c) và ngược lại
    """
    if seed is not None:
        random.seed(seed)
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

    # phần setup_time tạo ở đây nên t cx tạo cái precedences ở đây luôn
    precedences = generate_precedence_constraints(n_tasks = n_tasks) #tạo precedence mà ở đây lấy giá trị tham số n_task mà phúc dương đã tạo trong hàm này làm giá trị đầu vào cho hàm được gọi
    
    return {
        "n_tasks": n_tasks,
        "n_machines": n_machines,
        "tasks": tasks,
        "setups": setup_time,
        "precedences": precedences,
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

# hàm khởi tạo precedence nha - thứ tự ưu tiên các công việc
def generate_precedence_constraints(n_tasks: int) -> Dict[int,Any]: # ae mình thống nhất Dict nên ở đây t trả về 1 dict với id của tast và các danh sách task thực hiện sau nó
    precedence: Dict[int, Any] = {}
    max_relations = int ((n_tasks *(n_tasks -1))/2) # công thức tính số ràng buộc tối đa có thể có tương ứng với n_task ha
    num_relations = random.randint(1,max_relations //3) # do hồi bữa phúc dương kêu là nếu cho random tới max relation luôn thì nhiều quá nên t giảm bớt v, lấy tối đa của nó là 1/3 ha

    for new_relations in range(num_relations):
        a, b = random.sample(range(n_tasks), 2)
        if a > b:
            a, b = b, a  # kiểu t muốn là chiều xét của nó là 1 chiều thôi í
        
        if a not in precedence:
            precedence[a] = []  

        if b not in precedence[a]:
            if b in precedence and a in precedence[b]: 
                continue # checkvar nhẹ lỡ có a trước b rồi mà còn b trước a nữa thì cho cút
            precedence[a] = precedence [a] + [b]       

    return precedence        


        
if __name__ == "__main__":
    generate_environment()
