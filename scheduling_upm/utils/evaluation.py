
import copy
from typing import List, Tuple, Dict, Any

def objective_function(
    schedule: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int, int], int],
    precedences: Dict[int, Any] = None,
    total_resource: int = None,
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
        
    # Áp dụng ràng buộc resource 
    if total_resource is not None:
        resource_schedule = apply_resource_constraint(
            schedule=schedule,
            tasks=tasks,
            setups=setups,
            total_resource=total_resource
        )
        
        # Tính makespan từ resource schedule
        makespan = max(info["complete_time"] for info in resource_schedule.values())
    else:
        # Nếu không có resource constraint, dùng milestones thông thường
        makespan = max(task_completion_milestones.values())

    # Cost = makespan
    cost = makespan
    return cost
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

def apply_resource_constraint(schedule: Dict[int, List[int]], 
                              tasks: Dict[int, Any],
                              setups: Dict[Tuple[int, int], int],
                              total_resource: int) -> Dict[int, Dict[str, Any]]:
    
    
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
                "setup_time": setup_time,
                "index": idx
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
                    "start": task_start,
                    "start_setup": setup_start,
                    "start_process": process_start,
                    "complete_time": task_end,
                    "machine": m,
                    "index_on_machine": task["index"]
                }

                task_info = {  #chưa thông tin task sau khi schedule
                    "task_id": task["task_id"],
                    "machine": m,
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
