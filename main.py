from scheduling_upm.environment import generate_environment
from scheduling_upm.utils.operations import initial_schedule, objective_function
from scheduling_upm.simulated_annealing import simulated_annealing

environment = generate_environment(n_tasks=4, n_machines=2)

n_machines = environment.pop("n_machines", 2)
n_tasks = environment.pop("n_tasks", 4)
tasks = environment.pop("tasks", 4)
setups = environment.pop("setups", {})
total_resource = environment.pop("total_resource")

schedule = initial_schedule(tasks=tasks, n_machines=n_machines)
cost = objective_function(schedule=schedule, tasks=tasks, setups=setups, total_resource=total_resource)

print(simulated_annealing(tasks=tasks, setups=setups, n_machines=n_machines, total_resource=total_resource))
