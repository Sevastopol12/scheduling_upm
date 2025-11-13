from typing import Dict, List

class Schedule:
    """Representation of the solution"""

    def __init__(self, schedule: Dict[int, List[int]], cost: float):
        self.schedule = schedule
        self.cost = cost

    def update(self, new_schedule: Dict[int, List[int]], new_cost: float):
        """Updates whale's schedule and cost"""
        self.schedule = new_schedule
        self.cost = new_cost

class Task:
    def __init__(self, task_id, process_times, resource, weight=1, task_type="normal"):
        self.task_id = task_id
        self.process_times = process_times  # list thời gian trên mỗi máy
        self.resource = resource
        self.weight = weight  # 1-10
        self.task_type = task_type  # "normal", "mid", "late", "exploit"
    
    def __repr__(self):
        return f"Task({self.task_id}, weight={self.weight}, type={self.task_type})"


class Machine:
    def __init__(self, machine_id):
        self.machine_id = machine_id
    
    def __repr__(self):
        return f"Machine({self.machine_id})"