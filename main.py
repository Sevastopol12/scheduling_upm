from scheduling_upm.utils.environment import generate_environment
from scheduling_upm.whales_optim import WhaleOptimizationAlgorithm
from scheduling_upm.simulated_annealing import SimulatedAnnealing
environment = generate_environment(n_tasks=100, n_machines=10, seed=2503)

n_machines = environment.pop("n_machines", 2)
n_tasks = environment.pop("n_tasks", 4)
tasks = environment.pop("tasks", 4)
setups = environment.pop("setups", {})
total_resource = environment.pop("total_resource", None)
precedences = environment.pop("precedences", {})

solution = WhaleOptimizationAlgorithm(tasks=tasks, setups=setups, n_machines=n_machines, precedences=None, n_iterations=int(1e4)).optimize()
best_schedule, best_cost = solution.schedule, solution.cost

print(best_cost)
for machine, seq in best_schedule.items():
    print(f"{machine}: {seq}")
