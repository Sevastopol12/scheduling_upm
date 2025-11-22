from typing import Dict, List, Any


class Schedule:
    """Representation of the solution"""

    def __init__(
        self, schedule: Dict[int, List[int]], cost: float, milestones: Dict[int, Any]
    ):
        self.schedule = schedule
        self.milestones = milestones
        self.cost = cost

    def update(
        self,
        new_schedule: Dict[int, List[int]],
        new_cost: float,
        new_milestones: Dict[int, Any],
    ):
        """Updates whale's schedule and cost"""
        self.schedule = new_schedule
        self.cost = new_cost
        self.milestones = new_milestones
