import matplotlib.pyplot as plt
import matplotlib.patches as patches


def visualize_schedule(schedule_obj, title="Schedule Visualization", padding=5):
    milestones = schedule_obj.milestones

    # Time bounds
    min_time = min(m["start_setup"] for m in milestones.values())
    max_time = max(m["complete_time"] for m in milestones.values())
    time_span = max_time - min_time
    fig_width = max(10, time_span * 0.05)

    # Machines
    machines = sorted(set(m["machine"] for m in milestones.values()))
    machine_positions = {m: i for i, m in enumerate(machines)}

    fig, ax = plt.subplots(figsize=(fig_width, 6))

    bar_height = 0.6
    y_label_padding = 0.5  # extra space above top machine for task labels

    for task, m in milestones.items():
        machine = m["machine"]
        y = machine_positions[machine]

        # Time points
        t_setup_start = m["start_setup"]
        t_process_start = m["start_process"]
        t_complete = m["complete_time"]

        setup_duration = t_process_start - t_setup_start
        process_duration = t_complete - t_process_start

        # Setup bar
        ax.add_patch(
            patches.Rectangle(
                (t_setup_start, y - bar_height / 2),
                setup_duration,
                bar_height,
                edgecolor="black",
                facecolor="#a6cee3",
                label="Setup" if task == list(milestones.keys())[0] else "",
            )
        )

        # Process bar
        ax.add_patch(
            patches.Rectangle(
                (t_process_start, y - bar_height / 2),
                process_duration,
                bar_height,
                edgecolor="black",
                facecolor="#1f78b4",
                label="Process" if task == list(milestones.keys())[0] else "",
            )
        )

        # Duration text
        ax.text(
            t_setup_start + setup_duration / 2,
            y,
            f"{setup_duration:.1f}",
            ha="center",
            va="center",
            fontsize=8,
            color="black",
        )
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
            t_setup_start + setup_duration / 2,
            y + bar_height / 2 + 0.1,
            f"T{task}",
            ha="center",
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

    ax.set_ylabel("Machines")
    ax.set_title(title)

    # Grid and legend
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.show()
