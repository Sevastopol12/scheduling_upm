import numpy as np
from typing import List, Tuple, Dict, Any, Set


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Set[int]] = None,
) -> Tuple:
    """Objective: Minimize makespan"""
    # Compute milestones of task's completion time .Accouns for setups
    task_milestones, machine_milestones = record_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )

    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    if precedences is not None:
        task_milestones, machine_milestones = apply_precedences_constraint(
            schedule=schedule,
            machine_milestones=machine_milestones,
            task_milestones=task_milestones,
            precedences=precedences,
        )

    # TODO
    # Áp dụng ràng buộc resource để tính thời gian hoàn thành thực tế của từng task

    # Makespan
    makespan = compute_makespan(machine_milestones=machine_milestones)

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Cost
    cost = makespan
    return cost


def compute_makespan(machine_milestones: Dict[int, np.array]) -> int:
    machine_completion_time: List[int] = [
        milestones.max() if milestones.size > 0 else 0
        for milestones in machine_milestones.values()
    ]

    return max(machine_completion_time)


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
        machine: [] for machine in schedule.keys()
    }

    for machine, sequence in schedule.items():
        for idx in range(len(sequence)):
            # task's process time
            task = sequence[idx]
            process_time = tasks[task]["process_times"][machine]
            setup_time = 0 if idx < 1 else setups[sequence[idx - 1], sequence[idx]]

            # Start time
            current_runtime: int = 0 if idx < 1 else machine_milestones[machine][-1]

            # Update new complete time
            machine_milestones[machine].append(
                current_runtime + process_time + setup_time
            )

            # Store task info
            task_milestones[task] = {
                "start_time": current_runtime,
                "complete_time": machine_milestones[machine][-1],
                "process_machine": machine,
                "idx": idx,
            }

    # Array transformation
    machine_milestones = {
        machine: np.array([sequence])
        for machine, sequence in machine_milestones.items()
    }
    return task_milestones, machine_milestones


def apply_precedences_constraint(
    schedule: Dict[int, List[int]],
    machine_milestones: Dict[int, np.array],
    task_milestones: Dict[int, int],
    precedences: Dict[int, Set[int]],
) -> Dict[int, int]:
    # Copy
    new_task_milestones = task_milestones
    new_machine_milestones = machine_milestones

    # Storing machine total delay time as the result of taking precedences into accounts
    machine_delay_time = {}

    # Locate precedence violation and record
    for task, sequence in precedences.items():
        for precedence_task in sequence:
            task_start_time = new_task_milestones[task]["start_time"]
            precedence_complete_time = new_task_milestones[precedence_task][
                "complete_time"
            ]

            if precedence_complete_time > task_start_time:
                delay_time: int = precedence_complete_time - task_start_time

                # Get task position
                affected_machine_position: List[Tuple] = (
                    task_milestones[task]["process_machine"],
                    task_milestones[task]["idx"],
                )

                # Update the machine, position where the delay must be held
                current_delay = machine_delay_time.get(affected_machine_position, 0)
                machine_delay_time[affected_machine_position] = (
                    current_delay + delay_time
                )

    # Update milestones ( add delay time )
    for position, delay_time in machine_delay_time.items():
        # Get machine & affected index
        machine, affected_idx = position
        new_machine_milestones[machine][affected_idx:] += delay_time

        for task in schedule[machine][affected_idx:]:
            task_milestones[task]["start_time"] += delay_time
            task_milestones[task]["complete_time"] += delay_time

    return new_task_milestones, new_machine_milestones
