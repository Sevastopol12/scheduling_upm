import math
import random
import copy
from typing import Dict, Any, Tuple, Set, List
from .strategies.sa_strategy import random_explore, exploit
from .utils.operations import generate_schedule
from .utils.evaluation import objective_function
from .utils.entities import Schedule


class SimulatedAnnealing:
    def __init__(
        self,
        n_machines: int,
        tasks: Dict[int, Any],
        setups: Dict[Tuple[int, int], int],
        precedences: Dict[int, Set] = None,
        energy_constraint: Dict[str, Any] = None,
        total_resource: Dict[str, Any] = None,
        n_iterations: int = 1000,
        initial_temp: float = 1000.0,
    ):
        self.tasks = tasks
        self.setups = setups
        self.n_machines = n_machines
        self.n_iterations = n_iterations
        self.precedences = precedences or None
        self.energy_constraint = energy_constraint or None
        self.total_resource = total_resource or None
        self.initial_temp = initial_temp
        self.best_schedule = None
        self.current_schedule = None
        self.history = []

    def initialize_schedule(self):
        schedule = generate_schedule(tasks=self.tasks, n_machines=self.n_machines)
        cost = objective_function(
            schedule=schedule,
            tasks=self.tasks,
            setups=self.setups,
            precedences=self.precedences,
            total_resource=self.total_resource,
        )

        self.current_schedule = Schedule(schedule=schedule, cost=cost)
        self.best_schedule = Schedule(schedule=schedule, cost=cost)
        self.history.append(
            {
                "iteration": 0,
                "iter_cost": self.current_schedule.cost,
                "iter_schedule": copy.deepcopy(self.current_schedule.schedule),
                "best_schedule": copy.deepcopy(self.best_schedule.schedule),
                "best_cost": self.best_schedule.cost,
            }
        )

    def optimize(self) -> Tuple[Schedule, List[Dict]]:
        self.initialize_schedule()
        for iter in range(self.n_iterations):
            temperature: float = self.cooling_down(
                initial_temp=self.initial_temp, iteration=iter
            )

            # Generate new solution
            probability: float = random.random()
            # Keep track of iteration progess, affect adjusting behavior
            progress: float = iter / self.n_iterations

            # Explore
            if probability < 0.7 * (1 - progress):
                candidate_schedule = random_explore(
                    schedule=copy.deepcopy(self.current_schedule.schedule),
                    tasks=self.tasks,
                    n_ops=random.randint(1, 10),
                )

            # Exploit
            else:
                candidate_schedule = exploit(
                    schedule=copy.deepcopy(self.current_schedule.schedule),
                    tasks=self.tasks,
                    obj_function=objective_function,
                    precedences=self.precedences,
                    setups=self.setups,
                    energy_constraint=self.energy_constraint,
                    total_resource=self.total_resource,
                    n_ops=random.randint(1, 3),
                )

            candidate_cost = objective_function(
                schedule=candidate_schedule,
                tasks=self.tasks,
                setups=self.setups,
                precedences=self.precedences,
                energy_constraint=self.energy_constraint,
                total_resource=self.total_resource,
            )

            acp: float = self.acceptance_probability(
                old_cost=self.best_schedule.cost["total_cost"],
                new_cost=candidate_cost["total_cost"],
                temperature=temperature,
            )

            if random.random() < acp:
                self.current_schedule.update(
                    new_schedule=copy.deepcopy(candidate_schedule),
                    new_cost=copy.deepcopy(candidate_cost),
                )

            if candidate_cost["total_cost"] < self.best_schedule.cost["total_cost"]:
                self.best_schedule.update(
                    new_schedule=copy.deepcopy(candidate_schedule),
                    new_cost=copy.deepcopy(candidate_cost),
                )

            self.history.append(
                {
                    "iteration": iter +1,
                    "iter_cost": self.current_schedule.cost,
                    "iter_schedule": copy.deepcopy(self.current_schedule.schedule),
                    "best_schedule": copy.deepcopy(self.best_schedule.schedule),
                    "best_cost": self.best_schedule.cost,
                }
            )

            # early stop when temperature got too small
            if temperature < 1e-8:
                break

        return self.best_schedule, self.history

    def acceptance_probability(
        self, old_cost: float, new_cost: float, temperature: float
    ):
        if new_cost < old_cost:  # If better solution, accept it
            return 1.0
        # avoid division by zero
        if temperature <= 0:
            return 0.0
        # If worse, accept it with a possibility in attempt to escape local minima
        try:
            return math.exp(
                -(new_cost - old_cost) / temperature
            )  # probability of accepting
        except OverflowError:
            return 0.0

    def cooling_down(self, initial_temp: float, iteration: int, alpha: float = 0.995):
        """Exponential cooling"""
        return initial_temp * (alpha**iteration)
