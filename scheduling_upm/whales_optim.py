import random
import copy
from typing import Dict, Any, List, Set
from .utils.operations import generate_schedule
from .strategies.woa_strategy import (
    random_explore,
    discrete_shrinking_mechanism,
    discrete_spiral_update,
)
from .utils.evaluation import objective_function
from .utils.entities import Schedule


class WhaleOptimizationAlgorithm:
    """
    Whale Optimization Algorithm
    """

    def __init__(
        self,
        tasks: Dict[int, Any],
        setups: Dict[tuple[int, int], int],
        n_machines: int,
        n_schedules: int = 10,
        n_iterations: int = 1000,
        precedences: Dict[int, Set] = None,
        total_resource: int = None,
        energy_constraint: Dict[str, Any] = None
    ):
        if n_machines <= 0 or n_schedules <= 0:
            raise ValueError()

        self.tasks = tasks
        self.setups = setups
        self.n_machines = n_machines
        self.n_schedules = n_schedules
        self.n_iterations = n_iterations
        self.precedences = precedences or None
        self.energy_constraint = energy_constraint or None
        self.total_resource = total_resource or None
        self.schedules: List[Schedule] = []
        self.best_schedule: Schedule = None
        self.history = []

    def initialize_population(self):
        """Initializes the pod of whales"""
        for _ in range(self.n_schedules):
            schedule = generate_schedule(tasks=self.tasks, n_machines=self.n_machines)
            cost = objective_function(
                schedule=schedule,
                tasks=self.tasks,
                setups=self.setups,
                precedences=self.precedences,
                energy_constraint=self.energy_constraint,
            )
            self.schedules.append(Schedule(schedule=schedule, cost=cost))

        self.best_schedule = copy.deepcopy(
            min(self.schedules, key=lambda schedule: schedule.cost["total_cost"])
        )

    def optimize(self):
        self.initialize_population()

        for iter in range(self.n_iterations):
            a = self.linearly_decrement(iter=iter)

            for agent_schedule in self.schedules:
                A = 2 * a * random.random() - a
                # C = 2 * random.random()
                possibility = random.random()

                if possibility < 0.5:
                    if abs(A) <= 1:
                        # Exploitation: Shrinking encircling mechanism
                        candidate_schedule = discrete_shrinking_mechanism(
                            best_schedule=self.best_schedule.schedule,
                            n_moves=random.randint(1, max(1, int(a * 10 + 1))),
                            **{
                                "precedences": self.precedences,
                                "energy_constraint": self.energy_constraint,
                                "total_resource": self.total_resource,
                                "setups": self.setups,
                                "obj_function": objective_function,
                                "tasks": self.tasks,
                            },
                        )
                    else:
                        # Exploration: Search for prey
                        candidate_schedule = random_explore(
                            tasks=self.tasks, schedule=agent_schedule.schedule
                        )
                else:
                    # Exploitation: Spiral updating
                    candidate_schedule = discrete_spiral_update(
                        schedule=agent_schedule.schedule,
                        best_schedule=self.best_schedule.schedule,
                    )

                candidate_cost = objective_function(
                    schedule=candidate_schedule,
                    tasks=self.tasks,
                    setups=self.setups,
                    precedences=self.precedences,
                    energy_constraint=self.energy_constraint,
                    total_resource=self.total_resource,
                )

                if candidate_cost["total_cost"] < agent_schedule.cost["total_cost"]:
                    agent_schedule.update(
                        new_schedule=copy.deepcopy(candidate_schedule),
                        new_cost=candidate_cost,
                    )

                if (
                    agent_schedule.cost["total_cost"]
                    < self.best_schedule.cost["total_cost"]
                ):
                    self.best_schedule.update(
                        new_schedule=copy.deepcopy(agent_schedule.schedule),
                        new_cost=agent_schedule.cost,
                    )
                self.history.append(
                    {
                        "iteration": iter,
                        # "iter_cost": self.current_schedule.cost,
                        "iter_schedule": self.schedules,
                        "best_schedule": self.best_schedule.schedule,
                        "best_cost": self.best_schedule.cost,
                    }
                )

            # early stop when a got too small
            if a < 1e-8:
                break

        return self.best_schedule, self.history

    def linearly_decrement(self, iter: int):
        return 2 - 2 * (iter / self.n_iterations)
