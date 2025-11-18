import copy
import numpy as np
from typing import List, Tuple, Dict, Any

def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
    alpha_precedence: float = 10**6, # Hard constraint
    alpha_load: float = 100.0,  # Soft constraint
    alpha_energy: float = 1.0,  # Energy Exceed (Medium)
    verbose: bool = False,  # Detail để tune
) -> Tuple:
    """Objective: Minimize makespan + penalty
    Guide Tune Alpha:
    1. Chạy random schedules để lấy typical makespan, std_dev
    2. Chọn alpha sao cho penalty = 1-10x typical makespan nếu vi phạm medium
        - Hard constraint (precedence): alpha cao (10^6+) để cấm vi phạm.
        - Medium (energy): alpha trung bình (100 - 1000) để phạt exceed nhưng chấp nhận nếu cần.
        - Soft (load balacing): alpha thấp (10 - 100) để khuyến khích balancing mà không bị dominate makespan.
    3. Gird search: giả sử alpha_load = [1000, 2000, 5000, 7000], đo makespan cuối & std_dev cuối.
    4. Adaptive: Nếu std_dev cuối > threshold (e.g. 500), tăng alpha_load x2 và rerun

    --> Logging chi tiết để debug & tune các tham số để thử nghiệm
    if verbose:
        print(f"Makespan: {makespan}")
        print(f"Precedence Penalty (raw): {precedence_penalty} -> Weighted: {alpha_precedence * precedence_penalty}")
        print(f"Load Std Dev (raw): {std_dev} -> Weighted Penalty: {alpha_load * std_dev}")
        print(f"Energy Penalty (raw): {energy_penalty} -> Weighted: {alpha_energy * energy_penalty}")
        print(f"Total Cost: {cost}")

    Giải thích nghĩa
    1. Tune dùng để thí nghiệm & điều chỉnh các tham số để cải thiện performance. Trong trường hợp này, nó sẽ thử nghiệm & chọn best value cho alphas
    --> Đảm bảo các penalties được cân bằng đúng
    2. Verbose là 1 parameter trong code để logging chi tiết trong quá trình chạy để xem bên trong lúc debug xảy ra những gì
    --> Giúp điều chỉnh các thông số để dubug
    """

    # Compute milestones of task's completion time . Accouns for setups
    task_completion_milestones = compute_base_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )

    precedences_penalty = 0
    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    if precedences:
        precedences_penalty, task_completion_milestones = precedence_constraint(
            schedule=schedule,
            task_completion_milestones=task_completion_milestones,
            setups=setups,
            precedences=precedences,
        )

    # TODO
    # Áp dụng ràng buộc resource để tính thời gian hoàn thành thực tế của từng task

    # Cal energy_penalty (ví dụ: sum(max(0, energy_at_t - cap) for t in time)
    energy_penalty = 0

    # Makespan
    makespan = max(task_completion_milestones.values())

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Thêm penalty cho load balacing
    std_dev = calculate_load_standard_deviation(schedule, len(schedule), tasks)

    # Cost
    cost = (
        makespan +
        alpha_precedence * precedences_penalty +
        alpha_load * std_dev +
        alpha_energy * energy_penalty
    )

    if precedences_penalty > 0:
        return alpha_precedence * precedences_penalty

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

def calculate_machine_loads(schedule, n_machines, tasks):
    """
    Tính tổng load (weighted duration) của mỗi machine

    schedule: dict {machine_id: [task_ids]}
    n_machines: số máy
    tasks: dict {task_id: {process_times, resource, weight}}

    Return list: tổng load của mỗi máy
    """
    machine_loads = [0.0] * n_machines

    for machine_id, task_list in schedule.items():
        for task_id in task_list:
            task = tasks[task_id]
            # Load = process_time * weight
            process_time = task["process_times"][machine_id]
            weight = task.get("weight", 1)
            machine_loads[machine_id] += process_time * weight
    return machine_loads
    
def calculate_load_standard_deviation(schedule, n_machines, tasks):
    """
    Tính std_dev của load các máy

    schedule: dict {machine_id: [task_ids]}
    n_machines: số máy
    dict tasks

    Return float: std_dev của load
    """
    loads = calculate_machine_loads(schedule, n_machines, tasks)
    return float(np.std(loads))