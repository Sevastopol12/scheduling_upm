from scheduling_upm.environment import generate_environment
from scheduling_upm.utils.operations import generate_schedule, objective_function
from scheduling_upm.simulated_annealing import simulated_annealing

environment = generate_environment(n_tasks=20, n_machines=4, seed=2503)

n_machines = environment.pop("n_machines", 2)
n_tasks = environment.pop("n_tasks", 4)
tasks = environment.pop("tasks", 4)
setups = environment.pop("setups", {})
precedences = environment.pop("precedences", {})

schedule = generate_schedule(tasks=tasks, n_machines=n_machines)
cost = objective_function(schedule=schedule, tasks=tasks, setups=setups)

print(
    simulated_annealing(
        tasks=tasks, setups=setups, n_machines=n_machines, precedences=precedences
    )
)
