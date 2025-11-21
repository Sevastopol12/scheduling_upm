import copy
import time
import random
from typing import Dict, Any, Tuple, Set, List

from ..utils.evaluation import objective_function
from ..utils.entities import Schedule
from ..utils.operations import generate_schedule
from ..strategies.woa_strategy import (
    random_explore as woa_random_explore,
    discrete_spiral_update,
    discrete_shrinking_mechanism,
)
from ..strategies.sa_strategy import exploit as sa_exploit


# Mình sẽ dùng WOA để khám phá toàn cục, SA để khai thác cục bộ
class Hybrid:
    def __init__(
        self,
        tasks,
        setups,
        precedences,
        n_machines: int | None = None,
        n_schedules: int = 10,
        n_iterations: int = 100,
        sa_local_iters: int = 10,
        energy_constraint: dict | None = None,
        total_resource: int | None = None,
        explore_ratio: float = 0.5,
    ):
        self.tasks = tasks
        self.setups = setups
        self.n_machines = n_machines
        self.n_schedules = n_schedules
        self.n_iterations = n_iterations
        self.sa_local_iters = sa_local_iters
        self.precedences = precedences or None
        self.energy_constraint = energy_constraint or None
        self.total_resource = total_resource or None
        self.explore_ratio = explore_ratio

        self.best = None
        self.population: List[Schedule] = []
        self.history = []

    # Mình sẽ dùng WOA để khám phá toàn cục, SA để khai thác cục bộ
    # tạo dữ liệu ban đầu - điểm xuất phát
    def initialize_population(self):
        for _ in range(self.n_schedules):
            sched = generate_schedule(tasks=self.tasks, n_machines=self.n_machines)
            cost_dict = objective_function(
                schedule=sched,
                tasks=self.tasks,
                setups=self.setups,
                precedences=self.precedences,
                energy_constraint=self.energy_constraint,
                total_resource=self.total_resource,
            )

            milestones = cost_dict.pop("task_milestones")
            self.population.append(
                Schedule(schedule=sched, cost=cost_dict, milestones=milestones)
            )

        self.best = copy.deepcopy(
            min(self.population, key=lambda s: s.cost["total_cost"])
        )

    # xét a, lần lượt dùng woa để cập nhập và SA để tinh chỉnh
    def optimize(self) -> Dict[str, Any]:
        if len(self.tasks) < 1:
            return None, []

        self.initialize_population()

        for it in range(self.n_iterations):
            a = self.linearly_decrement(iter=it)

            for i, whale in enumerate(self.population):
                A = 2 * a * random.random() - a
                p = random.random()

                if p < self.explore_ratio:
                    if abs(A) <= 1:
                        n_moves = (
                            random.randint(1, max(1, int(a * 10)))
                            if a <= 0.3
                            else random.randint(1, 5)
                        )
                        candidate = discrete_shrinking_mechanism(
                            best_schedule=copy.deepcopy(self.best.schedule),
                            obj_function=objective_function,
                            tasks=self.tasks,
                            setups=self.setups,
                            precedences=self.precedences,
                            energy_constraint=self.energy_constraint,
                            total_resource=self.total_resource,
                            n_moves=n_moves,
                        )
                    else:
                        candidate = woa_random_explore(
                            schedule=copy.deepcopy(whale.schedule), tasks=self.tasks
                        )
                else:
                    candidate = discrete_spiral_update(
                        schedule=copy.deepcopy(whale.schedule),
                        best_schedule=copy.deepcopy(self.best.schedule),
                    )

                candidate_cost = objective_function(
                    schedule=copy.deepcopy(candidate),
                    tasks=self.tasks,
                    setups=self.setups,
                    precedences=self.precedences,
                    energy_constraint=self.energy_constraint,
                    total_resource=self.total_resource,
                )

                for _ in range(self.sa_local_iters):  # SA tinh chỉnh giúp WOA ở đây
                    temp_candidate = sa_exploit(
                        schedule=copy.deepcopy(candidate),
                        tasks=self.tasks,
                        obj_function=objective_function,
                        precedences=self.precedences,
                        setups=self.setups,
                        energy_constraint=self.energy_constraint,
                        total_resource=self.total_resource,
                    )

                    new_cost = objective_function(
                        schedule=temp_candidate,
                        tasks=self.tasks,
                        setups=self.setups,
                        precedences=self.precedences,
                        energy_constraint=self.energy_constraint,
                        total_resource=self.total_resource,
                        alpha_load=50.0,
                    )

                    if new_cost["total_cost"] < candidate_cost["total_cost"]:
                        candidate = copy.deepcopy(temp_candidate)
                        candidate_cost = new_cost
                        break

                milestones = candidate_cost.pop("task_milestones")
                # tiến hành cập nhật cá voi nếu tìm được ứng viên tốt hơn
                if candidate_cost["total_cost"] < whale.cost["total_cost"]:
                    whale.update(
                        new_schedule=copy.deepcopy(candidate),
                        new_cost=candidate_cost,
                        new_milestones=milestones,
                    )

                if whale.cost["total_cost"] < self.best.cost["total_cost"]:
                    self.best = copy.deepcopy(whale)

                self.history.append(
                    {
                        "iteration": iter,
                        "iter_cost": [agent.cost for agent in self.population],
                        "iter_schedule": self.population,
                        "best_schedule": self.best.schedule,
                        "best_cost": self.best.cost,
                    }
                )
                print(self.best.cost)

        return {
            "best_schedule": self.best.schedule,
            "best_cost": self.best.cost,
            "milestones": self.best.milestones,
            "history": self.history,
        }

    def linearly_decrement(self, iter: int):
        # khởi tạo giá trị quyết định tính khám phá
        return 2 - 2 * (iter / max(1, self.n_iterations))
