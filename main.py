from scheduling_upm.utils.environment import generate_environment
from scheduling_upm.whales_optim import WhaleOptimizationAlgorithm
from scheduling_upm.simulated_annealing import SimulatedAnnealing

environment = generate_environment(n_tasks=20, n_machines=4, seed=2503)

n_machines = environment.pop("n_machines", 2)
n_tasks = environment.pop("n_tasks", 4)
tasks = environment.pop("tasks", 4)
setups = environment.pop("setups", {})
total_resource = environment.pop("total_resource", None)
precedences = environment.pop("precedences", {})
energy_constraint = environment.pop("energy_constraint", {})


solution = WhaleOptimizationAlgorithm(
    tasks=tasks,
    setups=setups,
    n_machines=n_machines,
    precedences=precedences,
    energy_constraint=energy_constraint,
    total_resource=200,
    n_iterations=int(1e3),
).optimize()

solution, _ = SimulatedAnnealing(
    tasks=tasks,
    setups=setups,
    n_machines=n_machines,
    precedences=precedences,
    energy_constraint=energy_constraint,
    total_resource=200,
    n_iterations=int(1e5),
).optimize()
best_schedule, best_cost = solution.schedule, solution.cost

print(best_cost)
for machine, seq in best_schedule.items():
    print(f"{machine}: {seq}")


best_solution_hybrid, total_time = hybrid_woa_sa(
    tasks=tasks,
    setups=setups,
    precedences=precedences,
    n_machines=n_machines,
    n_schedules=10,        
    n_iterations=100,      
    sa_local_iters=2,      
    seed=2503,
    energy_constraint=energy_constraint,
    total_resource=200,
)

best_schedule_hybrid, best_cost_hybrid = best_solution_hybrid.schedule, best_solution_hybrid.cost

print("\n--- Hybrid WOA + SA ---")
print(f"Best cost: {best_cost_hybrid}")
for machine, seq in best_schedule_hybrid.items():
    print(f"{machine}: {seq}")