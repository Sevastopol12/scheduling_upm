import argparse
import copy
import time
import random
from typing import List

from scheduling_upm.utils.environment import generate_environment
from scheduling_upm.utils.evaluation import objective_function
from scheduling_upm.utils.entities import Schedule
from scheduling_upm.utils.operations import generate_schedule
from scheduling_upm.strategies.woa_strategy import (
    random_explore as woa_random_explore,
    discrete_spiral_update,
    discrete_shrinking_mechanism,
)
from scheduling_upm.strategies.sa_strategy import exploit as sa_exploit

# Mình sẽ dùng WOA để khám phá toàn cục, SA để khai thác cục bộ
def initialize_population(          # tạo dữ liệu ban đầu - điểm xuất phát
    n_schedules: int,
    tasks,
    n_machines: int,
    setups,
    precedences,
    energy_constraint: dict | None = None,
    total_resource: int | None = None,
) -> List[Schedule]:
    pop = []
    for _ in range(n_schedules):
        sched = generate_schedule(tasks=tasks, n_machines=n_machines)
        cost_dict = objective_function(
            schedule=sched,
            tasks=tasks,
            setups=setups,
            precedences=precedences,
            energy_constraint=energy_constraint,
            total_resource=total_resource,
        )
        pop.append(Schedule(schedule=sched, cost=cost_dict["total_cost"]))
    return pop


def linearly_decrement(iter: int, n_iterations: int): # khởi tạo giá trị quyết định tính khám phá
    return 2 - 2 * (iter / max(1, n_iterations))


def hybrid_woa_sa(
    tasks,
    setups,
    precedences,
    n_machines: int | None = None,
    n_schedules: int = 10,
    n_iterations: int = 100,
    sa_local_iters: int = 2,
    seed: int | None = None,
    energy_constraint: dict | None = None,
    total_resource: int | None = None,
):
    population = initialize_population(
        n_schedules=n_schedules,
        tasks=tasks,
        n_machines=n_machines,
        setups=setups,
        precedences=precedences,
        energy_constraint=energy_constraint,
        total_resource=total_resource,
    )
    best = copy.deepcopy(min(population, key=lambda s: s.cost))

    start = time.time()
    for it in range(n_iterations): #xét a, lần lượt dùng woa để cập nhập và SA để tinh chỉnh 
        a = linearly_decrement(iter=it, n_iterations=n_iterations)

        for i, whale in enumerate(population):
            A = 2 * a * random.random() - a
            p = random.random()

            if p < 0.5:
                if abs(A) <= 1:
                    n_moves = random.randint(1, max(1, int(a * 10))) if a <= 0.3 else random.randint(1, 5)
                    candidate = discrete_shrinking_mechanism(
                        best_schedule=best.schedule,
                        obj_function=objective_function,
                        tasks=tasks,
                        setups=setups,
                        precedences=precedences,
                        energy_constraint=energy_constraint,
                        total_resource=total_resource,
                        n_moves=n_moves,
                    )
                else:
                    candidate = woa_random_explore(schedule=whale.schedule, tasks=tasks)
            else:
                candidate = discrete_spiral_update(schedule=whale.schedule, best_schedule=best.schedule)

           
            candidate_schedule = copy.deepcopy(candidate)
            prev_cost = objective_function(
                schedule=candidate_schedule,
                tasks=tasks,
                setups=setups,
                precedences=precedences,
                energy_constraint=energy_constraint,
                total_resource=total_resource,
            )["total_cost"]
            for _ in range(sa_local_iters):  # SA tinh chỉnh giúp WOA ở đây
                candidate_schedule = sa_exploit(
                    schedule=candidate_schedule,
                    tasks=tasks,
                    obj_function=objective_function,
                    precedences=precedences,
                    setups=setups,
                    energy_constraint=energy_constraint,
                    total_resource=total_resource,
                )
                new_cost = objective_function(
                    schedule=candidate_schedule,
                    tasks=tasks,
                    setups=setups,
                    precedences=precedences,
                    energy_constraint=energy_constraint,
                    total_resource=total_resource,
                )["total_cost"]
                if new_cost >= prev_cost:
                    break
                prev_cost = new_cost

            candidate_cost = prev_cost
            #tiến hành cập nhật cá voi nếu tìm được ứng viên tốt hơn
            if candidate_cost < whale.cost:
                whale.update(new_schedule=copy.deepcopy(candidate_schedule), new_cost=candidate_cost)

            if whale.cost < best.cost:
                best = copy.deepcopy(whale)

        if (it + 1) % max(1, n_iterations // 10) == 0:
            elapsed = time.time() - start
            print(f"iter {it+1}/{n_iterations} best_cost={best.cost:.3f} elapsed={elapsed:.2f}s")

    total_time = time.time() - start
    return best, total_time





