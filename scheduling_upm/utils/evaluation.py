
import copy
from typing import List, Tuple, Dict, Any

def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
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

    # Makespan
    makespan = max(task_completion_milestones.values())

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Cost
    cost = makespan
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
