from typing import List, Tuple, Dict, Any, Set
from collections import defaultdict


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Set[int]] = None,
    resources: Dict[str, Any] = None,
) -> int:
    """Objective: Minimize makespan"""
    # Compute milestones of task's completion time .Accounts for setups
    task_milestones = record_milestones(schedule=schedule, tasks=tasks, setups=setups)

    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task
    if precedences is not None:
        task_milestones, deadlock_penalty = apply_precedences_constraint(
            schedule=schedule,
            task_milestones=task_milestones,
            precedences=precedences,
        )

    # Áp dụng ràng buộc resource để tính penalty
    if resources is not None:
        process_penalty, setup_penalty = resource_distribution_over_time(
            task_milestones=task_milestones, resources=resources
        )
    else:
        process_penalty = setup_penalty = 0

    # Makespan
    makespan = compute_makespan(task_milestones=task_milestones)

    # TODO
    # Xét thêm những khía cạnh khác, tính cost

    # Cost
    cost = makespan + deadlock_penalty + process_penalty + setup_penalty
    print(f"makespan: {makespan}")
    print(f"deadlock_penalty: {deadlock_penalty}")
    print(f"process_penalty: {process_penalty}")
    print(f"setup_penalty: {setup_penalty}")
    return cost


def compute_makespan(task_milestones: Dict[int, int]) -> Tuple[int, int]:
    latest_task = sorted(
        task_milestones.values(), key=lambda task: task["complete_time"]
    )
    makespan = latest_task[-1]["complete_time"]
    return makespan


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
    deadlock_penalty = 0

    # Locate precedence violation and record
    for task, sequence in precedences.items():
        for precedence_task in sequence:
            task_start_time = new_task_milestones[task]["start_process"]
            precedence_complete_time = new_task_milestones[precedence_task][
                "complete_time"
            ]

            if precedence_complete_time > task_start_time:
                # Infeasible solution
                if (
                    new_task_milestones[precedence_task]["process_machine"]
                    == new_task_milestones[task]["process_machine"]
                ):
                    deadlock_penalty += int(10e2) * (
                        precedence_complete_time - task_start_time
                    )

                delay_time: int = precedence_complete_time - task_start_time

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
            task_milestones[task]["start_setup"] += delay_time
            task_milestones[task]["start_process"] += delay_time
            task_milestones[task]["complete_time"] += delay_time

    del machine_delay_time
    return new_task_milestones, deadlock_penalty


def resource_distribution_over_time(
    task_milestones: Dict[int, Dict[str, Any]],
    resources: Dict[str, Any],
) -> Tuple[int, int]:
    process_cap: int = resources["max_process_resource"]
    setup_cap: int = resources["max_setup_resource"]
    task_resources: Dict[int, Dict[str, Any]] = resources["task_resources"]

    # Event log: time/usage
    process_events: Dict[int, int] = defaultdict(int)
    setup_events: Dict[int, int] = defaultdict(int)

    # Populate events lists
    for task, task_properties in task_milestones.items():
        # Get task's needed resource
        machine: int = task_properties["process_machine"]
        setup_usage: int = task_resources[task]["setup_usage"][machine]
        process_usage: int = task_resources[task]["process_usage"][machine]

        # Setup phase
        setup_events[task_properties["start_setup"]] += setup_usage
        setup_events[task_properties["start_process"]] -= setup_usage

        # Process phase
        process_events[task_properties["start_process"]] += process_usage
        process_events[task_properties["complete_time"]] -= process_usage

    # Process events to calculate total penalty on violation
    setup_exceeds_penalty = total_penalty_on_violation(
        events_log=setup_events, resource_cap=setup_cap
    )
    process_exceeds_penalty = total_penalty_on_violation(
        events_log=process_events, resource_cap=process_cap
    )

    return process_exceeds_penalty, setup_exceeds_penalty


def total_penalty_on_violation(events_log: Dict[int, int], resource_cap: int) -> int:
    # List of events start time
    sorted_event_start_times: list[int] = sorted(events_log.keys())
    current_usages: int = 0
    exceeds_penalty: int = 0

    for idx in range(1, len(sorted_event_start_times)):
        start_time: int = sorted_event_start_times[idx - 1]
        end_time: int = sorted_event_start_times[idx]

        # Penalize per unit exceeds * duration
        if current_usages > resource_cap:
            duration: int = end_time - start_time
            penalty_per_unit_time: int = current_usages - resource_cap
            exceeds_penalty += penalty_per_unit_time * duration

        current_usages += events_log[start_time]

    return exceeds_penalty
