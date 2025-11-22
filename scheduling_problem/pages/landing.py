import reflex as rx

from ..components.landing.setup_environment import (
    apply_button,
    selected_chips,
    task_object,
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
        rx.hstack(
            rx.flex(
                task_section(card_layout=card_layout),
                display_generated_tasks(card_layout=card_layout),
                align="start",
                spacing="4",
                direction="row",
                width="100%",
            ),
            width="100%",
        ),
        rx.center(
            rx.button(
                "Generate",
                on_click=[
                    PageState.generate_environment,
                ],
                size="4",
            ),
            width="100%",
            dicrection="column",
            paddingBottom="1em",
        ),
        rx.flex(
            rx.vstack(
                algorithm_section(card_layout=card_layout),
                width=rx.cond(AlgorithmState.get_task_length > 0, "40%", "100%"),
            ),
            rx.cond(
                AlgorithmState.get_task_length > 0,
                plot_schedule(),
                rx.fragment(),
            ),
            marginTop="4em",
            marginBottom="4em",
            direction="row",
            spacing="4",
            width="100%",
        ),
        paddingRight="3em",
        paddingLeft="3em",
        paddingTop="2em",
        direction="column",
        spacing="4",
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
                    marginBottom="1em",
                ),
                rx.scroll_area(
                    generate_task(),
                    constraint_settings(),
                    paddingRight="0.7em",
                    width="100%",
                    height="70vh",
                ),
                rx.center(
                    apply_button(
                        "book_heart",
                        "Default setting",
                        PageState.set_to_default,
                        "gray",
                    ),
                    apply_button("shuffle", "Randomize", PageState.randomize, "violet"),
                    rx.spacer(),
                    apply_button("bean", "seed", PageState.generate_seed, "grass"),
                    rx.badge(
                        PageState.seed,
                        size="3",
                        font_weight="regular",
                        variant="surface",
                        radius="full",
                    ),
                    spacing="2",
                    width="100%",
                    marginTop="1em",
                ),
                **card_layout,
            ),
            direction="column",
            spacing="5",
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
                    marginBottom="1em",
                ),
                rx.scroll_area(
                    algorithm_settings(),
                    paddingRight="0.7em",
                    width="100%",
                    height="70vh",
                ),
                rx.center(
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
                    apply_button(
                        "book_heart",
                        "Optimize",
                        AlgorithmState.scheduling_result,
                        "violet",
                    ),
                    direction="row",
                    spacing="2",
                    width="100%",
                    marginTop="2em",
                    align="center",
                ),
                width=rx.cond(AlgorithmState.get_task_length > 0, "100%", "60%"),
                paddingLeft="2em",
                paddingTop="1em",
                paddingRight="2em",
            ),
            direction="column",
            spacing="5",
            width=rx.cond(AlgorithmState.get_task_length > 0, "100%", "100%"),
        ),
    )


def display_generated_tasks(card_layout) -> rx.Component:
    scroll_layout = {
        "width": "100%",
        "paddingRight": "0.7em",
        "height": "auto",
        "max_height": "25vh",
        "type": "hover",
    }
    card_width = {"width": "100%"}
    return rx.center(
        rx.card(
            rx.flex(
                rx.center(
                    rx.heading(
                        "Generated Task",
                        font_size="2.3em",
                        font_weight="medium",
                    ),
                    spacing="5",
                    direction="row",
                    width="100%",
                    marginBottom="1em",
                ),
                rx.scroll_area(
                    rx.vstack(
                        task_props(card_width, scroll_layout),
                        show_energy(card_width, scroll_layout),
                        show_setups(card_width, scroll_layout),
                        show_precedences(card_width, scroll_layout),
                        width="100%",
                    ),
                    width="100%",
                    height="67vh",
                    type="hover",
                    scrollbars="vertical",
                    paddingRight="0.7em",
                ),
                rx.hstack(
                    rx.spacer(),
                    apply_button(
                        "trash",
                        "Remove all",
                        [
                            AlgorithmState.remove_precedences,
                            AlgorithmState.remove_energy,
                            AlgorithmState.remove_resource,
                            AlgorithmState.remove_tasks,
                            AlgorithmState.remove_setups,
                        ],
                        "tomato",
                    ),
                    width="100%",
                ),
                direction="column",
                spacing="4",
            ),
            **card_layout,
            height="85vh",
        ),
        direction="column",
        spacing="5",
        width="50%",
    )


