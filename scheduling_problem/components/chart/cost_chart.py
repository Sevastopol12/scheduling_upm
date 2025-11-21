import reflex as rx
import matplotlib.pyplot as plt
import numpy as np
import io
import base64


def swarm_chart_to_base64(history, lower_q=0.25, upper_q=0.75):
    if not history:
        return ""

    # Extract iteration index
    iterations = np.array([h["iteration"] for h in history])

    # Extract population matrix
    population_costs = [
        [sched.cost["total_cost"] for sched in h["iter_schedule"]] for h in history
    ]

    # Flatten for quantile threshold
    flat_costs = np.array([c for gen in population_costs for c in gen])
    q_low, q_high = np.quantile(flat_costs, [lower_q, upper_q])

    # Filter population for plotting
    filtered_iters = []
    filtered_costs = []
    for i, gen in enumerate(population_costs):
        for c in gen:
            if q_low <= c <= q_high:
                filtered_iters.append(iterations[i])
                filtered_costs.append(c)

    filtered_iters = np.array(filtered_iters)
    filtered_costs = np.array(filtered_costs)

    # Best-so-far cost
    best_costs = np.array([h["best_cost"]["total_cost"] for h in history])
    best_idx = best_costs.argmin()

    #Plot
    fig, ax = plt.subplots(figsize=(12, 7))

    scatter = ax.scatter(
        filtered_iters,
        filtered_costs,
        c=filtered_costs,
        cmap="coolwarm",
        s=40,
        edgecolor="black",
        alpha=0.65,
        label="Population (Quantile filtered)",
    )

    ax.plot(iterations, best_costs, color="limegreen", linewidth=3, label="Best-so-far")

    ax.scatter(
        iterations[best_idx],
        best_costs[best_idx],
        s=350,
        marker="*",
        color="gold",
        edgecolor="black",
        label="Global best",
        zorder=5,
    )

    ax.set_xlabel("Iteration", fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Cost", fontsize=14, fontweight="bold")
    ax.set_title("WOA Convergence (Quantile-Filtered)", fontsize=16, fontweight="bold")

    cbar = plt.colorbar(scatter)
    cbar.set_label("Cost", fontsize=12)

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=12)

    # Convert to base64
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)

    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{data}"


def swarm_schedule_chart(data: str):
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