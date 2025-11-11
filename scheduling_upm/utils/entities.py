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
