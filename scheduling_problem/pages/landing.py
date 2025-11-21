import reflex as rx

from ..components.landing.setup_environment import (
    apply_button,
    selected_chips,
    num_constraint_input,
    slider_input,
)
from ..components.states.page_state import PageState
from ..components.states.algorithm_state import State as AlgorithmState
from ..components.chart.time_chart import schedule_chart


@rx.page(route="/")
def index() -> rx.Component:
    card_layout = {
        "paddingLeft": "2em",
        "paddingTop": "1em",
        "paddingRight": "2em",
        "width": "100%",
    }

    return rx.flex(
        rx.flex(
            task_section(card_layout=card_layout),
            algorithm_section(card_layout=card_layout),
            align="start",
            direction="row",
            width="100%",
        ),
        rx.center(
            rx.button(
                "Generate",
                on_click=[
                    PageState.generate_environment,
                    AlgorithmState.scheduling_result,
                ],
                size="4",
            ),
            width="100%",
            dicrection="column",
            paddingBottom="1em",
        ),
        plot_schedule(),
        direction="column",
        spacing="5",
        width="100%",
    )


# Task section
def task_section(card_layout) -> rx.Component:
    return (
        rx.center(
            rx.card(
                rx.center(
                    rx.heading(
                        "Problem settings",
                        font_size="2.3em",
                        font_weight="medium",
                    ),
                    direction="column",
                    spacing="4",
                    marginBottom="2em",
                ),
                rx.scroll_area(
                    generate_task(),
                    constraint_settings(),
                    paddingRight="0.7em",
                    width="100%",
                    height="50vh",
                ),
                rx.center(
                    apply_button(
                        "book_heart",
                        "Default setting",
                        PageState.set_to_default,
                        "gray",
                    ),
                    apply_button("shuffle", "Randomize", PageState.randomize, "violet"),
                    spacing="2",
                    width="100%",
                    marginTop="2em",
                ),
                **card_layout,
            ),
            direction="column",
            spacing="5",
            paddingRight="1em",
            paddingLeft="3em",
            paddingTop="3em",
            width="50%",
        ),
    )


def algorithm_section(card_layout) -> rx.Component:
    return (
        rx.center(
            rx.card(
                rx.center(
                    rx.heading(
                        "Algorithm settings",
                        font_size="2.3em",
                        font_weight="medium",
                    ),
                    marginBottom="2em",
                ),
                rx.scroll_area(
                    algorithm_settings(),
                    paddingRight="0.7em",
                    width="100%",
                    height="50vh",
                ),
                rx.center(
                    rx.spacer(),
                    num_constraint_input(
                        "iterations",
                        PageState.set_n_iterations,
                        PageState.n_iterations,
                    ),
                    apply_button(
                        "book_heart",
                        "Default setting",
                        PageState.set_algorithm_to_default,
                        "gray",
                    ),
                    apply_button("bean", "seed", PageState.generate_seed, "grass"),
                    rx.badge(
                        PageState.seed,
                        font_size="1em",
                        font_weight="regular",
                        variant="surface",
                        radius="full",
                    ),
                    direction="row",
                    spacing="2",
                    width="100%",
                    marginTop="2em",
                    align="center",
                ),
                **card_layout,
            ),
            direction="column",
            spacing="5",
            paddingLeft="1em",
            paddingRight="3em",
            paddingTop="3em",
            width="50%",
        ),
    )


# Settings's UI


def generate_task() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.heading("Task generation", font_size="1.6em", font_weight="medium"),
            rx.flex(
                num_constraint_input(
                    "machines", PageState.set_n_machines, PageState.n_machines
                ),
                num_constraint_input("task", PageState.set_n_tasks, PageState.n_tasks),
                direction="row",
                spacing="5",
                align="center",
                justify="between",
            ),
            direction="column",
            spacing="4",
        ),
        width="100%",
        marginBottom="1.5em",
    )


def constraint_settings() -> rx.Component:
    return rx.flex(
        setup_relations(),
        precedence_relations(),
        resource_distribution(),
        energy_consumption(),
        direction="column",
        width="100%",
        spacing="5",
        marginTop="1em",
    )


