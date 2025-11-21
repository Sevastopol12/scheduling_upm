import reflex as rx

from typing import Any, Optional
from reflex.components.radix.themes.base import LiteralAccentColor


class State(rx.State):
    n_tasks: int = 0
    n_machines: int = 0
    seed: Optional[int] = None
    energy_constraint: dict[str, Any] = {}
    energy_cap: Optional[int] = None

    @rx.event
    def set_n_tasks(self, value: str):
        if value != "":
            self.n_tasks = int(value)

    @rx.event
    def set_n_machines(self, value: str):
        if value != "":
            self.n_machines = int(value)

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


def apply_button(
    icon: str, title: str, on_click: callable, color_scheme: LiteralAccentColor
):
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=14),
            rx.text(title, font_size="1.2em", font_weight="medium"),
            align="center",
            justify="between",
        ),
        variant="soft",
        size="2",
        radius="large",
        color_scheme=color_scheme,
        on_click=on_click,
        cursor="pointer",
    )


def selected_chips(
    title: str, icon: str, on_click: callable, color_scheme: LiteralAccentColor
) -> rx.Component:
    return rx.badge(
        rx.hstack(
            rx.text(title, font_size="1.2em", font_weight="regular"),
            rx.icon(icon, size=14),
            align="center",
            justify="between",
        ),
        radius="medium",
        size="3",
        variant="outline",
        cursor="pointer",
        style={"_hover": {"opacity": 0.75}},
        color_scheme=color_scheme,
    )


def num_constraint_input(
    property_title: str, on_change: callable, default: str = "-1", disable: bool = True
) -> rx.Component:
    return rx.hstack(
        rx.badge(
            f"{property_title.capitalize()}: ",
            variant="soft",
            font_weight="medium",
            radius="medium",
            font_size="1em",
            color="accent",
        ),
        rx.input(
            placeholder=f"{property_title}: int",
            type="number",
            variant="surface",
            radius="large",
            on_change=on_change,
            value=default,
            disabled=rx.cond(disable, False, True),
        ),
        align="center",
        spacing="3",
        width="100%",
    )


def slider_input(
    property_title: str,
    on_change: callable,
    display_value: int = 0.00,
    default: float | int = 0.00,
    value_range: list[float, float] | list[int, int] = [0.00, 1.00],
    disable: bool = True,
):
    return rx.vstack(
        rx.badge(
            display_value.to(str),
            radius="medium",
            variant="outline",
            font_size="0.8em",
            font_weight="regular",
        ),
        rx.hstack(
            rx.badge(
                f"{property_title.capitalize()}: ",
                variant="soft",
                font_weight="medium",
                radius="medium",
                size="3",
                color="accent",
            ),
            rx.slider(
                default_value=default,
                value=[display_value],
                min_=value_range[0],
                max=value_range[1],
                on_change=on_change.throttle(100),
                step=value_range[1] * 0.01,
                disabled=rx.cond(disable, False, True),
            ),
            align="center",
            width="100%",
        ),
        width="100%",
        align="center",
        spacing="3",
    )


