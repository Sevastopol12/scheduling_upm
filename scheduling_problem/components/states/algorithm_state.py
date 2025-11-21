import reflex as rx
import asyncio
from typing import Optional, Any
from collections import defaultdict

from ...scheduling_upm.utils.environment import generate_environment
from ...scheduling_upm.algorithms.simulated_annealing import SimulatedAnnealing
from ...scheduling_upm.algorithms.whales_optim import WhaleOptimizationAlgorithm
from ...scheduling_upm.algorithms.hybrid_woa_sa import Hybrid
from ...components.chart.time_chart import plot_schedule_to_base64
from ...components.chart.cost_chart import swarm_chart_to_base64

class State(rx.State):
    # Problem
    n_machines: int = 4
    n_iterations: int = 0
    tasks: dict[int, Any] = {}
    setups: dict[int, dict[int, int]] = {}
    precedences: Optional[dict[int, list[int]]] = None
    energy_constraint: Optional[dict[str, Any]] = None
    total_resource: Optional[int] = None
    sa_explore_ratio: float = 0.0
    whales_explore_ratio: float = 0.0
    hybrid_explore_ratio: float = 0.0

    # solution
    sa_schedule: dict[int, list[int]] = {}
    sa_history: list[dict[int, Any]]
    sa_cost: dict[str, Any] = {}
    sa_milestones: dict[int, dict[str, Any]] = {}

    whales_schedule: dict[int, list[int]] = {}
    whales_history: list[dict[int, Any]]
    whales_cost: dict[str, Any] = {}
    whales_milestones: dict[int, dict[str, Any]] = {}

    hybrid_schedule: dict[int, list[int]] = {}
    hybrid_history: list[dict[int, Any]]
    hybrid_cost: dict[str, Any] = {}
    hybrid_milestones: dict[int, dict[str, Any]] = {}

    @rx.event
    def apply_settings(self, env_param: dict[str, Any]):
        environment = generate_environment(**env_param)

        self.n_machines = environment.pop("n_machines")
        self.tasks = environment.pop("tasks")
        self.setups = environment.pop("web_base_object", {})
        self.total_resource = environment.pop("total_resource", None)
        self.precedences = environment.pop("precedences", None)
        self.energy_constraint = environment.pop("energy_constraint", None)

    @rx.event
    def apply_base_settings(self, params: dict[str, Any]):
        self.n_iterations = params.pop("n_iterations", 1000)
        self.sa_explore_ratio = params.pop("sa_explore_ratio", 0.5)
        self.whales_explore_ratio = params.pop("whales_explore_ratio", 0.7)
        self.hybrid_explore_ratio = params.pop("hybrid_explore_ratio", 0.5)

    def convert_setups(
        self, web_base_object: dict[int, dict[int, int]]
    ) -> dict[tuple[int, int], int]:
        setups = {}
        for task_a, seq in web_base_object.items():
            for task_b, setup_time in seq.items():
                setups[(task_a, task_b)] = setup_time

        return setups

    @rx.event(background=True)
    async def scheduling_result(self) -> dict[str, Any]:
        async with self:
            tasks = [
                rx.run_in_thread(
                    SimulatedAnnealing(
                        n_machines=self.n_machines,
                        tasks=self.tasks,
                        setups=self.convert_setups(web_base_object=self.setups),
                        total_resource=self.total_resource,
                        precedences=self.precedences,
                        energy_constraint=self.energy_constraint,
                        n_iterations=self.n_iterations,
                        explore_ratio=self.sa_explore_ratio,
                    ).optimize
                ),
                rx.run_in_thread(
                    WhaleOptimizationAlgorithm(
                        n_machines=self.n_machines,
                        tasks=self.tasks,
                        setups=self.convert_setups(web_base_object=self.setups),
                        total_resource=self.total_resource,
                        precedences=self.precedences,
                        energy_constraint=self.energy_constraint,
                        n_iterations=self.n_iterations,
                        explore_ratio=self.whales_explore_ratio,
                    ).optimize
                ),
                rx.run_in_thread(
                    Hybrid(
                        n_machines=self.n_machines,
                        tasks=self.tasks,
                        setups=self.convert_setups(web_base_object=self.setups),
                        total_resource=self.total_resource,
                        precedences=self.precedences,
                        energy_constraint=self.energy_constraint,
                        n_iterations=self.n_iterations,
                        explore_ratio=self.hybrid_explore_ratio,
                    ).optimize
                )
            ]
            (sa_solution, whales_solution, hybrid_solution) = await asyncio.gather(*tasks)

            self.sa_cost = sa_solution["best_cost"]
            self.sa_history = sa_solution["history"]
            self.sa_milestones = sa_solution["milestones"]
            self.sa_schedule = sa_solution["best_schedule"]

            self.whales_cost = whales_solution["best_cost"]
            self.whales_history = whales_solution["history"]
            self.whales_milestones = whales_solution["milestones"]
            self.whales_schedule = whales_solution["best_schedule"]

            self.hybrid_cost = hybrid_solution["best_cost"]
            self.hybrid_history = hybrid_solution["history"]
            self.hybrid_milestones = hybrid_solution["milestones"]
            self.hybrid_schedule = hybrid_solution["best_schedule"]

    @rx.var
    def sa_plot(self) -> Optional[str]:
        return plot_schedule_to_base64(
            self.sa_milestones, title="Simulated Annealing Result"
        )

    @rx.var
    def whales_plot(self) -> Optional[str]:
        return plot_schedule_to_base64(self.whales_milestones, title="Whales Result")
    
    @rx.var
    def hybrid_plot(self) -> Optional[str]:
        return plot_schedule_to_base64(self.hybrid_milestones, title="Hybrid Result")

    @rx.var
    def sa_cost_plot(self) -> Optional[str]:
        return swarm_chart_to_base64(
            self.sa_hi
        )