def task_props(card_width, scroll_layout) -> rx.Component:
    return (
        rx.card(
            rx.hstack(
                rx.heading("Tasks", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                rx.dialog.root(
                    rx.dialog.trigger(
                        apply_button(
                            "plus",
                            "Add",
                            None,
                            color_scheme="grass",
                        ),
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Add a task"),
                        rx.form(
                            rx.flex(
                                rx.input(placeholder="weight", name="weight"),
                                rx.input(placeholder="resource usage", name="resource"),
                                rx.input(placeholder="energy usage", name="resource"),
                                rx.input(
                                    placeholder="process times", name="process_times"
                                ),
                                rx.flex(
                                    rx.dialog.close(
                                        rx.button(
                                            "Cancel",
                                            variant="soft",
                                            color_scheme="gray",
                                        ),
                                    ),
                                    rx.dialog.close(
                                        rx.button("Submit", type="submit"),
                                    ),
                                    spacing="3",
                                    justify="end",
                                ),
                                direction="column",
                                spacing="4",
                            ),
                            on_submit=AlgorithmState.add_task,
                            reset_on_submit=False,
                        ),
                    ),
                ),
                spacing="3",
                align="center",
                width="100%",
                marginBottom="1em",
            ),
            rx.scroll_area(
                rx.grid(
                    rx.foreach(
                        AlgorithmState.convert_task_object,
                        lambda item: rx.tooltip(
                            selected_chips(f"task {item[0]}", "calendar"),
                            content=f"process time: [ {item[1]['process_times']}] | resource: {item[1]['resource']} | weight: {item[1]['weight']}",
                        ),
                    ),
                    width="100%",
                    columns="4",
                    spacing="2",
                ),
                **scroll_layout,
            ),
            direction="column",
            **card_width,
        ),
    )


def show_precedences(card_width, scroll_layout) -> rx.Component:
    return (
        rx.card(
            rx.hstack(
                rx.heading("Precedences", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                spacing="3",
                align="center",
                width="100%",
                marginBottom="1em",
            ),
            rx.scroll_area(
                rx.grid(
                    rx.foreach(
                        AlgorithmState.convert_precedences_relations,
                        lambda item: rx.tooltip(
                            selected_chips(f"task {item[0]}", "calendar"),
                            content=f"Posteriors: [ {item[1]}]",
                        ),
                    ),
                    width="100%",
                    columns="4",
                    spacing="2",
                ),
                **scroll_layout,
            ),
            direction="column",
            **card_width,
        ),
    )


def show_energy(card_width, scroll_layout) -> rx.Component:
    return (
        rx.card(
            rx.hstack(
                rx.heading("Energy", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                spacing="3",
                align="center",
                width="100%",
                marginBottom="1em",
            ),
            rx.scroll_area(
                rx.grid(
                    rx.foreach(
                        AlgorithmState.convert_energy_consumption,
                        lambda item: rx.tooltip(
                            selected_chips(item[0], "calendar"),
                            content=f"energy consume: [{item[1]}]",
                        ),
                    ),
                    width="100%",
                    columns="5",
                    spacing="2",
                ),
                **scroll_layout,
            ),
            direction="column",
            **card_width,
        ),
    )


def show_setups(card_width, scroll_layout) -> rx.Component:
    return (
        rx.card(
            rx.hstack(
                rx.heading("Setups relation", font_size="1.6em", font_weight="medium"),
                rx.spacer(),
                spacing="3",
                align="center",
                width="100%",
                marginBottom="1em",
            ),
            rx.scroll_area(
                rx.grid(
                    rx.foreach(
                        AlgorithmState.convert_setups_for_display,
                        lambda item: rx.foreach(
                            item[1],
                            lambda item_1: rx.tooltip(
                                selected_chips(f"({item[0]}, {item_1[0]})"),
                                content=f"setup time: {item_1[1]}",
                            ),
                        ),
                    ),
                    width="100%",
                    columns="4",
                    spacing="2",
                ),
                **scroll_layout,
            ),
            direction="column",
            **card_width,
        ),
    )


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
        load_balancing(),
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


def load_balancing() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.flex(
                rx.heading(
                    "Load balance: ",
                    font_weight="medium",
                    font_size="1.6em",
                ),
                rx.spacer(),
                rx.center(
                    rx.switch(
                        on_change=PageState.apply_load_balance,
                        checked=PageState.use_load_balance,
                    ),
                    rx.badge(rx.cond(PageState.use_load_balance, "enable", "disable")),
                    spacing="2",
                ),
                direction="row",
                align="center",
            ),
            opacity=rx.cond(PageState.use_load_balance, "1.0", "0.5"),
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
        constraint_weight(),
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
                width="100%",
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
                width="100%",
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
                width="100%",
                spacing="4",
            ),
            direction="column",
            width="100%",
            spacing="4",
        ),
        width="100%",
    )


