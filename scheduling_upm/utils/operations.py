import random
from typing import List, Dict, Any


def random_move(
    schedule: Dict[int, List[Any]], n_moves: int = 1
) -> Dict[int, List[Any]]:
    """Early stage. Move a task from one machine to another"""
    for _ in range(n_moves):
        machine_a, machine_b = random.sample(list(schedule.keys()), k=2)

        if len(schedule[machine_a]) < 2:
            continue

        job_idx = random.randrange(len(schedule[machine_a]))
        task = schedule[machine_a].pop(job_idx)

        pos = random.randrange(len(schedule[machine_b]) + 1)
        schedule[machine_b].insert(pos, task)

    return schedule


def inter_machine_swap(schedule: Dict[int, List[int]], n_swaps: int = 1):
    """
    Early-Mid stage. Swap tasks between different machines:
    """
    for _ in range(n_swaps):
        machine_a, machine_b = random.sample(list(schedule.keys()), k=2)

        if len(schedule[machine_a]) < 1 or len(schedule[machine_b]) < 1:
            continue

        task_a = random.randrange(len(schedule[machine_a]))
        task_b = random.randrange(len(schedule[machine_b]))

        schedule[machine_a][task_a], schedule[machine_b][task_b] = (
            schedule[machine_b][task_b],
            schedule[machine_a][task_a],
        )

    return schedule


def generate_schedule(
    tasks: Dict[int, Any], n_machines: int = 4
) -> Dict[int, List[int]]:
    """Initial / Early stage. Generate a whole new schedule"""
    schedule: Dict[int, List[int]] = {machine: [] for machine in range(n_machines)}
    shuffled_tasks = list(tasks.keys())
    random.shuffle(shuffled_tasks)

    for idx, task in enumerate(shuffled_tasks):
        schedule[idx % n_machines].append(task)

    return schedule


def shuffle_machine(
    schedule: Dict[int, List[Any]], n_machines: int = 1
) -> Dict[int, List[Any]]:
    """Early / Late stage. Shuffle task order on random machine."""
    machines = random.sample(list(schedule.keys()), n_machines)
    for machine in machines:
        if len(schedule[machine]) > 0:
            random.shuffle(schedule[machine])

    return schedule


def intra_machine_swap(schedule: Dict[int, List[Any]]) -> Dict[int, List[Any]]:
    """All stage. Swap two tasks within the same machine"""
    machine = random.choice(list(schedule.keys()))
    if len(schedule[machine]) > 1:
        task_a, task_b = random.sample(range(len(schedule[machine])), 2)
        schedule[machine][task_a], schedule[machine][task_b] = (
            schedule[machine][task_a],
            schedule[machine][task_b],
        )

    return schedule


def critical_task_move(schedule: Dict[int, List[int]], tasks: Dict[int, Any]):
    """Mid-Late stage. Move a longest-processing task from one machine to another"""
    machine_a, machine_b = random.sample(list(schedule.keys()), 2)
    if len(schedule[machine_a]) < 1:
        return schedule

    longest_task_idx: int = max(
        range(len(schedule[machine_a])),
        key=lambda task_idx: tasks[schedule[machine_a][task_idx]]["process_times"][
            machine_a
        ],
    )
    task = schedule[machine_a].pop(longest_task_idx)
    # insert near best position
    insert_position: int = random.randrange(len(schedule[machine_b]) + 1)
    schedule[machine_b].insert(insert_position, task)

    return schedule


def lookahead_insertion(
    schedule: Dict[int, List[int]], obj_function: callable, attempts: int = 10, **kwargs
):
    """Late stage. Attempt to find the best position to insert a task in"""
    new_schedule = {machine: sequence for machine, sequence in schedule.items()}
    current_cost: float = obj_function(schedule=new_schedule, **kwargs)

    for _ in range(attempts):
        # Randomly move task
        candidate = random_move(schedule=new_schedule)
        candidate_cost: float = obj_function(schedule=candidate, **kwargs)

        if candidate_cost < current_cost:
            return candidate

    return new_schedule

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