# Page's Component


def precedence_relations() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading("Precedences", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                rx.center(
                    rx.switch(
                        on_change=PageState.apply_precedences,
                        checked=PageState.use_precedences,
                    ),
                    rx.badge(rx.cond(PageState.use_precedences, "enable", "disable")),
                    spacing="2",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.hstack(
                num_constraint_input(
                    "number of precedences",
                    PageState.set_n_precedences,
                    PageState.n_precedences,
                    PageState.use_precedences,
                ),
                width="100%",
            ),
            opacity=rx.cond(PageState.use_precedences, "1.0", "0.5"),
            direction="column",
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def setup_relations() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.flex(
                rx.heading(
                    "Setups: ",
                    font_weight="medium",
                    font_size="1.6em",
                ),
                rx.spacer(),
                rx.center(
                    rx.switch(
                        on_change=PageState.apply_setups,
                        checked=PageState.use_setups,
                    ),
                    rx.badge(rx.cond(PageState.use_setups, "enable", "disable")),
                    spacing="2",
                ),
                direction="row",
                align="center",
            ),
            opacity=rx.cond(PageState.use_setups, "1.0", "0.5"),
            direction="column",
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def resource_distribution() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading("Resources", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                rx.center(
                    rx.switch(
                        on_change=PageState.apply_resources_cap,
                        checked=PageState.use_resources_cap,
                    ),
                    rx.badge(rx.cond(PageState.use_resources_cap, "enable", "disable")),
                    spacing="2",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.hstack(
                num_constraint_input(
                    "cap",
                    PageState.set_resources_cap,
                    PageState.resources_cap,
                    PageState.use_resources_cap,
                ),
                num_constraint_input(
                    "lower",
                    lambda value: PageState.set_resources_bound(0, value),
                    default=PageState.resources_bound[0],
                    disable=PageState.use_resources_cap,
                ),
                num_constraint_input(
                    "upper",
                    lambda value: PageState.set_resources_bound(1, value),
                    default=PageState.resources_bound[1],
                    disable=PageState.use_resources_cap,
                ),
                width="100%",
            ),
            opacity=rx.cond(PageState.use_resources_cap, "1.0", "0.5"),
            direction="column",
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def energy_consumption() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading(
                    "Energy consumption", font_size="1.6em", font_weight="medium"
                ),
                rx.spacer(),
                rx.center(
                    rx.switch(
                        on_change=PageState.apply_energy_cap,
                        checked=PageState.use_energy_cap,
                    ),
                    rx.badge(rx.cond(PageState.use_energy_cap, "enable", "disable")),
                    spacing="2",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.hstack(
                num_constraint_input(
                    "cap",
                    PageState.set_energy_cap,
                    PageState.energy_cap,
                    PageState.use_energy_cap,
                ),
                num_constraint_input(
                    "lower",
                    lambda value: PageState.set_energy_bound(0, value),
                    default=PageState.energy_bound[0],
                    disable=PageState.use_energy_cap,
                ),
                num_constraint_input(
                    "upper",
                    lambda value: PageState.set_energy_bound(1, value),
                    default=PageState.energy_bound[1],
                    disable=PageState.use_energy_cap,
                ),
                width="100%",
            ),
            opacity=rx.cond(PageState.use_energy_cap, "1.0", "0.5"),
            direction="column",
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


# Algorithm settings


def algorithm_settings() -> rx.Component:
    return rx.flex(
        simulated_annealing(),
        whales(),
        hybrid(),
        direction="column",
        width="100%",
        spacing="5",
        marginTop="1em",
    )


def simulated_annealing() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading(
                    "Simulated Annealing", font_size="1.6em", font_weight="medium"
                ),
                rx.spacer(),
                rx.hstack(
                    apply_button("book-heart", "Default", None, "gray"),
                    rx.center(
                        rx.switch(
                            on_change=None,
                            checked=None,
                        ),
                        rx.badge(rx.cond(False, "enable", "disable")),
                        spacing="2",
                    ),
                    align="center",
                    spacing="2",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.vstack(
                slider_input(
                    "explore ratio",
                    display_value=PageState.sa_explore_ratio,
                    on_change=PageState.set_sa_explore_ratio,
                    default=PageState.sa_explore_ratio,
                    value_range=[0.00, 1.00],
                ),
                align="start",
                width="50%",
            ),
            opacity=rx.cond(True, "1.0", "0.5"),
            direction="column",
            width="100%",
            spacing="4",
        ),
        width="100%",
    )


def whales() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading(
                    "Whales Optimization", font_size="1.6em", font_weight="medium"
                ),
                rx.spacer(),
                rx.hstack(
                    apply_button("book-heart", "Default", None, "gray"),
                    rx.center(
                        rx.switch(
                            on_change=None,
                            checked=None,
                        ),
                        rx.badge(rx.cond(False, "enable", "disable")),
                        spacing="2",
                    ),
                    align="center",
                    spacing="2",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.vstack(
                slider_input(
                    "explore ratio",
                    display_value=PageState.whales_explore_ratio,
                    on_change=PageState.set_whales_explore_ratio,
                    default=PageState.whales_explore_ratio,
                    value_range=[0.00, 1.00],
                ),
                num_constraint_input(
                    "number of agents",
                    PageState.set_whales_agents,
                    PageState.whales_agents,
                ),
                align="end",
                width="50%",
                spacing="4",
            ),
            opacity=rx.cond(True, "1.0", "0.5"),
            direction="column",
            width="100%",
            spacing="4",
        ),
        width="100%",
    )


def hybrid() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading("Hybrid", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                rx.hstack(
                    apply_button("book-heart", "Default", None, "gray"),
                    rx.center(
                        rx.switch(
                            on_change=None,
                            checked=None,
                        ),
                        rx.badge(rx.cond(False, "enable", "disable")),
                        spacing="2",
                    ),
                    align="center",
                    spacing="2",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.vstack(
                slider_input(
                    "explore ratio",
                    display_value=PageState.hybrid_explore_ratio,
                    on_change=PageState.set_hybrid_explore_ratio,
                    default=PageState.hybrid_explore_ratio,
                    value_range=[0.00, 1.00],
                ),
                num_constraint_input(
                    "number of agents",
                    PageState.set_hybrid_agents,
                    PageState.hybrid_agents,
                ),
                align="end",
                width="50%",
                spacing="4",
            ),
            direction="column",
            width="100%",
            spacing="4",
        ),
        width="100%",
    )


# Chart


def plot_schedule():
    return rx.center(
        rx.heading("Job Scheduling Visualization", font_size="2.3em"),
        rx.scroll_area(
            rx.vstack(
                rx.card(
                    rx.center(
                        rx.heading("Simulated Annealing", font_size="1.6em"),
                        paddingBottom="2em",
                    ),
                    rx.hstack(
                        schedule_chart(data=AlgorithmState.sa_plot),
                        schedule_chart(data=AlgorithmState.sa_plot),
                        spacing="4",
                    ),
                    width="100%",
                ),
                rx.card(
                    rx.center(
                        rx.heading("Whales", font_size="1.6em"), paddingBottom="2em"
                    ),
                    rx.hstack(
                        schedule_chart(data=AlgorithmState.whales_plot),
                        schedule_chart(data=AlgorithmState.whales_plot),
                        spacing="4",
                    ),
                    width="100%",
                ),
                rx.card(
                    rx.center(
                        rx.heading("Hybrid", font_size="1.6em"), paddingBottom="2em"
                    ),
                    rx.hstack(
                        schedule_chart(data=AlgorithmState.hybrid_plot),
                        schedule_chart(data=AlgorithmState.hybrid_plot),
                        spacing="4",
                    ),
                    width="100%",
                ),
                width="100%",
                align="center",
            ),
            height="88vh",
            width="95vw",
            align="center",
        ),
        direction="column",
        spacing="6",
        width="100%",
    )
