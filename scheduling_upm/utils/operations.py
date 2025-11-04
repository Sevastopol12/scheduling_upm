import random
import copy
from typing import List, Tuple, Dict, Any


def swap_task(schedule) -> Dict[int, List[int]]:
    """Adjustment in schedule, aims to minimize makespan"""

    new_schedule = copy.deepcopy(schedule)
    machines: List[int] = list(new_schedule.keys())
    probability: float = random.random()

    # Swap task between 2 machines
    if probability < 0.4:
        machine_a, machine_b = random.sample(machines, k=2)
        if new_schedule[machine_a] and new_schedule[machine_b]:
            task_a = random.randrange(len(new_schedule[machine_a]))
            task_b = random.randrange(len(new_schedule[machine_b]))

            new_schedule[machine_a][task_a], new_schedule[machine_b][task_b] = (
                new_schedule[machine_b][task_b],
                new_schedule[machine_a][task_a],
            )

    # Move a task from 1 machine to another
    elif probability < 0.8:
        machine_a, machine_b = random.sample(machines, k=2)
        if new_schedule[machine_a]:
            job_idx = random.randrange(len(new_schedule[machine_a]))
            task = new_schedule[machine_a].pop(job_idx)

            pos = random.randrange(len(new_schedule[machine_b]) + 1)
            new_schedule[machine_b].insert(pos, task)
    # Swap 2 tasks on same machine
    else:
        machine = random.choice(machines)
        if len(new_schedule[machine]) > 1:
            task_a, task_b = random.sample(range(len(new_schedule[machine])), 2)
            new_schedule[machine][task_a], new_schedule[machine][task_b] = (
                new_schedule[machine][task_a],
                new_schedule[machine][task_b],
            )
    return new_schedule


def initial_schedule(
    tasks: Dict[int, Any], n_machines: int = 4
) -> Dict[int, List[int]]:
    """Perform Round-robin scheduling method to initialize schedule"""
    schedule: Dict[int, List[int]] = {machine: [] for machine in range(n_machines)}

    for task in tasks.keys():
        schedule[task % n_machines].append(task)
    return schedule


def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    total_resource: int, #thêm total_resource
) -> Tuple:
    """Objective: Minimize makespan"""

    # Compute milestones of task's completion time . Accouns for setups
    task_completion_milestones = compute_base_milestones(
        schedule=schedule, tasks=tasks, setups=setups
    )

    # TODO
    # Áp dụng ràng buộc precedences để tính thời gian hoàn thành thực tế của từng task

    # TODO
    # Áp dụng ràng buộc resource để tính thời gian hoàn thành thực tế của từng task
    
    applied_schedule = apply_resource_constraint(schedule, tasks, setups, total_resource) #áp dụng ràng buộc resource và tính lại makespan
    makespan = 0
    for m in applied_schedule.keys():
        if applied_schedule[m]:
            last_end = applied_schedule[m][-1]["end"]
            makespan = max(makespan, last_end)
    return makespan
    # Áp dụng ràng buộc resource thực tế
  
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

def apply_resource_constraint(schedule: Dict[int, List[int]], 
                              tasks: Dict[int, Any],
                              setups: Dict[Tuple[int, int], int],
                              total_resource: int) -> Dict[int, List[Dict[str, Any]]]:

    pool_resource = total_resource #pool resource là tài nguyên còn lại trong pool mà ban đầu là tổng resource
    running_tasks: List[Dict[str, Any]] = [] # danh sách các task đang chạy có 
    current_time: Dict[int, int] = {m: 0 for m in schedule.keys()} #Thời gian hiện tại của từng máy
    final_schedule: Dict[int, List[Dict[str, Any]]] = {m: [] for m in schedule.keys()} #Lịch trình cuối cùng sau khi áp dụng ràng buộc tài nguyên

    for m in schedule.keys(): # duyệt qua từng máy
        for idx, task_id in enumerate(schedule[m]): # duyệt qua từng task trên máy m
            needed_resource = tasks[task_id]["resource"] #lấy resource cần thiết để thực hiện task
            proc_time = tasks[task_id]["process_times"][m] #lấy thời gian xử lý của task trên máy m
            setup_time = 0 if idx == 0 else setups[(schedule[m][idx - 1], task_id)] #

            # Đợi đến khi có đủ resource trong pool
            while needed_resource > pool_resource:
                # tìm task kết thúc sớm nhất
                min_end = min([r["end"] for r in running_tasks]) #task vừa hoàn thành
                finished = [r for r in running_tasks if r["end"] == min_end]  
                for f in finished:
                    pool_resource += f["resource"] #trả resource về pool
                    running_tasks.remove(f) #xóa khỏi running tasks
                current_time[m] = max(current_time[m], min_end) #cập nhật thời gian hiện tại của máy m

            # Khi có đủ resource -> lấy resource từ pool
            pool_resource -= needed_resource
            start_time = current_time[m] #task sẽ bắt đầu ở thời gian hiện tại của máy m
            end_time = start_time + proc_time + setup_time

            task_info = {
                "task_id": task_id,
                "machine": m,
                "start": start_time,
                "end": end_time,
                "resource": needed_resource
            }#ghi lại task
            
            running_tasks.append(task_info) #để ghi các task chiếm resource và giải phóng khi current time = end time
            current_time[m] = end_time
            final_schedule[m].append(task_info)

    return final_schedule


