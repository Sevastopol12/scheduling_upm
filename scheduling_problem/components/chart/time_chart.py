import reflex as rx
import matplotlib.pyplot as plt
import matplotlib.patches as patches  # Import patches
import io
import base64
from typing import Dict, Any, Union, Optional


def plot_schedule_to_base64(
    milestones: Dict[str, Dict[str, Union[int, float]]],
    title="Schedule Visualization",
    padding=5,
) -> str:
    """
    Generates a Matplotlib schedule visualization (Gantt chart)
    and returns it as a Base64-encoded PNG image string.
    """
    if not isinstance(milestones, dict):
        # The proxy might be behaving like a list of tuples or an ordered collection.
        # This conversion attempts to resolve it back to a standard dict.
        try:
            milestones = dict(milestones)
        except (TypeError, ValueError):
            # If it's truly unconvertible, just return empty.
            return ""

    if not milestones:
        return ""

    # Time bounds
    min_time = min(m["start_setup"] for m in milestones.values())
    max_time = max(m["complete_time"] for m in milestones.values())
    fig_width = 10
    fig_height = 5

    # Machines
    machines = sorted(set(m["machine"] for m in milestones.values()))
    machine_positions = {m: i for i, m in enumerate(machines)}

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    bar_height = 0.6
    y_label_padding = 0.5

    # Helper for legend:
    legend_added = {"setup": False, "process": False}

    for task, m in milestones.items():
        machine = m["machine"]
        y = machine_positions[machine]

        # Time points
        t_setup_start = m["start_setup"]
        t_process_start = m["start_process"]

        setup_duration = t_process_start - t_setup_start
        process_duration = m["complete_time"] - t_process_start

        # Setup bar
        if setup_duration > 0:
            ax.add_patch(
                patches.Rectangle(
                    (t_setup_start, y - bar_height / 2),
                    setup_duration,
                    bar_height,
                    edgecolor="black",
                    facecolor="#a6cee3",  # Light blue
                    label="Setup" if not legend_added["setup"] else None,
                )
            )
            legend_added["setup"] = True

            # Duration text for Setup
            ax.text(
                t_setup_start + setup_duration / 2,
                y,
                f"{setup_duration:.1f}",
                ha="center",
                va="center",
                fontsize=8,
                color="black",
            )

        # Process bar
        ax.add_patch(
            patches.Rectangle(
                (t_process_start, y - bar_height / 2),
                process_duration,
                bar_height,
                edgecolor="black",
                facecolor="#1f78b4",  # Dark blue
                label="Process" if not legend_added["process"] else None,
            )
        )
        legend_added["process"] = True

        # Duration text for Process
        ax.text(
            t_process_start + process_duration / 2,
            y,
            f"{process_duration:.1f}",
            ha="center",
            va="center",
            fontsize=8,
            color="white",
        )

        # Task ID above bars
        ax.text(
            t_setup_start,
            y + bar_height / 2 + 0.1,
            f"T{task}",
            ha="left",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    # Y-axis ticks and labels
    ax.set_yticks(list(machine_positions.values()))
    ax.set_yticklabels([f"Machine {m}" for m in machines])

    # Set y-limits to fit all bars and labels
    ax.set_ylim(-0.5, len(machines) - 0.5 + y_label_padding)

    # X-axis
    ax.set_xlabel("Time")
    ax.set_xlim(min_time - padding, max_time + padding)

    ax.set_title(title, fontsize=16, fontweight="bold")

    # Grid and legend
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="upper right")

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)

    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"


def schedule_chart(data):
    return rx.center(
        rx.cond(
            data,
            rx.image(
                src=data,
                alt="Matplotlib Schedule Gantt Chart",
                max_width="1000em",
                width="100%",
            ),
            rx.fragment(),
        )
    )
