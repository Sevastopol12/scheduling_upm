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
    
    pool_resource = total_resource #lượng resource hiện có = tổng resource
    running_tasks: List[Dict[str, Any]] = [] # Danh sách các task đang chạy sau khi cấp resource
    current_time = 0 # Thời gian hiện tại
    current_task_index = {m: 0 for m in schedule.keys()} # theo dõi task của mỗi máy
    final_schedule: Dict[int, List[Dict[str, Any]]] = {m: [] for m in schedule.keys()} #lịch trả về
    current_machine_time = {m: 0 for m in schedule.keys()} #thời gian rảnh
    
    total_tasks = sum(len(schedule[m]) for m in schedule) #đếm tổng số task 
    completed_tasks = 0 #dùng để dừng vòng lặp
    
    while completed_tasks < total_tasks: #lặp đến khi hoàn thành tất cả task
        finished_tasks = [t for t in running_tasks if t["end"] <= current_time] #tìm task đã hoàn thành (current time > end thì task đã xong)
        for t in finished_tasks:
            pool_resource += t["resource"]  #trả lại resource
            running_tasks.remove(t) #xóa task đã xong khỏi danh sách đang chạy
            completed_tasks += 1 # tăng task đã hoàn thành lên 1
            current_machine_time[t["machine"]] = t["end"] # cập nhật thời gian
        
        #tìm task tiếp theo trên máy có thể chạy
        ready_tasks = []
        for m in schedule.keys():
            idx = current_task_index[m] #lấy index task hiện tại trên máy m
            if idx >= len(schedule[m]):  #nếu hết task trên máy thì bỏ qua
                continue 
            
            #kiểm tra máy m có đang chạy task không
            if any(rt["machine"] == m for rt in running_tasks): #nếu đang chạy thì bỏ qua
                continue
            
            #kiểm tra máy có đang rảnh không
            if current_machine_time[m] > current_time:
                continue
            #lấy thông tin
            task_id = schedule[m][idx]
            needed_resource = tasks[task_id]["resource"]
            proc_time = tasks[task_id]["process_times"][m]
            #tính setup time chuyển đổi từ task trước đó sang task hiện tại
            setup_time = 0
            if idx > 0:
                prev_task = schedule[m][idx - 1]
                setup_time = setups.get((prev_task, task_id), 0)
            #thêm task vào danh sách task sẵn sàng
            ready_tasks.append({
                "machine": m,
                "task_id": task_id,
                "resource": needed_resource,
                "proc_time": proc_time,
                "setup_time": setup_time
            })
        
        scheduled_any = False #biến kiểm tra có task nào được lên lịch trong lần lặp này không
        for task in ready_tasks: #duyệt qua các task sẵn sàng
            if task["resource"] <= pool_resource: #nếu đủ resource để chạy task
                pool_resource -= task["resource"] #trừ resource của pool
                m = task["machine"] #lấy số máy
                 #tính thời gian bắt đầu và kết thúc
                
                task_start = max(current_machine_time[m], current_time) 
                setup_start = task_start 
                process_start = task_start + task["setup_time"] 
                task_end = process_start + task["proc_time"]

                final_schedule[task["task_id"]] = {
                    "machine": m,
                    "start": task_start,
                    "end": task_end,
                    "setup_start_time": setup_start,
                    "process_start_time": process_start,
                    "resource": task["resource"]
                }

                task_info = {  #chưa thông tin task sau khi schedule
                    "task_id": task["task_id"],
                    "machine": m,
                    "start": task_start,
                    "end": task_end,
                    "resource": task["resource"]
                }
                
                running_tasks.append(task_info) #thêm task vào danh sách đang chạy
                current_task_index[m] += 1 #cập nhật index task trên máy
                scheduled_any = True #đánh dấu có task được lên lịch
        
        
        if running_tasks: #nếu có task đang chạy
            current_time = min(t["end"] for t in running_tasks) #nhảy đến thời điểm task sớm nhất kết thúc
        elif not scheduled_any: #nếu không có task đang chạy và không có task nào được lên lịch
           
            next_times = [current_machine_time[m] for m in schedule.keys() #lấy danh sách thời gian rảnh cua các máy còn task chưa schedule
                         if current_task_index[m] < len(schedule[m])]  #
            if next_times: 
                current_time = min(next_times) #nhảy đến thời gian rảnh sớm nhất
            else: 
                break  #Không còn task nào thì đã hoàn thành hết task, thoát vòng lặp
    
    return final_schedule