def constraint_weight() -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.heading("Load-Energy", font_size="1.6em", font_weight="medium"),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.hstack(
                rx.badge(f"Load: {round(AlgorithmState.alpha_load, 3)}"),
                rx.slider(
                    value=[AlgorithmState.alpha_load],
                    on_change=AlgorithmState.set_load_energy_ratio,
                    step=0.01,
                    _min=0.00,
                    max=0.5,
                    value_range=[0.00, 0.5],
                ),
                rx.badge(f"Energy: {round(AlgorithmState.alpha_energy, 3)}"),
                align="end",
                width="100%",
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
    return rx.card(
        rx.center(
            rx.heading("Job Scheduling Visualization", font_size="2.3em"),
            rx.scroll_area(
                rx.vstack(
                    rx.card(
                        rx.center(
                            rx.heading("Simulated Annealing", font_size="1.6em"),
                            rx.center(
                                rx.heading("Total cost:", font_size="1.3em"),
                                rx.badge(
                                    f"{AlgorithmState.sa_cost['total_cost']:.3f}",
                                    variant="outline",
                                    size="3",
                                    color="accent",
                                ),
                                direction="row",
                                spacing="3",
                                width="100%",
                            ),
                            cost_value(AlgorithmState.sa_cost),
                            spacing="3",
                            direction="column",
                            paddingBottom="2em",
                        ),
                        schedule_chart(data=AlgorithmState.sa_plot),
                        width="100%",
                    ),
                    rx.card(
                        rx.center(
                            rx.heading("Whales", font_size="1.6em"),
                            rx.center(
                                rx.heading("Total cost:", font_size="1.3em"),
                                rx.badge(
                                    f"{AlgorithmState.whales_cost['total_cost']:.3f}",
                                    variant="outline",
                                    size="3",
                                    color="accent",
                                ),
                                direction="row",
                                spacing="3",
                                width="100%",
                            ),
                            cost_value(AlgorithmState.whales_cost),
                            spacing="3",
                            direction="column",
                            paddingBottom="2em",
                        ),
                        schedule_chart(data=AlgorithmState.whales_plot),
                        width="100%",
                    ),
                    rx.card(
                        rx.center(
                            rx.heading("Hybrid", font_size="1.6em"),
                            rx.center(
                                rx.heading("Total cost:", font_size="1.3em"),
                                rx.badge(
                                    f"{AlgorithmState.hybrid_cost['total_cost']:.3f}",
                                    variant="outline",
                                    size="3",
                                    color="accent",
                                ),
                                direction="row",
                                spacing="3",
                                width="100%",
                            ),
                            cost_value(AlgorithmState.hybrid_cost),
                            spacing="3",
                            direction="column",
                            paddingBottom="2em",
                        ),
                        schedule_chart(data=AlgorithmState.hybrid_plot),
                        width="100%",
                    ),
                    width="100%",
                    align="center",
                ),
                height="70vh",
                width="53vw",
                align="center",
            ),
            paddingRight="0.7em",
            direction="column",
            spacing="6",
            width="100%",
        )
    )


def cost_value(cost: dict) -> rx.Component:
    badge_layout = {
        "variant": "soft",
        "font_weight": "medium",
        "radius": "medium",
        "font_size": "0.9em",
        "color": "accent",
    }
    return rx.hstack(
        rx.card(
            rx.vstack(
                rx.heading("Makespan", font_size="1.2em"),
                rx.badge(cost["makespan"], **badge_layout),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Deadlock", font_size="1.2em"),
                rx.badge(
                    f"{cost['precedence_penalty'].to(int) // int(1e6)}", **badge_layout
                ),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Load std_dev", font_size="1.2em"),
                rx.badge(cost["std_dev"], **badge_layout),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.heading("Energy exceeds", font_size="1.2em"),
                rx.badge(cost["energy_exceeds"], **badge_layout),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        align="center",
        justify="between",
        width="80%",
    )
