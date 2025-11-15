import copy
from typing import List, Tuple, Dict, Any
from collections import defaultdict


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
    energy_constraint: Dict[str, Any] = None,
    total_resource: int = None,
) -> Tuple:
    """Objective: Minimize makespan"""

    # Áp dụng ràng buộc resource
    task_completion_milestones = (
        apply_resource_constraint(
            schedule=schedule,
            tasks=tasks,
            setups=setups,
            total_resource=total_resource,
        )
        if total_resource is not None
        else compute_base_milestones(schedule=schedule, tasks=tasks, setups=setups)
    )

    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    precedence_penalty = 0
    if precedences is not None:
        precedence_penalty, task_completion_milestones = precedence_constraint(
            schedule=schedule,
            task_completion_milestones=task_completion_milestones,
            setups=setups,
            precedences=precedences,
        )

    # Energy consumption constraint
    energy_exceeds_penalty = 0
    if energy_constraint is not None:
        energy_exceeds_penalty = energy_consumption_over_time(
            task_milestones=task_completion_milestones,
            energy_constraint=energy_constraint,
        )

    # Makespan
    makespan = compute_makespan(task_milestones=task_completion_milestones)

    # Cost
    cost = makespan + precedence_penalty + energy_exceeds_penalty
    return cost


def compute_makespan(task_milestones: Dict[int, int]) -> Tuple[int, int]:
    makespan = max(task["complete_time"] for task in task_milestones.values())
    return makespan


def compute_base_milestones(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
):
    """Calculate base milestone, without constraint"""
    # Lưu trữ thời gian hoàn thành của mỗi task
    task_milestones: Dict[int, int] = {}

    # Lưu trữ các mốc thời gian hoàn thành mỗi task của máy
    # E.g: { machine: [task_1_complete_time, task_2_complete_time,.etc],.etc }

    machine_milestones: Dict[int, List[int]] = {
        machine: 0 for machine in schedule.keys()
    }

    for machine, sequence in schedule.items():
        for idx in range(len(sequence)):
            # task's process time
            task = sequence[idx]
            process_time = tasks[task]["process_times"][machine]
            setup_time = 0 if idx < 1 else setups[sequence[idx - 1], sequence[idx]]

            # Start time
            current_runtime: int = 0 if idx < 1 else machine_milestones[machine]

            # Update new complete time
            machine_milestones[machine] += process_time + setup_time

            # Store task info
            task_milestones[task] = {
                "start_setup": current_runtime,
                "start_process": current_runtime + setup_time,
                "complete_time": machine_milestones[machine],
                "machine": machine,
                "idx_on_machine": idx,
            }

    del machine_milestones
    return task_milestones


def precedence_constraint(
    schedule: Dict[int, List[int]],
    task_completion_milestones: Dict[int, int],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
):
    """Overwrites current milestones with respect to precedences"""
    # Đầu tiên t sẽ check các máy đang làm những task nào, là cơ sở cho pre vs post để check ràng buộc
    # t cũng tạo 1 bản chép, và bản chép này là để t ghi lại thời gian thực tế nó làm, nhưng vẫn có bản cũ giữ lại thời gian làm
    # ví dụ task 1 2s, task 2 3s, thì sau khi xong t vẫn có dữ liệu là task 1 2s, task 2 3s và dữ liệu làm thực tế là task 1 2s task 2 5s.
    task_to_machine = {task: m for m, seq in schedule.items() for task in seq}
    actual_completion_times = copy.deepcopy(task_completion_milestones)

    # sửa giá trị pen nếu vi phạm
    PENALTY_BASE = int(1e3)
    penalty = 0

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

                if (
                    idx_pre > idx_post
                ):  # chỉnh lại cách tính pen linh hoạt chứ k cố định
                    DISTANCE = abs(idx_pre - idx_post)
                    penalty += PENALTY_BASE * DISTANCE

            else:
                finish_pre = actual_completion_times[pre]["complete_time"]

                seq_post = schedule[machine_post]
                idx_post = seq_post.index(post)

                if idx_post == 0:
                    start_post = 0

                else:
                    prev_task = seq_post[idx_post - 1]
                    setup_time = setups.get((prev_task, post), 0)
                    start_post = (
                        actual_completion_times[prev_task]["complete_time"] + setup_time
                    )

                if start_post < finish_pre:
                    delay = finish_pre - start_post
                    for k in range(idx_post, len(seq_post)):
                        cur_task = seq_post[k]
                        actual_completion_times[cur_task]["start_setup"] += delay
                        actual_completion_times[cur_task]["start_process"] += delay
                        actual_completion_times[cur_task]["complete_time"] += delay

    return penalty, actual_completion_times


def energy_consumption_over_time(
    task_milestones: Dict[int, Dict[str, Any]],
    energy_constraint: Dict[str, Any],
) -> int:
    """Calculate total penalty per energy exceeded in accounts of all machine during processing"""

    energy_cap: int = energy_constraint["energy_cap"]
    energy_usages: Dict[int, List[int]] = energy_constraint["energy_usages"]

    # Events log of  time: consume energy / release
    events_log: Dict[int, int] = defaultdict(int)

    # Populate events lists
    for task, properties in task_milestones.items():
        # Get task's energy usage
        machine: int = properties["machine"]
        usage: int = energy_usages[task][machine]

        # Add events
        events_log[properties["start_setup"]] += usage
        events_log[properties["complete_time"]] -= usage

    exceeds_penalty: int = total_penalty_on_violation(
        events_log=events_log, energy_cap=energy_cap
    )

    return exceeds_penalty


