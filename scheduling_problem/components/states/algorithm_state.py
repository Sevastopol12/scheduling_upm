import reflex as rx
import asyncio
from typing import Optional, Any

from ...scheduling_upm.utils.environment import generate_environment
from ...scheduling_upm.algorithms.simulated_annealing import SimulatedAnnealing
from ...scheduling_upm.algorithms.whales_optim import WhaleOptimizationAlgorithm
from ...scheduling_upm.algorithms.hybrid_woa_sa import Hybrid
from ...components.chart.time_chart import plot_schedule_to_base64


class State(rx.State):
    # Problem
    n_machines: int = 0
    n_iterations: int = 0
    tasks: dict[int, Any] = {}
    custom_tasks: dict[int, Any] = {}
    setups: dict[int, dict[int, int]] = {}
    precedences: Optional[dict[int, list[int]]] = None
    custom_precedence: dict[int, list[int]] = {}
    energy_constraint: Optional[dict[str, Any]] = None
    custom_energy: dict[int, Any] = {}
    total_resource: Optional[int] = None
    sa_explore_ratio: float = 0.0
    whales_explore_ratio: float = 0.0
    hybrid_explore_ratio: float = 0.0

    # Parameter
    alpha_load: float = 0.1
    alpha_energy: float = 0.1

    # solution
    sa_schedule: dict[int, list[int]] = {}
    sa_history: list[dict[int, Any]] = []
    sa_cost: dict[str, Any] = {}
    sa_milestones: dict[int, dict[str, Any]] = {}

    whales_schedule: dict[int, list[int]] = {}
    whales_history: list[dict[int, Any]] = []
    whales_cost: dict[str, Any] = {}
    whales_milestones: dict[int, dict[str, Any]] = {}

    hybrid_schedule: dict[int, list[int]] = {}
    hybrid_history: list[dict[int, Any]] = []
    hybrid_cost: dict[str, Any] = {}
    hybrid_milestones: dict[int, dict[str, Any]] = {}

    @rx.var
    def get_task_length(self) -> int:
        return len(self.sa_schedule)

    @rx.event
    def remove_precedences(self):
        self.precedences = None

    @rx.event
    def remove_setups(self):
        self.setups = {}

    @rx.event
    def remove_tasks(self):
        self.tasks = {}
        self.custom_tasks = {}

    @rx.event
    def pop_task(self, value):
        value = int(value)
        if self.custom_tasks.get(value, None):
            self.custom_tasks = {
                task: props
                for task, props in self.custom_tasks.items()
                if task != value
            }
        if self.tasks.get(value, None):
            self.tasks = {
                task: props for task, props in self.tasks.items() if task != value
            }

    @rx.event
    def add_task(self, value):
        weight = float(value.get("weight", 0))
        resource = float(value.get("resource_usage", 0))

        energy = value.get("energy_usage", "")
        if len(energy) > 0:
            energy_usages = [int(usage) for usage in energy]
            energy_usages.extend([0 for _ in range(self.n_machines - len(energy))])
        else:
            energy_usages = [0 for _ in range(self.n_machines)]

        process_times = value.get("process_times", "")
        if len(process_times) > 0:
            time_on_machine = [int(time) for time in process_times]
            time_on_machine.extend(
                [0 for _ in range(self.n_machines - len(process_times))]
            )
        else:
            time_on_machine = [0 for _ in range(self.n_machines)]

        self.custom_tasks[len(self.custom_tasks)] = {
            "process_times": time_on_machine,
            "weight": weight,
            "resource": resource,
        }

        self.custom_energy[len(self.custom_tasks)] = energy_usages

    @rx.event
    def add_setup(self, value):
        self.tasks[len(self.tasks)] = value

    @rx.event
    def remove_energy(self):
        self.energy_constraint = None
        self.custom_energy = {}

    @rx.event
    def remove_resource(self):
        self.total_resource = None

    @rx.event
    def apply_settings(self, env_param: dict[str, Any]):
        environment = generate_environment(**env_param)

        self.n_machines = environment.pop("n_machines")
        generated_tasks = environment.pop("tasks")
        self.tasks = {**self.custom_tasks, **generated_tasks}
        self.setups = environment.pop("web_base_object", {})
        self.total_resource = environment.pop("total_resource", None)
        self.precedences = environment.pop("precedences", None)
        self.energy_constraint = environment.pop("energy_constraint", None)
        for pending_task, usages in self.custom_energy.items():
            self.energy_constraint["energy_usages"][pending_task] = usages

    @rx.event
    def apply_base_settings(self, params: dict[str, Any]):
        self.n_iterations = params.pop("n_iterations", 1000)
        self.sa_explore_ratio = params.pop("sa_explore_ratio", 0.5)
        self.whales_explore_ratio = params.pop("whales_explore_ratio", 0.7)
        self.hybrid_explore_ratio = params.pop("hybrid_explore_ratio", 0.5)
        self.alpha_load: float = 0.25
        self.alpha_energy: float = 0.25

    def convert_setups(
        self, web_base_object: dict[int, dict[int, int]]
    ) -> dict[tuple[int, int], int]:
        setups = {}
        for task_a, seq in web_base_object.items():
            for task_b, setup_time in seq.items():
                setups[(task_a, task_b)] = setup_time

        return setups

    @rx.event
    def set_load_energy_ratio(self, value: list[float]):
        self.alpha_load = value[0]
        self.alpha_energy = 0.5 - value[0]

    @rx.event(background=True)
    async def scheduling_result(self):
        if len(self.tasks) < 1:
            return

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
                        alpha_load=self.alpha_load,
                        alpha_energy=self.alpha_energy,
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
                        alpha_load=self.alpha_load,
                        alpha_energy=self.alpha_energy,
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
                        alpha_load=self.alpha_load,
                        alpha_energy=self.alpha_energy,
                    ).optimize
                ),
            ]
            (sa_solution, whales_solution, hybrid_solution) = await asyncio.gather(
                *tasks
            )

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
    def convert_task_object(self) -> dict[int, dict[str, Any]]:
        if len(self.tasks) and len(self.custom_tasks) < 1:
            return {}

        task_object = {}
        for task, props in self.custom_tasks.items():
            task_object[task] = props

        for task, props in self.tasks.items():
            task_object[task] = props

        return task_object

    @rx.var
    def convert_precedences_relations(self) -> dict[int, list[int]]:
        if self.precedences is None or len(self.precedences) < 1:
            return {}

        return {
            precedence: posteriors
            for precedence, posteriors in self.precedences.items()
        }

    @rx.var
    def convert_energy_consumption(self) -> dict[int, list[int]]:
        energies = {}
        if len(self.custom_energy) < 1:
            for task, energy in self.custom_energy.get("energy_usages", {}).items():
                energies[task] = energy

        if self.energy_constraint is not None:
            for task, energy in self.energy_constraint.get("energy_usages", {}).items():
                energies[task] = energy

        return energies

    @rx.var
    def convert_setups_for_display(self) -> dict[int, dict[int, int]]:
        if len(self.setups) < 1:
            return {}
        return self.setups
