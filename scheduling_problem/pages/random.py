import reflex as rx
from typing import Any, Optional

from ..components.landing.setup_environment import apply_button, selected_chips
from ..components.states.algorithm_state import State as AlgorithmState


class State(rx.State):
    n_machines: int = 1
    n_tasks: int = 1
    n_precedences: int = -1
    resources_cap: int = -1
    energy_cap: int = -1
    algorithm: str = "sa"

    current_tasks: list[int]

    @rx.event
    def set_energy_cap(self, value: str):
        if value != "":
            self.energy_cap = int(value)

    @rx.event
    def set_resource_cap(self, value: str):
        if value != "":
            self.resource_cap = int(value)

    @rx.event
    def set_seed(self, value: str):
        if value != "":
            self.resource_cap = int(value)

    @rx.event
    def remove_task(self, task_id: str):
        if task_id != "":
            self.tasks.pop(int(task_id), None)

    @rx.event
    def set_algorithm(self, value: str):
        if value != "":
            self.algorithm == value

    @rx.event(background=True)
    async def randomize_task(self):
        algorithm_state = await self.get_state(AlgorithmState)
        algorithm_state.get_param(
            env_param={
                "n_machines": self.n_machines,
                "n_tasks": self.n_tasks,
                "n_precedences": -1,
                "resources_cap": -1,
                "energy_cap": -1,
            },
            algorithm=self.algorithm,
        )


@rx.page(route="/")
def index() -> rx.Component:
    card_layout = {
        "paddingLeft": "2em",
        "paddingTop": "1em",
        "paddingRight": "2em",
        "width": "50%",
    }
    return rx.center(
        rx.card(
            rx.center(
                rx.heading("Generate task", font_size="1.9em", font_weight="medium"),
                marginBottom="2em",
            ),
            rx.button("Randomize"),
            **card_layout,
        ),
        direction="column",
        spacing="5",
        padding="3em",
        width="100%",
    )
