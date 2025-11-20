import math
import random
import copy
from typing import Dict, Any, Tuple, Set, List
from .strategies.sa_strategy import random_explore, exploit
from .utils.operations import generate_schedule, critical_task_move
from .utils.evaluation import objective_function
from .utils.entities import Schedule


class SimulatedAnnealing:
    def __init__(
        self,
        n_machines: int,
        tasks: Dict[int, Any],
        setups: Dict[Tuple[int, int], int],
        precedences: Dict[int, Set] = None,
        resource: Dict[str, Any] = None,
        energy_constraint: Dict[str, Any] = None,
        total_resource: Dict[str, Any] = None,
        n_iterations: int = 1000,
        initial_temp: float = 1000.0,
        guided_intensity: float = 0.05, #mức độ áp dụng GLS (ví dụ 0.01 thì GLS ảnh hưởng ít, gần như là SA, 0.05 là đang cân bằng, 0.2 lớn thì xài gls nhiều)
        choose: str = "default",
    ):
        self.tasks = tasks
        self.setups = setups
        self.n_machines = n_machines
        self.n_iterations = n_iterations
        self.precedences = precedences or {}
        self.resource = resource or {}
        self.energy_constraint = energy_constraint or {}
        self.total_resource = total_resource or None
        self.initial_temp = initial_temp
        self.best_schedule = None
        self.current_schedule = None
        self.history = []
        self.feature_stagnation = {
            "std_dev": 0,
            "energy_exceeds": 0,
        }
        self.scale_factor = math.log(len(tasks) + n_machines + 5)
        self.guided_intensity = guided_intensity #mức độ ảnh hưởng của GLS
        self.choose = choose

    def initialize_schedule(self):
        schedule = generate_schedule(tasks=self.tasks, n_machines=self.n_machines)
        cost = self.compute_cost(schedule)
        self.current_schedule = Schedule(schedule=schedule, cost=cost)
        self.best_schedule = Schedule(schedule=schedule, cost=cost)

    def optimize(self) -> Tuple[Schedule, List[Dict]]:
        self.initialize_schedule()
        TRIGGER_INTERVAL = max(1, int(self.n_iterations / 10))

        for iter in range(self.n_iterations):
            temperature = self.cooling_down(self.initial_temp, iter)
            progress = iter / self.n_iterations

            #Exploration / Exploitation
            if random.random() < 0.7 * (1 - progress):
                candidate_schedule = random_explore(
                    schedule=copy.deepcopy(self.current_schedule.schedule),
                    tasks=self.tasks,
                )
            else:
                candidate_schedule = exploit(
                    schedule=copy.deepcopy(self.current_schedule.schedule),
                    tasks=self.tasks,
                    obj_function=objective_function,
                    precedences=self.precedences,
                    setups=self.setups,
                    energy_constraint=self.energy_constraint,
                    total_resource=self.total_resource,
                )

            candidate_cost = self.compute_cost(candidate_schedule)
            features = candidate_cost["features"]

            thresholds = {"std_dev": 1.0, "energy_exceeds": 0} #set đánh giá std_dev và energy_exceeds
            for f in self.feature_stagnation:
                v = features.get(f, 0)
                thr = thresholds.get(f, 0)
                self.feature_stagnation[f] = self.feature_stagnation.get(f, 0) + 1 if v > thr else 0

            acp_sa = self.acceptance_probability(
                self.current_schedule.cost["total_cost"],
                candidate_cost["total_cost"],
                temperature,
            )
            acp_gls = self.acceptance_probability_gls(
                self.current_schedule.cost["total_cost"],
                candidate_cost["total_cost"],
                temperature,
                features,
            )
            accept_prob = acp_sa if self.choose == "default" else acp_gls

            #trigger là chu kỳ để kích hoạt target jump ở trên thiết lập là 1/10 số lần lặp
            #điều kiện là nó phải có ít nhất 1 vòng lặp và đến chu kỳ kích hoạt
            #std_dev và energy_stag để lưu lại độ trễ 
            if iter > 0 and iter % TRIGGER_INTERVAL == 0: 
                std_stag = self.feature_stagnation.get("std_dev", 0)
                energy_stag = self.feature_stagnation.get("energy_exceeds", 0)
                if std_stag > 0 and energy_stag > 0:
                    
                    candidate_schedule = critical_task_move(copy.deepcopy(self.current_schedule.schedule), self.tasks)
                    candidate_cost = self.compute_cost(candidate_schedule)
                   
                    for k in self.feature_stagnation:
                        self.feature_stagnation[k] = 0
                    accept_prob = 1.0

            if random.random() < accept_prob:
                self.current_schedule.update(
                    new_schedule=copy.deepcopy(candidate_schedule),
                    new_cost=candidate_cost,
                )

            if candidate_cost["total_cost"] < self.best_schedule.cost["total_cost"]:
                self.best_schedule.update(
                    new_schedule=copy.deepcopy(candidate_schedule),
                    new_cost=candidate_cost,
                )

            self.history.append({
                "iteration": iter,
                "iter_cost": self.current_schedule.cost,
                "best_cost": self.best_schedule.cost,
                "feature_stagnation": copy.deepcopy(self.feature_stagnation),
                "features": features,
                "acp_sa": acp_sa,
                "acp_gls": acp_gls,
                "accept_prob": accept_prob,
                "temperature": temperature,
            })

            if temperature < 1e-8:
                break

        return self.best_schedule, self.history    

    def acceptance_probability(
        self, old_cost: float, new_cost: float, temperature: float
    ):
        if new_cost < old_cost:
            return 1.0
        if temperature <= 0:
            return 0.0
        try:
            return math.exp(-(new_cost - old_cost) / temperature)
        except OverflowError:
            return 0.0
        
    def cooling_down(self, initial_temp: float, iteration: int, alpha: float = 0.995):
        return initial_temp * (alpha**iteration)
    


    #tính cost của lịch và các features
    def compute_cost(self, schedule: Dict[int, List[int]]) -> Dict[str, float]:
        obj = objective_function(
            schedule=schedule,
            tasks=self.tasks,
            setups=self.setups,
            precedences=self.precedences,
            energy_constraint=self.energy_constraint,
            total_resource=self.total_resource,
        )
        # features are penalties / std_dev etc. exclude makespan
        features = {k: v for k, v in obj.items() if k not in ("total_cost", "makespan")}
        return {"total_cost": obj["total_cost"], "features": features}

    def acceptance_probability_gls(
        self, old_cost: float, new_cost: float, temperature: float, features: Dict[str, float]
    ) -> float:
        if new_cost < old_cost:
            return 1.0
        if temperature <= 0:
            return 0.0
        #tính penalty cho gls
        std_dev_val = float(features.get("std_dev", 0))
        energy_val = float(features.get("energy_exceeds", 0))
        feature_penalty = std_dev_val + energy_val

        gls_penalty = self.guided_intensity * feature_penalty * self.scale_factor

        adjusted_delta = (new_cost - old_cost) + gls_penalty

        try:
            return math.exp(-adjusted_delta / temperature)
        except OverflowError:
            return 0.0

 


    
