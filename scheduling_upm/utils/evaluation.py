from typing import List, Tuple, Dict, Any, Set


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Set[int]] = None,
) -> int:
    """Objective: Minimize makespan"""
    # Compute milestones of task's completion time .Accounts for setups
    task_milestones = record_milestones(schedule=schedule, tasks=tasks, setups=setups)

    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    if precedences is not None:
        task_milestones, machine_total_delay = apply_precedences_constraint(
            schedule=schedule,
            task_milestones=task_milestones,
            precedences=precedences,
        )

    # TODO
    # Áp dụng ràng buộc resource để tính thời gian hoàn thành thực tế của từng task

    # Makespan
    makespan = compute_makespan(task_milestones=task_milestones)

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Cost
    cost = makespan
    return cost


def compute_makespan(task_milestones: Dict[int, int]) -> int:
    task_complete_time = [
        task_milestones[task]["complete_time"] for task in task_milestones.keys()
    ]
    return max(task_complete_time)


def record_milestones(
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


def apply_precedences_constraint(
    schedule: Dict[int, List[int]],
    task_milestones: Dict[int, int],
    precedences: Dict[int, Set[int]],
) -> Tuple[Dict[int, int], Dict[int, int]]:
    # Copy
    new_task_milestones = task_milestones

    # Storing machine total delay time as the result of taking precedences into accounts
    machine_delay_time = {}

    # Locate precedence violation and record
    for task, sequence in precedences.items():
        for precedence_task in sequence:
            task_start_process = new_task_milestones[task]["start_process"]
            precedence_complete_time = new_task_milestones[precedence_task][
                "complete_time"
            ]

            if precedence_complete_time > task_start_process:
                delay_time: int = precedence_complete_time - task_start_process

                # Get task position
                position: List[Tuple] = (
                    task_milestones[task]["process_machine"],
                    task_milestones[task]["idx"],
                )

                # Update the machine, position where the delay must be held
                current_delay = machine_delay_time.get(position, 0)
                machine_delay_time[position] = current_delay + delay_time

    # Update milestones ( add delay time )
    for position, delay_time in machine_delay_time.items():
        # Get machine & affected index
        machine, idx = position

        for task in schedule[machine][idx:]:
            task_milestones[task]["start_process"] += delay_time
            task_milestones[task]["complete_time"] += delay_time

    return new_task_milestones, machine_delay_time
