from heapq import heappush, heappop
import math

def shift_schedule(machine_sequences, processing_time, setup_time, precedence,
                   release_time, num_operators):
    # Chuyển Schedule theo trình tự --> thời gian
    machine_free_time = {k: 0 for k in machine_sequences}
    last_op = {k: None for k in machine_sequences}
    op_start, op_end = {}, {}
    running_ops = []  # heap by end time
    completed = set()

    pending = {k: list(seq) for k, seq in machine_sequences.items()}
    active_ops = 0
    time = 0

    while True:
        # 1. Trả về ops đã hoàn thành
        while running_ops and running_ops[0][0] <= time:
            _, finished_op, machine = heappop(running_ops)
            completed.add(finished_op)
            machine_free_time[machine] = time
            active_ops -= 1

        # 2. Tìm ops có thể bắt đầu
        candidates = []
        for k, seq in pending.items():
            if not seq:
                continue
            op = seq[0]
            # precedence check
            if any(pred not in completed for pred in precedence.get(op, [])):
                continue
            # machine available
            if active_ops >= num_operators or time < machine_free_time[k]:
                continue
            # compute earliest start
            prev = last_op[k]
            setup = 0
            if prev is not None:
                setup = setup_time.get(prev, {}).get(op, {}).get(k, 0)
            start = max(release_time.get(op, 0), machine_free_time[k]) + setup
            candidates.append((start, op, k))

        if not candidates and not running_ops:
            break  # finished or infeasible
        if not candidates:
            time = running_ops[0][0]
            continue

        # 3. Earliest finish greedy
        start, op, k = min(candidates, key=lambda x: x[0])
        p = processing_time.get(op, {}).get(k, math.inf)
        if math.isinf(p):
            raise ValueError(f"Operation {op} cannot run on machine {k}")
        end = start + p
        op_start[op], op_end[op] = start, end

        last_op[k] = op
        pending[k].pop(0)
        heappush(running_ops, (end, op, k))
        active_ops += 1
        time = start

    schedule = {op: {'machine': k, 'start': op_start[op], 'end': op_end[op]}
                for k in machine_sequences for op in op_start if op in machine_sequences[k]}
    return schedule


def evaluate_schedule(schedule, due_date, weight):
    # Đánh giá Schedule đã xây dựng bằng cách tạo Cmax, Weighted Tardiness, Load imbalance
    Cmax = max(op['end'] for op in schedule.values())
    weighted_tardiness = sum(
        weight[i] * max(0, schedule[i]['end'] - due_date[i]) for i in schedule
    )

    loads = {}
    for op, data in schedule.items():
        k = data['machine']
        loads.setdefault(k, 0)
        loads[k] += data['end'] - data['start']

    mean_load = sum(loads.values()) / len(loads)
    load_std = (sum((l - mean_load) ** 2 for l in loads.values()) / len(loads)) ** 0.5

    return {
        'Cmax': Cmax,
        'WeightedTardiness': weighted_tardiness,
        'LoadStd': load_std
    }


def evaluate_combined(schedule, due_date, weight, alpha=1.0, beta=1.0, gamma=1.0):
    # Kết hợp nhiều obj thành 1 điểm năng lượng
    metrics = evaluate_schedule(schedule, due_date, weight)
    energy = (alpha * metrics['WeightedTardiness'] +
              beta * metrics['Cmax'] +
              gamma * metrics['LoadStd'])
    metrics['Energy'] = energy
    return metrics

# Test
if __name__ == "__main__":
    machine_sequences = {
        1: ['A', 'B'],
        2: ['C']
    }

    processing_time = {
        'A': {1: 5, 2: 7},
        'B': {1: 6, 2: 4},
        'C': {1: 8, 2: 3}
    }

    setup_time = {
        'A': {'B': {1: 2, 2: 1}},
        'B': {'C': {1: 1, 2: 2}}
    }

    precedence = {
        'B': ['A']
    }

    release_time = {'A': 0, 'B': 0, 'C': 0}
    num_operators = 2

    schedule = shift_schedule(machine_sequences, processing_time, setup_time, precedence, release_time, num_operators)
    print("Schedule:", schedule)

    due_date = {'A': 12, 'B': 15, 'C': 10}
    weight = {'A': 2, 'B': 1, 'C': 1}
    result = evaluate_combined(schedule, due_date, weight)
    print("nEvaluation:", result)