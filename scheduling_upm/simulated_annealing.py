import math
import random
import copy
from typing import Dict, Any, Tuple, List
from .environment import generate_schedule, objective_function, build_schedule


def simulated_annealing(
    tasks: Dict[int, Any],
    setups: Dict[Tuple[int,int], int],
    precedences: List[Tuple[int,int]],
    n_machines: int,
    operator_limit: int = 2,
    n_iteration: int = 2000,
    initial_temp: float = 1000.0,
    cooling_alpha: float = 0.995,
    alpha_obj: float = 1.0,
    beta_obj: float = 1.0,
    gamma_obj: float = 0.1,
    seed: int = None
) -> Tuple[Dict[int,List[int]], float, List[Dict]]:
    """
    Simulated Annealing that operates on sequence encoding:
      - schedule is dict machine -> [op1, op2, ...]
      - neighbor generation tries swaps between machines or within a machine
      - neighbor accepted only if build_schedule is feasible (no deadlock)
    Returns best_schedule, best_energy, history
    """
    if seed is not None:
        random.seed(seed)


    # initial solution
    current_schedule = generate_schedule(tasks, n_machines)
    current_energy, _ = objective_function(current_schedule, tasks, setups, precedences, operator_limit, alpha_obj, beta_obj, gamma_obj)
    best_schedule = copy.deepcopy(current_schedule)
    best_energy = current_energy


    history: List[Dict] = []
    for it in range(n_iteration):
        T = initial_temp * (cooling_alpha ** it)
        neighbor = generate_neighbor(current_schedule)
        # try to evaluate neighbor; if infeasible, try limited number of alternative neighbors
        tries = 0
        MAX_TRIES = 50
        energy, info = objective_function(neighbor, tasks, setups, precedences, operator_limit, alpha_obj, beta_obj, gamma_obj)
        while (not info.get("feasible", True)) and tries < MAX_TRIES:
            neighbor = generate_neighbor(current_schedule)
            energy, info = objective_function(neighbor, tasks, setups, precedences, operator_limit, alpha_obj, beta_obj, gamma_obj)
            tries += 1


        if not info.get("feasible", True):
            # couldn't find feasible neighbor; skip iteration
            history.append({"iter": it, "current_energy": current_energy, "best_energy": best_energy})
            if T < 1e-9:
                break
            continue


        # acceptance criterion
        if accept_move(current_energy, energy, T):
            current_schedule = neighbor
            current_energy = energy


        if energy < best_energy:
            best_schedule = copy.deepcopy(neighbor)
            best_energy = energy


        history.append({"iter": it, "current_energy": current_energy, "best_energy": best_energy})


        if T < 1e-9:
            break


    return best_schedule, best_energy, history




def generate_neighbor(schedule: Dict[int,List[int]]) -> Dict[int,List[int]]:
    """
    Generate neighbor by:
      - swapping two operations between machines OR
      - swapping two positions within same machine (with some probability)
    Note: feasibility is checked in objective_function via build_schedule; this function makes the swap only.
    """
    new_sched = copy.deepcopy(schedule)
    machines = list(new_sched.keys())


    # choose swap type
    if random.random() < 0.4:
        # swap between two different machines (positions)
        m1, m2 = random.sample(machines, 2)
        if not new_sched[m1] or not new_sched[m2]:
            return new_sched
        i = random.randrange(len(new_sched[m1]))
        j = random.randrange(len(new_sched[m2]))
        new_sched[m1][i], new_sched[m2][j] = new_sched[m2][j], new_sched[m1][i]
    else:
        # swap within one machine (if length >=2)
        m = random.choice(machines)
        if len(new_sched[m]) < 2:
            return new_sched
        i, j = random.sample(range(len(new_sched[m])), 2)
        new_sched[m][i], new_sched[m][j] = new_sched[m][j], new_sched[m][i]


    return new_sched




def accept_move(old_energy: float, new_energy: float, T: float) -> bool:
    if new_energy < old_energy:
        return True
    if T <= 0:
        return False
    try:
        p = math.exp(-(new_energy - old_energy) / T)
    except OverflowError:
        p = 0.0
    return random.random() < p



