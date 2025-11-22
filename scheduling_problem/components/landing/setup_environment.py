import reflex as rx

from typing import Any, Optional
from reflex.components.radix.themes.base import LiteralAccentColor


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
    title: str = "temp",
    icon: Optional[str] = "",
    on_click: callable = None,
    color_scheme: LiteralAccentColor = "violet",
) -> rx.Component:
    return rx.badge(
        rx.hstack(
            rx.text(title, font_size="1.2em", font_weight="regular"),
            rx.cond(icon != "", rx.icon(icon, size=14), rx.fragment()),
            align="center",
            justify="between",
            width="100%",
        ),
        radius="full",
        size="3",
        variant="surface",
        cursor="pointer",
        style={"_hover": {"opacity": 0.75}},
        color_scheme=color_scheme,
    )


def task_object(
    task_id: str, proc_times: list[int], resource: str, weight: str
) -> rx.Component:
    return rx.hstack(
        rx.grid(
            selected_chips(task_id),
            selected_chips(proc_times),
            selected_chips(resource),
            selected_chips(weight),
            collumns="4",
            width="4",
            spacing="3",
        ),
        width="100%",
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
