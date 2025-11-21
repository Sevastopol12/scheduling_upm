import reflex as rx
import random

from .algorithm_state import State as AlgorithmState


class PageState(rx.State):
    n_machines: str = "2"
    n_tasks: str = "4"

    # precedences
    n_precedences: str = "-1"
    use_precedences: bool = True

    # setups
    use_setups: bool = True

    # resource
    resources_cap: str = "-1"
    resources_bound: list[str, str] = ["0", "0"]
    use_resources_cap: bool = True

    # energy
    energy_cap: str = "-1"
    energy_bound: list[str, str] = ["0", "0"]
    use_energy_cap: bool = True

    # Algorithm settings
    whales_agents: str = "10"
    hybrid_agents: str = "10"
    sa_explore_ratio: float = 0.7
    whales_explore_ratio: float = 0.5
    hybrid_explore_ratio: float = 0.5
    n_iterations: str = "10"
    seed: str = "2503"

    # Task & machine settings
    @rx.event
    def set_n_tasks(self, value: str):
        if value != "":
            self.n_tasks = value

    @rx.event
    def set_n_machines(self, value: str):
        if value != "":
            self.n_machines = value

    @rx.var
    def get_task_length(self) -> str:
        return self.n_tasks

    @rx.var
    def get_all_task(self) -> range:
        return range(1, int(self.n_tasks) + 1)

    # Precedences
    @rx.event
    def apply_precedences(self, value: bool):
        self.use_precedences = value

    @rx.event
    def set_n_precedences(self, value: str):
        if value != "":
            self.n_precedences = value

    # Setups
    @rx.event
    def apply_setups(self, value: bool):
        self.use_setups = value

    # Resources
    @rx.event
    def apply_resources_cap(self, value: bool):
        self.use_resources_cap = value

    @rx.event
    def set_resources_cap(self, value: str):
        if value != "":
            self.resources_cap = value

    @rx.event
    def set_resources_bound(self, idx: int, value: str):
        if value == "":
            value = "0"

        self.resources_bound[idx] = value

    # Energy
    @rx.event
    def apply_energy_cap(self, value: bool):
        self.use_energy_cap = value

    @rx.event
    def set_energy_bound(self, idx: int, value: str):
        if value == "":
            value = "0"

        self.energy_bound[idx] = value

    @rx.event
    def set_energy_cap(self, value: str):
        if value != "":
            self.energy_cap = value

    # Algorithms settings

    # Simulated Annealing
    @rx.event
    def set_sa_explore_ratio(self, value: list[float, int]):
        self.sa_explore_ratio = value[0]

    # Whales
    @rx.event
    def set_whales_explore_ratio(self, value: list[float, int]):
        self.whales_explore_ratio = value[0]

    @rx.event
    def set_whales_agents(self, value: str):
        self.whales_agents = value

    # Hybrid
    @rx.event
    def set_hybrid_explore_ratio(self, value: list[float, int]):
        self.hybrid_explore_ratio = value[0]

    @rx.event
    def set_hybrid_agents(self, value: str):
        self.hybrid_agents = value

    # Other
    @rx.event
    def set_n_iterations(self, value: str):
        self.n_iterations = value

    @rx.event
    def generate_seed(self):
        self.seed = str(random.randint(1, 10000))

    @rx.event
    def set_algorithm_to_default(self):
        self.n_iterations = "10"
        self.whales_agents = "10"
        self.hybrid_agents = "10"
        self.sa_explore_ratio = 0.7
        self.whales_explore_ratio = 0.5
        self.hybrid_explore_ratio = 0.5
        self.seed = "2503"

    @rx.event
    def set_to_default(self):
        self.n_tasks = "4"
        self.n_machines = "2"
        self.n_precedences = "-1"
        self.resources_cap = "-1"
        self.resources_bound = ["0", "-1"]
        self.energy_cap = "-1"
        self.energy_bound = ["0", "-1"]
        self.seed = "2503"

    @rx.event
    def randomize(self):
        self.n_tasks = str(random.randint(1, 100))
        self.n_machines = str(random.randint(1, 10))

        if self.use_precedences:
            max_relations = int(self.n_tasks) * (int(self.n_tasks) - 1) // 2
            self.n_precedences = str(
                random.randint(1, max(2, int(max_relations * 0.2)))
            )

        if self.use_resources_cap:
            cap = random.randint(100, int(self.n_machines) * 100 + 1)
            upper_bound = random.randrange(1, cap)
            lower_bound = random.randrange(0, upper_bound)

            self.resources_bound = [str(lower_bound), str(upper_bound)]
            self.resources_cap = str(cap)

        if self.use_energy_cap:
            cap = random.randint(10, int(self.n_machines) * 10 + 1)
            upper_bound = random.randrange(1, cap)
            lower_bound = random.randrange(0, upper_bound)

            self.energy_bound = [str(lower_bound), str(upper_bound)]
            self.energy_cap = str(cap)

    @rx.event(background=True)
    async def generate_environment(self):
        async with self:
            algorithm_state = await self.get_state(AlgorithmState)
            algorithm_state.apply_settings(
                env_param={
                    "n_machines": int(self.n_machines),
                    "n_tasks": int(self.n_tasks),
                    "setup_relations": self.use_setups,
                    "n_precedences": int(self.n_precedences)
                    if self.use_precedences
                    else None,
                    "resources_cap": int(self.resources_cap)
                    if self.use_resources_cap
                    else None,
                    "resources_range": [
                        int(self.resources_bound[0]),
                        int(self.resources_bound[1]),
                    ]
                    if self.use_resources_cap
                    else None,
                    "energy_cap": int(self.energy_cap) if self.use_energy_cap else None,
                    "energy_range": [
                        int(self.energy_bound[0]),
                        int(self.energy_bound[1]),
                    ]
                    if self.use_energy_cap
                    else None,
                    "seed": self.seed,
                }
            )

    @rx.event
    async def apply_algorithm(self):
        async with self:
            algorithm_state = await self.get_state(AlgorithmState)
            algorithm_state.apply_base_settings(
                params={
                    "n_iterations": int(self.n_iterations),
                    "sa_explore_ratio": self.sa_explore_ratio,
                    "whales_explore_ratio": self.whales_explore_ratio,
                    "hybrid_explore_ratio": self.hybrid_explore_ratio,
                }
            )