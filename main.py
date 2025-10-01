from scheduling_upm.environment import (
    generate_environment,
    generate_schedule,
    objective_function,
)
from scheduling_upm.simulated_annealing import simulated_annealing

tasks, setups = generate_environment(n_tasks=4, n_machines=2)
schedule = generate_schedule(tasks=tasks, n_machines=2)
makespan = objective_function(schedule=schedule, tasks=tasks, setups=setups)

print(simulated_annealing(tasks=tasks, setups=setups, n_machines=2))
