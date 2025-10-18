from typing import List, Dict, Any, Tuple
import random
import math
import statistics


def generate_environment(n_tasks: int = 10, n_machines: int = 3, seed: int = None) -> Tuple[Dict[int, Any], Dict[Tuple[int,int], int], List[Tuple[int,int]]]:
    """
    Returns:
      tasks: dict task_id -> {
         "proc_times": List[int] length n_machines,
         "weight": float (wi),
         "due_date": int (di),
         "release": int (Ri)
      }
      setup: dict (a,b) -> setup_time (int)
      precedences: list of (a,b) meaning a must finish before b starts
    """
    if seed is not None:
        random.seed(seed)


    tasks: Dict[int, Any] = {}
    base_proc = [random.randint(5, 30) for _ in range(n_tasks)]
    for t in range(n_tasks):
        times = []
        for _ in range(n_machines):
            modifier = random.choice([0.6, 0.8, 1.0, 1.2, 1.6])
            times.append(max(1, int(base_proc[t] * modifier)))
        tasks[t] = {
            "proc_times": times,
            "weight": random.uniform(1.0, 3.0),
            "due_date": random.randint(50, 200),
            "release": random.randint(0, 20),
        }


    # Setup matrix: time to switch from a -> b (sequence-dependent)
    setup: Dict[Tuple[int,int], int] = {}
    for a in range(n_tasks):
        for b in range(n_tasks):
            setup[(a,b)] = 0 if a == b else random.randint(0, 10)


    # Precedence list (a,b): a must finish before b
    precedences: List[Tuple[int,int]] = []
    n_pre = random.randint(0, max(1, n_tasks // 3))
    tries = 0
    while len(precedences) < n_pre and tries < n_pre * 10:
        a, b = random.sample(range(n_tasks), 2)
        if a != b and (a,b) not in precedences:
            precedences.append((a,b))
        tries += 1


    return tasks, setup, precedences




def generate_schedule(tasks: Dict[int, Any], n_machines: int = 3) -> Dict[int, List[int]]:
    """
    Simple round-robin assignment returning sequences per machine.
    This is the solution encoding expected by build_schedule.
    """
    schedule = {k: [] for k in range(n_machines)}
    for i, tid in enumerate(sorted(tasks.keys())):
        schedule[i % n_machines].append(tid)
    return schedule




# ---------------- Shift schedule phase ----------------
def build_schedule(
    machine_sequences: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setup: Dict[Tuple[int,int], int],
    precedences: List[Tuple[int,int]],
    operator_limit: int = 2,
    max_penalty: float = 1e6,
) -> Tuple[bool, Dict[int,float], Dict[int,float], Dict[int,float], Dict]:
    """
    Convert sequence encoding -> timeline (Si, Ci) observing:
      - unrelated machine processing times (proc_times[task][machine])
      - sequence-dependent setup times setup[(prev, cur)]
      - precedence constraints (precedences list)
      - limited concurrent operators (operator_limit)


    Returns:
      feasible: bool (False if deadlock/infeasible)
      Si: dict task->start_time
      Ci: dict task->completion_time
      machine_loads: dict machine->total_processing_including_setup
      info: dict with metrics: makespan, weighted_tardiness, load_std
    """
    # bookkeeping
    Si: Dict[int,float] = {}
    Ci: Dict[int,float] = {}
    n_total = sum(len(seq) for seq in machine_sequences.values())


    # pointers for next index in each machine sequence
    ptr = {k: 0 for k in machine_sequences.keys()}
    # last operation on machine k (for setup)
    last_op = {k: None for k in machine_sequences.keys()}
    machine_free_time = {k: 0.0 for k in machine_sequences.keys()}
    running: List[Tuple[float,int,int]] = []  # list of (end_time, op_id, machine)
    current_time = 0.0


    # quick predecessor map
    preds = {i: [] for i in tasks.keys()}
    for a,b in precedences:
        preds[b].append(a)


    # helper to check predecessors done
    def preds_done(op_id):
        for p in preds.get(op_id, []):
            if p not in Ci:
                return False
        return True


    # total processed ops count
    done_count = 0
    attempts = 0
    MAX_ATTEMPTS = 100000  # safeguard


    while done_count < n_total and attempts < MAX_ATTEMPTS:
        attempts += 1
        # remove finished from running and update current_time if needed
        running = sorted(running, key=lambda x: x[0])
        if running and (len(running) >= operator_limit or not any(
            ( (ptr[k] < len(machine_sequences[k])) and preds_done(machine_sequences[k][ptr[k]]) and machine_free_time[k] <= current_time)
            for k in machine_sequences.keys()
        )):
            # advance to next finishing op if we can't start new one now
            next_end = running[0][0]
            current_time = max(current_time, next_end)
            # pop finished
            finished = [r for r in running if r[0] <= current_time]
            for end_t, op_id, m in finished:
                if op_id not in Ci:
                    Ci[op_id] = end_t
                    done_count += 1
            running = [r for r in running if r[0] > current_time]
            continue


        # Build candidate list: (machine, op, earliest_start)
        candidates = []
        for k, seq in machine_sequences.items():
            if ptr[k] >= len(seq):
                continue
            op = seq[ptr[k]]
            if not preds_done(op):
                continue
            # compute earliest start given machine free time, predecessors completion, release time
            pred_finish = max([Ci[p] for p in preds.get(op, [])]) if preds.get(op, []) else 0.0
            rel = tasks[op].get("release", 0.0)
            machine_ready = machine_free_time[k]
            setup_time = 0 if last_op[k] is None else setup.get((last_op[k], op), 0)
            est = max(current_time, pred_finish, rel, machine_ready) + setup_time
            # processing time depends on machine k (unrelated machines)
            proc = tasks[op]["proc_times"][k]
            eft = est + proc
            candidates.append( (est, eft, k, op, setup_time, proc) )


        if not candidates and not running:
            # deadlock (no candidate to start and no running)
            return False, Si, Ci, {}, {"feasible": False, "reason": "deadlock"}


        if not candidates:
            # nothing can start now (maybe operator limit reached) -> advance time
            if running:
                next_end = running[0][0]
                current_time = max(current_time, next_end)
                finished = [r for r in running if r[0] <= current_time]
                for end_t, op_id, m in finished:
                    if op_id not in Ci:
                        Ci[op_id] = end_t
                        done_count += 1
                running = [r for r in running if r[0] > current_time]
            continue


        # choose candidate to start: earliest finish time greedy
        candidates.sort(key=lambda x: (x[1], x[0]))  # prefer earliest finish then earliest start
        est, eft, chosen_m, chosen_op, s_time, p_time = candidates[0]


        # check operator limit
        if len(running) >= operator_limit:
            # someone must finish first
            next_end = running[0][0]
            current_time = max(current_time, next_end)
            finished = [r for r in running if r[0] <= current_time]
            for end_t, op_id, m in finished:
                if op_id not in Ci:
                    Ci[op_id] = end_t
                    done_count += 1
            running = [r for r in running if r[0] > current_time]
            continue


        # start chosen operation at start_time = est - setup_time (we included setup into est)
        start_time = est - s_time
        if start_time < current_time:
            start_time = current_time  # safety
            # recalc eft
            eft = start_time + s_time + p_time


        Si[chosen_op] = start_time
        end_time = eft
        running.append((end_time, chosen_op, chosen_m))


        # update machine pointer & last_op & machine_free_time (machine becomes busy until end_time)
        ptr[chosen_m] += 1
        last_op[chosen_m] = chosen_op
        machine_free_time[chosen_m] = end_time


        # advance current_time a bit (to allow detection)
        # current_time = min(current_time, start_time)
        # keep current_time as is (we move time through finishing events)


    if attempts >= MAX_ATTEMPTS:
        return False, Si, Ci, {}, {"feasible": False, "reason": "max attempts"}


    # finalize any running ops
    for end_t, op_id, m in running:
        if op_id not in Ci:
            Ci[op_id] = end_t


    # compute metrics
    makespan = max(Ci.values()) if Ci else 0.0
    # weighted tardiness
    WT = 0.0
    for op, c in Ci.items():
        di = tasks[op].get("due_date", 1e9)
        tard = max(0.0, c - di)
        WT += tasks[op].get("weight", 1.0) * tard


    # load per machine (processing + setups)
    loads = {k: 0.0 for k in machine_sequences.keys()}
    for k, seq in machine_sequences.items():
        total = 0.0
        prev = None
        for op in seq:
            setup_t = 0 if prev is None else setup.get((prev, op), 0)
            total += setup_t + tasks[op]["proc_times"][k]
            prev = op
        loads[k] = total


    load_values = list(loads.values())
    load_std = statistics.pstdev(load_values) if len(load_values) > 1 else 0.0


    info = {"feasible": True, "makespan": makespan, "WT": WT, "load_std": load_std}
    return True, Si, Ci, loads, info




def objective_function(
    machine_sequences: Dict[int, List[int]],
    tasks: Dict[int, Any],
    setup: Dict[Tuple[int,int], int],
    precedences: List[Tuple[int,int]],
    operator_limit: int = 2,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
    infeasible_penalty: float = 1e5
) -> Tuple[float, Dict]:
    """
    Compute combined objective:
      Objective = alpha * WT + beta * Cmax + gamma * LoadStd
    Returns (energy, info_dict)
    """
    feasible, Si, Ci, loads, info = build_schedule(machine_sequences, tasks, setup, precedences, operator_limit)
    if not feasible:
        return infeasible_penalty, {"feasible": False, "reason": info.get("reason", "infeasible")}
    WT = info["WT"]
    Cmax = info["makespan"]
    LoadStd = info["load_std"]
    energy = alpha * WT + beta * Cmax + gamma * LoadStd
    info.update({"energy": energy})
    return energy, info