def total_penalty_on_violation(events_log: Dict[int, int], energy_cap: int) -> int:
    """Penalize exceeded usages"""
    # List of events start time
    sorted_event_start_times: list[int] = sorted(events_log.keys())
    current_usages: int = 0
    exceeds_penalty: int = 0

    for idx in range(len(sorted_event_start_times)):
        start_time: int = sorted_event_start_times[idx]
        end_time: int = (
            sorted_event_start_times[idx + 1]
            if idx + 1 < len(sorted_event_start_times)
            else start_time
        )
        current_usages += events_log[start_time]

        # Penalize per unit exceeds * duration
        if current_usages > energy_cap:
            duration: int = end_time - start_time
            penalty_per_unit_time: int = current_usages - energy_cap
            exceeds_penalty += penalty_per_unit_time * duration

    return exceeds_penalty


def apply_resource_constraint(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    total_resource: int,
) -> Dict[int, Dict[str, Any]]:
    """Calculate True completion time with respect to resource distribution. Generate milestones on executtion"""

    pool_resource = total_resource  # lượng resource hiện có = tổng resource
    # Danh sách các task đang chạy sau khi cấp resource
    running_tasks: List[Dict[str, Any]] = []
    current_time = 0  # Thời gian hiện tại
    # theo dõi task của mỗi máy
    current_task_index = {m: 0 for m in schedule.keys()}
    # lịch trả về
    final_schedule: Dict[int, List[Dict[str, Any]]] = {m: [] for m in schedule.keys()}
    current_machine_time = {m: 0 for m in schedule.keys()}  # thời gian rảnh

    total_tasks = sum(len(schedule[m]) for m in schedule)  # đếm tổng số task
    completed_tasks = 0  # dùng để dừng vòng lặp

    # lặp đến khi hoàn thành tất cả task
    while completed_tasks < total_tasks:
        # tìm task đã hoàn thành (current time > end thì task đã xong)
        finished_tasks = [t for t in running_tasks if t["end"] <= current_time]
        for t in finished_tasks:
            pool_resource += t["resource"]  # trả lại resource
            running_tasks.remove(t)  # xóa task đã xong khỏi danh sách đang chạy
            completed_tasks += 1  # tăng task đã hoàn thành lên 1
            current_machine_time[t["machine"]] = t["end"]  # cập nhật thời gian

        # tìm task tiếp theo trên máy có thể chạy
        ready_tasks = []
        for m in schedule.keys():
            idx = current_task_index[m]  # lấy index task hiện tại trên máy m
            if idx >= len(schedule[m]):  # nếu hết task trên máy thì bỏ qua
                continue

            # kiểm tra máy m có đang chạy task không
            if any(rt["machine"] == m for rt in running_tasks):
                # nếu đang chạy thì bỏ qua
                continue

            # kiểm tra máy có đang rảnh không
            if current_machine_time[m] > current_time:
                continue

            # lấy thông tin
            task_id = schedule[m][idx]
            needed_resource = tasks[task_id]["resource"]
            proc_time = tasks[task_id]["process_times"][m]

            # tính setup time chuyển đổi từ task trước đó sang task hiện tại
            setup_time = 0
            if idx > 0:
                prev_task = schedule[m][idx - 1]
                setup_time = setups.get((prev_task, task_id), 0)
            # thêm task vào danh sách task sẵn sàng
            ready_tasks.append(
                {
                    "machine": m,
                    "task_id": task_id,
                    "resource": needed_resource,
                    "proc_time": proc_time,
                    "setup_time": setup_time,
                    "index": idx,
                }
            )
        # biến kiểm tra có task nào được lên lịch trong lần lặp này không
        scheduled_any = False
        for task in ready_tasks:  # duyệt qua các task sẵn sàng
            if task["resource"] <= pool_resource:  # nếu đủ resource để chạy task
                pool_resource -= task["resource"]  # trừ resource của pool
                m = task["machine"]  # lấy số máy
                # tính thời gian bắt đầu và kết thúc

                task_start = max(current_machine_time[m], current_time)
                setup_start = task_start
                process_start = task_start + task["setup_time"]
                task_end = process_start + task["proc_time"]

                final_schedule[task["task_id"]] = {
                    "start_setup": setup_start,
                    "start_process": process_start,
                    "complete_time": task_end,
                    "machine": m,
                    "index_on_machine": task["index"],
                }

                task_info = {  # chưa thông tin task sau khi schedule
                    "task_id": task["task_id"],
                    "machine": m,
                    "end": task_end,
                    "resource": task["resource"],
                }

                running_tasks.append(task_info)  # thêm task vào danh sách đang chạy
                current_task_index[m] += 1  # cập nhật index task trên máy
                scheduled_any = True  # đánh dấu có task được lên lịch

        # nếu có task đang chạy
        if running_tasks:
            # nhảy đến thời điểm task sớm nhất kết thúc
            current_time = min(t["end"] for t in running_tasks)
        # nếu không có task đang chạy và không có task nào được lên lịch
        elif not scheduled_any:
            next_times = [
                current_machine_time[m]
                for m in schedule.keys()  # lấy danh sách thời gian rảnh cua các máy còn task chưa schedule
                if current_task_index[m] < len(schedule[m])
            ]
            if next_times:
                current_time = min(next_times)  # nhảy đến thời gian rảnh sớm nhất
            else:
                break  # Không còn task nào thì đã hoàn thành hết task, thoát vòng lặp

    return final_schedule
