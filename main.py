from scheduling_upm.environment import generate_environment
from scheduling_upm.utils.operations import initial_schedule, objective_function
from scheduling_upm.simulated_annealing import simulated_annealing

environment = generate_environment(n_tasks=4, n_machines=2)

n_machines = environment.pop("n_machines", 2)
n_tasks = environment.pop("n_tasks", 4)
tasks = environment.pop("tasks", 4)
setups = environment.pop("setups", {})
resources = environment.pop("resources") #lấy resource của từng máy  # đưa resources sa và operations 

schedule = initial_schedule(tasks=tasks, n_machines=n_machines)
cost = objective_function(schedule=schedule, tasks=tasks, setups=setups)
best_schedule, best_cost, history = simulated_annealing(
    tasks=tasks, 
    setups=setups, 
    n_machines=n_machines,)

print(simulated_annealing(tasks=tasks, setups=setups, n_machines=n_machines))
