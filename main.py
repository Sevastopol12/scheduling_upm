from scheduling_upm.utils.environment import generate_environment
from scheduling_upm.simulated_annealing import SimulatedAnnealing

environment = generate_environment(n_tasks=4, n_machines=2, seed=2503)

n_machines = environment.pop("n_machines", 2)
n_tasks = environment.pop("n_tasks", 4)
tasks = environment.pop("tasks", 4)
setups = environment.pop("setups", {})
precedences = environment.pop("precedences", {})

solution, history = SimulatedAnnealing(tasks=tasks, setups=setups, n_machines=n_machines, precedences=None, n_iterations=1000).optimize()
best_schedule, best_cost = solution.schedule, solution.cost