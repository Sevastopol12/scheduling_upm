import math
import random
import copy
from typing import Dict, Any, Tuple, Set, List
from .strategies.sa_strategy import random_explore, transition, exploit
from .utils.operations import generate_schedule
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
        guided_intensity: float = 0.05, #mức độ áp dụng GLS
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
        self.guided_intensity = guided_intensity 

    def initialize_schedule(self):
        schedule = generate_schedule(tasks=self.tasks, n_machines=self.n_machines)
        cost = objective_function(
            schedule=schedule,
            tasks=self.tasks,
            setups=self.setups,
            precedences=self.precedences,
        )

        self.current_schedule = Schedule(schedule=schedule, cost=cost)
        self.best_schedule = Schedule(schedule=schedule, cost=cost)

    def optimize(self) -> Tuple[Schedule, List[Dict]]:
        self.initialize_schedule()

        feature_penalties = {'imbalance': 0, 'setup': 0, 'idle': 0, 'concentration': 0}
        no_improve = 0 #đếm số vòng không cải thiện
        n_tasks = len(self.tasks)
        update_freq = max(10, self.n_iterations // 100) # tần suất cập nhật penalty
        penalty_inc = max(0.1, n_tasks / 100.0) #tăng penalty khi phát hiện đặc trưng xấu

        for iter in range(self.n_iterations):
            temperature: float = self.cooling_down(
                initial_temp=self.initial_temp, iteration=iter
            )

            # Generate new solution
            probability: float = random.random()
            # Keep track of iteration progess, affect adjusting behavior
            progress: float = iter / self.n_iterations

            # Explore
            if probability < 0.5 * (1 - progress):
                candidate_schedule = random_explore(
                    schedule=self.current_schedule.schedule, tasks=self.tasks
                )
            # Transition
            elif probability < 0.9 * (1 - progress):
                candidate_schedule = transition(
                    schedule=self.current_schedule.schedule, tasks=self.tasks
                )
            # Exploit
            else:
                candidate_schedule = exploit(
                    schedule=self.current_schedule.schedule,
                    tasks=self.tasks,
                    obj_function=objective_function,
                    **{
                        "precedences": self.precedences,
                        "setups": self.setups,
                        "energy_constraint": self.energy_constraint,
                        "total_resource": self.total_resource,
                    },
                )

            candidate_cost = objective_function(
                schedule=candidate_schedule,
                tasks=self.tasks,
                setups=self.setups,
                precedences=self.precedences,
                energy_constraint=self.energy_constraint,
                total_resource=self.total_resource,
            )

            acp: float = self.acceptance_probability_guided(
                current_cost=self.current_schedule.cost,
                new_cost=candidate_cost,
                temperature=temperature,
                candidate_schedule=candidate_schedule,
                progress=progress,
                feature_penalties=feature_penalties,
            )

            if random.random() < acp:
                self.current_schedule.update(
                    new_schedule=copy.deepcopy(candidate_schedule),
                    new_cost=candidate_cost,
                )

            if candidate_cost < self.best_schedule.cost:
                self.best_schedule.update(
                    new_schedule=copy.deepcopy(candidate_schedule),
                    new_cost=candidate_cost,
                )
                no_improve = 0 #đếm số vòng lặp không cải thiện
            else:
                no_improve += 1 #nếu không cải thiện thì tăng biến đếm số vòng không cải thiện
            #khi thuật toán không cải thiện trong một số vòng lặp nhất định, ta sẽ cập nhật penalty
            if no_improve > 0 and no_improve % update_freq == 0:
                features = self._quick_features(self.current_schedule.schedule) #xác định đặc trưng hiện tại

                worst_feature = None #tìm đặc trưng xấu nhất
                max_ratio = -1 #lưu giá trị tệ nhất
                for feat, util in features.items(): #duyệt qua các đặc trưng
                    if util > 0: #chỉ xét các đặc trưng có giá trị sử dụng > 0
                        ratio = util / (1 + feature_penalties[feat]) #tính tỉ lệ theo công thức của GLS
                        if ratio > max_ratio: 
                            max_ratio = ratio #câp nhật giá trị tệ nhất
                            worst_feature = feat #lưu đặc trưng tệ nhất
                #mục đích là tìm đặc trưng xấu nhất mà chưa penalty nhiều
                #Tăng penalty cho đặc trưng đó
                if worst_feature:
                    feature_penalties[worst_feature] += penalty_inc 

            self.history.append(
                {
                    "iteration": iter,
                    "iter_cost": self.current_schedule.cost,
                    "iter_schedule": self.current_schedule.schedule,
                    "best_schedule": self.best_schedule.schedule,
                    "best_cost": self.best_schedule.cost,
                    "penalties": dict(feature_penalties),
                    "no_improve": no_improve,
                }
            )

            # early stop when temperature got too small
            if temperature < 1e-8:
                break

        return self.best_schedule, self.history

    def acceptance_probability(
        self, old_cost: float, new_cost: float, temperature: float
    ):
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

    def cooling_down(self, initial_temp: float, iteration: int, alpha: float = 0.995):
        """Exponential cooling"""
        return initial_temp * (alpha**iteration)

    def _quick_features(self, schedule: Dict[int, List[int]]) -> Dict[str, float]:
        n_tasks = len(self.tasks) #lấy tổng số task
        ideal_load = n_tasks / self.n_machines #tải lý tưởng trên mỗi máy
         
        imbalance = sum(abs(len(schedule[m]) - ideal_load) for m in schedule) / (n_tasks + 1)  #tính mất cân bằng bằng cách lấy tổng sai lệch tuyệt đối so với tải lý tưởng, chuẩn hóa bằng n_tasks + 1
        
        total_setup = sum( 
            self.setups.get((schedule[m][i-1], schedule[m][i]), 0) 
            for m in schedule for i in range(1, len(schedule[m]))
        ) #tính tổng thời gian thiết lập trong lịch trình hiện tại
        max_setup = max(self.setups.values()) * n_tasks if self.setups else 1 #tính giá trị chuẩn hóa, setup max nhân số task
        setup_ratio = total_setup / max_setup if max_setup > 0 else 0 #tính tỷ lệ thiết lập chuẩn hóa, chuẩn hóa về [0, 1], càng lớn càng tốn chi phí setup
        
        idle = sum(1 for tasks in schedule.values() if len(tasks) == 0) / self.n_machines 
        
        max_len = max(len(tasks) for tasks in schedule.values()) #tính số lượng task nhiều nhất trong 1 máy
        avg_len = n_tasks / self.n_machines #số task trung bình trên mỗi máy
        concentration = (max_len / avg_len - 1) if avg_len > 0 else 0 #nếu 1 máy quá nhiều task so với trung bình thì concentration sẽ lớn
        
        return {
            'imbalance': imbalance,#cân bằng tải
            'setup': setup_ratio, #chi phí setup
            'idle': idle, #tỷ lệ máy rảnh
            'concentration': max(0, concentration), #tập trung task
        }

    def acceptance_probability_guided(
        self,
        current_cost: float, #chi phí hiện tại
        new_cost: float, #chi phí mới
        temperature: float, #nhiệt độ
        candidate_schedule: Dict[int, List[int]], 
        progress: float, #tiến độ
        feature_penalties: Dict[str, float], #mức phạt GLS cho từng feature
    ) -> float:
        
        if new_cost < current_cost:
            return 1.0
        if temperature <= 0:
            return 0.0
        
        delta = new_cost - current_cost #nếu delta lớn hơn 0 nghĩa là giải pháp mới tệ hơn
        
        features = self._quick_features(candidate_schedule) #tính các đặc trưng của lịch trình
        
        feat_sum = sum(abs(v) for v in features.values()) #tổng tuyệt đối các đặc trưng để chuẩn hóa
        #công thức trọng số 
        if feat_sum > 0: 
            penalty = sum((v / feat_sum) * feature_penalties.get(f, 0) for f, v in features.items()) #tính penalty tổng hợp dựa trên tỉ trọng của từng đặc trưng nhân với mức phạt áp dụng cho đặc trưng đó
        else:
            penalty = 0
        
        adaptive_lambda = min(1.0, self.guided_intensity * (0.5 + 0.5 * progress)) #progress càng cao thì lambda càng lớn, tức là càng về sau càng áp dụng mạnh GLS
        
        n_tasks = len(self.tasks) 
        scale = max(1.0, math.log(n_tasks * self.n_machines + 1)) #scale theo kích thước bài toán để tránh giá trị quá lớn
        
        augmented = delta * (1 + adaptive_lambda * penalty) #nếu penalty lớn thì xác suất chấp nhận càng nhỏ
        try:
            return min(1.0, math.exp(-augmented / (temperature * scale)))
        except OverflowError:
            return 0.0       