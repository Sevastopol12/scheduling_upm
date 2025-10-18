from scheduling_upm.environment import generate_environment, generate_schedule, objective_function,  build_schedule
from scheduling_upm.simulated_annealing import simulated_annealing


if __name__ == "__main__":
    # parameters
    N_TASKS = 12
    N_MACHINES = 3
    OPERATOR_LIMIT = 2


    tasks, setups, precedences = generate_environment(n_tasks=N_TASKS, n_machines=N_MACHINES, seed=42)
    initial_schedule = generate_schedule(tasks, n_machines=N_MACHINES)
    initial_energy, info = objective_function(initial_schedule, tasks, setups, precedences, operator_limit=OPERATOR_LIMIT)


    print("Precedences:", precedences)
    print("Initial schedule:", initial_schedule)
    print("Initial energy:", initial_energy, "info:", info)


    best_schedule, best_energy, history = simulated_annealing(
        tasks=tasks,
        setups=setups,
        precedences=precedences,
        n_machines=N_MACHINES,
        operator_limit=OPERATOR_LIMIT,
        n_iteration=1500,
        initial_temp=500.0,
        cooling_alpha=0.997,
        alpha_obj=1.0,
        beta_obj=1.0,
        gamma_obj=0.2,
        seed=123
    )


    print("\nBest schedule:", best_schedule)
    print("Best energy:", best_energy)
    # optionally, compute final detailed schedule
    feasible, Si, Ci, loads, info = build_schedule(best_schedule, tasks, setups, precedences, OPERATOR_LIMIT)
    print("Final schedule feasible:", feasible)
    print("Metrics:", info)



