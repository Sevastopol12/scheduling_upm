import copy
from typing import List, Tuple, Dict, Any
from collections import defaultdict


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
    energy_constraint: Dict[str, Any] = None,
) -> Tuple:
    """Objective: Minimize makespan"""

    # Compute milestones of task's completion time . Accouns for setups
    task_completion_milestones = compute_base_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )
    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    if precedences:
        penalty, task_completion_milestones = precedence_constraint(
            schedule=schedule,
            task_completion_milestones=task_completion_milestones,
            setups=setups,
            precedences=precedences,
        )
        if penalty > 0:
            return penalty

    # TODO
    # Áp dụng ràng buộc resource để tính thời gian hoàn thành thực tế của từng task

    # Energy consumption penalty
    energy_exceeds_penalty = 0
    if energy_constraint is not None:
        energy_exceeds_penalty = energy_consumption_over_time(
            task_milestones=task_completion_milestones,
            energy_constraint=energy_constraint,
        )

    # Makespan
    makespan = compute_makespan(task_milestones=task_completion_milestones)

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Cost
    cost = makespan + energy_exceeds_penalty
    return cost


def compute_makespan(task_milestones: Dict[int, int]) -> Tuple[int, int]:
    latest_task = sorted(
        task_milestones.values(), key=lambda task: task["complete_time"]
    )
    makespan = latest_task[-1]["complete_time"]
    return makespan


def compute_base_milestones(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
):
    # Lưu trữ mốc thời gian hoàn thành và tổng thời gian chạy, setup của mỗi task
    task_milestones: Dict[int, Dict[str, int]] = {}

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
                "process_machine": machine,
                "idx": idx,
            }

    del machine_milestones
    return task_milestones


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


def energy_consumption_over_time(
    task_milestones: Dict[int, Dict[str, Any]],
    energy_constraint: Dict[str, Any],
) -> int:
    energy_cap: int = energy_constraint["energy_cap"]
    energy_usages: Dict[int, List[int]] = energy_constraint["energy_usages"]

    # Events log of  time: consume energy / release
    events_log: Dict[int, int] = defaultdict(int)

    # Populate events lists
    for task, properties in task_milestones.items():
        # Get task's energy usages
        machine: int = properties["process_machine"]
        usage: int = energy_usages[task][machine]
        # Add events
        events_log[properties["start_setup"]] += usage
        events_log[properties["complete_time"]] -= usage

    # Process events to calculate total penalty on violation
    exceeds_penalty: int = total_penalty_on_violation(
        events_log=events_log, energy_cap=energy_cap
    )

    return exceeds_penalty


def total_penalty_on_violation(events_log: Dict[int, int], energy_cap: int) -> int:
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
