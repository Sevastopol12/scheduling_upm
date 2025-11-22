import random
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict


def generate_environment(
    custom_tasks={},
    n_tasks: int = 15,
    n_machines: int = 4,
    setup_relations: bool = True,
    load_balance: bool = True,
    n_precedences: Optional[int] = None,
    resources_cap: Optional[int] = None,
    resources_range: Optional[List[int]] = None,
    energy_cap: Optional[int] = None,
    energy_range: Optional[List[int]] = None,
    seed: Optional[int] = None,
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
    if seed is not None:  # keep task generation consistent
        random.seed(seed)

    total_resource = (
        (n_machines * 100 if resources_cap == -1 else resources_cap)
        if resources_cap is not None
        else None
    )

    # Generate tasks
    tasks: Dict[int, Any] = {}
    for t in range(len(custom_tasks), n_tasks):
        times: List[int] = process_time_on_each_machine(n_machines=n_machines)
        resource: int = (
            0
            if resources_cap is None
            else (
                random.randint(resources_range[0], resources_range[1])
                if resources_range is not None and resources_range[1] != -1
                else random.randint(0, int(resources_cap * 0.6))
            )
        )

        weight: int = random.randint(1, 10) if load_balance else 0
        tasks[t] = {"process_times": times, "resource": resource, "weight": weight}

    # Sequence-dependent setup times between tasks
    setup_time, web_base_object = generate_sequence_dependent_constraint(
        n_tasks=n_tasks, setup_relation=setup_relations
    )

    # phần setup_time tạo ở đây nên t cx tạo cái precedences ở đây luôn
    # tạo precedence mà ở đây lấy giá trị tham số n_task mà phúc dương đã tạo trong hàm này làm giá trị đầu vào cho hàm được gọi
    precedences = (
        generate_precedence_constraints(n_tasks=n_tasks, n_precedences=n_precedences)
        if n_precedences is not None
        else None
    )

    # Energy consumption
    energy_constraint = (
        generate_energy_constraint(
            n_machines=n_machines,
            n_tasks=n_tasks,
            custom_cap=energy_cap,
            custom_range=energy_range,
        )
        if energy_cap is not None
        else None
    )
    return {
        "n_tasks": n_tasks,
        "n_machines": n_machines,
        "tasks": tasks,
        "setups": setup_time,
        "precedences": precedences,
        "energy_constraint": energy_constraint,
        "total_resource": total_resource,
        "web_base_object": web_base_object,
    }


def process_time_on_each_machine(n_machines: int) -> List[int]:
    """Generate task's process time on each machine"""
    times: List[int] = []
    for _ in range(n_machines):
        # Performance coefficient
        modifier: float = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        base_process_time: int = random.randint(5, 30)
        times.append(max(1, int(base_process_time * modifier)))
    return times


def energy_usage_on_each_machine(
    n_machines: int, custom_cap: int, custom_range: Optional[List[int]] = None
) -> List[int]:
    """Generate task's energy usages on each machine"""
    usages_by_machine: List[int] = []
    for _ in range(n_machines):
        # Performance coefficient
        modifier: float = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        energy_usages: int = (
            random.randint(custom_range[0], custom_range[1])
            if custom_range is not None and custom_range[1] != -1
            else random.randint(0, custom_cap)
        )
        usages_by_machine.append(int(energy_usages * modifier))

    return usages_by_machine


def generate_sequence_dependent_constraint(
    n_tasks: int, setup_relation: bool
) -> Tuple[Dict[Tuple[int, int], int]]:
    """
    Khởi tạo mối quan hệ thứ tự của từng công việc.
    Tham số mẫu {
        (task_a, task_b): setup_time,
        (task_a, task_c): setup_time,
        ...
    }
    """

    web_base_object: Dict[int, Dict[int, int]] = {}
    setups = defaultdict(tuple)
    for task_a in range(n_tasks):
        if task_a not in web_base_object:
            web_base_object[task_a] = {}

        for task_b in range(n_tasks):
            setup_time = random.randint(0, 10) if setup_relation else 0

            web_base_object[task_a][task_b] = 0 if task_a == task_b else setup_time

            setups[(task_a, task_b)] = 0 if task_a == task_b else setup_time

    return setups, web_base_object


# hàm khởi tạo precedence nha - thứ tự ưu tiên các công việc
def generate_precedence_constraints(
    n_tasks: int, n_precedences: int = -1
) -> Dict[int, Any]:
    # ae mình thống nhất Dict nên ở đây t trả về 1 dict với id của tast và các danh sách task thực hiện sau nó
    precedence: Dict[int, Any] = {}
    # công thức tính số ràng buộc tối đa có thể có tương ứng với n_task ha
    max_relations = int((n_tasks * (n_tasks - 1)) / 2)
    # do hồi bữa phúc dương kêu là nếu cho random tới max relation luôn thì nhiều quá nên t giảm bớt v, lấy tối đa của nó là 1/3 ha
    num_relations = (
        n_precedences
        if n_precedences > 0
        else random.randint(0, int(max_relations * 0.2))
    )

    for new_relations in range(num_relations):
        a, b = random.sample(range(n_tasks), 2)
        if a > b:
            a, b = b, a  # kiểu t muốn là chiều xét của nó là 1 chiều thôi í

        if a not in precedence:
            precedence[a] = []

        if b not in precedence[a]:
            if b in precedence and a in precedence[b]:
                continue  # checkvar nhẹ lỡ có a trước b rồi mà còn b trước a nữa thì cho cút
            precedence[a] = precedence[a] + [b]

    return precedence


def generate_energy_constraint(
    n_machines: int = 2,
    n_tasks: int = 4,
    custom_cap: int = -1,
    custom_range: Optional[List[int]] = None,
) -> Dict[str, Any]:
    energy_cap: int = (
        custom_cap
        if custom_cap != -1
        else int(n_machines * 10 * random.choice([0.7, 0.8, 0.9, 1.0]))
    )

    energy_constraint: Dict[str, Any] = {
        "energy_cap": energy_cap,
        "energy_usages": defaultdict(int),
    }

    for task in range(n_tasks):
        energy_constraint["energy_usages"][task] = energy_usage_on_each_machine(
            n_machines=n_machines, custom_range=custom_range, custom_cap=energy_cap
        )

    return energy_constraint
