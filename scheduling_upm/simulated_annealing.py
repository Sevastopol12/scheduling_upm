import math
import random
import copy
from typing import Dict, Any, Tuple, List
from .environment import objective_function, generate_schedule


def simulated_annealing(
    tasks: Dict[str, Any],
    setups: Dict[Tuple[int, int], int],
    n_machines: int,
    n_iteration: int = 1000,
    initial_temp: float = 1000.0,
):
    if not tasks or not setups:
        return []

    """Simulated Annealing"""
    # Initial solution
    history: List[Dict[str, Any]] = []
    candidate_schedule = generate_schedule(tasks=tasks, n_machines=n_machines)
    current_schedule: Dict[int, List[int]] = candidate_schedule
    current_cost: int = objective_function(
        schedule=candidate_schedule, tasks=tasks, setups=setups
    )

    best_schedule = copy.deepcopy(current_schedule)
    best_cost = current_cost

    for iter in range(n_iteration):
        temperature: float = cooling_down(initial_temp=initial_temp, iteration=iter)

        candidate_schedule = adjust_schedule(schedule=candidate_schedule)
        candidate_cost = objective_function(
            schedule=candidate_schedule, tasks=tasks, setups=setups
        )

        acp: float = acceptance_probability(
            old_cost=best_cost, new_cost=candidate_cost, temperature=temperature
        )

        if random.random() < acp:
            current_schedule = candidate_schedule
            current_cost = candidate_cost

        if candidate_cost < best_cost:
            best_schedule = copy.deepcopy(candidate_schedule)
            best_cost = candidate_cost

        history.append(
            {"iteration": iter, "iter_cost": current_cost, "best_cost": best_cost}
        )

        # early stop when temperature got too small
        if temperature < 1e-8:
            break

    return best_schedule, best_cost, history


def adjust_schedule(schedule):
    """Adjustment in schedule, aims to minimize makespan"""
    return schedule


def acceptance_probability(old_cost, new_cost, temperature):
    if new_cost < old_cost:  # If better solution, accept it
        return 1.0
    # avoid division by zero
    if temperature <= 0:
        return 0.0
    # If worse, accept it with a possibility in attempt to escape local minima
    try:
        return math.exp(
            -(new_cost - old_cost) / temperature
        )  # probability of accepting
    except OverflowError:
        return 0.0


def cooling_down(initial_temp: float, iteration: int, alpha: float = 0.995):
    """Exponential cooling"""
    return initial_temp * (alpha**iteration)


if __name__ == "__main__":
    simulated_annealing(tasks={}, setups={}, n_machines=1)
