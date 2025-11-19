import math
import random
import copy
from typing import Dict, Any, Tuple, Set, List
from .strategies.sa_strategy import random_explore, exploit
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
        guided_intensity: float = 0.05, #mức độ áp dụng GLS (ví dụ 0.01 thì GLS ảnh hưởng ít, gần như là SA, 0.05 là đang cân bằng, 0.2 lớn thì xài gls nhiều)
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
        self.feature_stagnation = {"idle": 0, "concentration": 0} #dùng để đếm số lần liên tiếp feature xấu
        self.scale_factor = math.log(len(tasks) + n_machines + 5) #hệ số chuẩn hóa penalty theo kích thước bài toán, penalty sẽ tỉ lệ thuận với kích thước bài toán
        self.guided_intensity = guided_intensity #mức độ ảnh hưởng của GLS
        

    def initialize_schedule(self):
        schedule = generate_schedule(tasks=self.tasks, n_machines=self.n_machines)
        cost = self.compute_cost(schedule)
        self.current_schedule = Schedule(schedule=schedule, cost=cost)
        self.best_schedule = Schedule(schedule=schedule, cost=cost)

    def optimize(self) -> Tuple[Schedule, List[Dict]]:
        self.initialize_schedule()
        MAX_STAGNATION = max(20, int(0.1 * self.n_iterations))

        for iter in range(self.n_iterations):
            temperature = self.cooling_down(self.initial_temp, iter)
            progress = iter / self.n_iterations

            # --- Exploration / Exploitation ---
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

            #stagnation tracking
            for f, v in features.items(): #f là tên feature, v là giá trị feature
                threshold = 0.2 if f == "idle" else 0.3 #ngưỡng vi phạm  
                self.feature_stagnation[f] = self.feature_stagnation[f] + 1 if v > threshold else 0 #đếm số lần vi phạm liên tiếp

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

            weight_gls = 0.3 + 0.5 * progress  # 0.3 -> 0.8
            weight_sa = 1.0 - weight_gls

            accept_prob = weight_sa * acp_sa + weight_gls * acp_gls

            #escape from infeasible zone
            worst_feature = max(self.feature_stagnation, key=self.feature_stagnation.get) #tìm feature xấu liên tục
            if self.feature_stagnation[worst_feature] > MAX_STAGNATION: #nếu vượt ngưỡng stagnation
                if random.random() < 0.7: #70% nhảy có mục tiêu để sửa feature xấu
                    candidate_schedule = self._targeted_jump( 
                        self.current_schedule.schedule, worst_feature 
                    )
                else:
                    candidate_schedule = generate_schedule(self.tasks, self.n_machines) #30% tạo lịch mới hoàn toàn

                candidate_cost = self.compute_cost(candidate_schedule)
                self.feature_stagnation = {"idle": 0, "concentration": 0}
                accept_prob = 1.0  #chấp nhận để thoang khỏi vùng kẹt
 
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
                "weight_sa": weight_sa,
                "weight_gls": weight_gls,
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
    
    def _check_idle_machines(self, schedule: Dict[int, List[int]]) -> float: #tỉ lệ máy rảnh
        idle_count = sum(1 for tasks in schedule.values() if len(tasks) == 0) #lấy danh sách task của các máy để kiểm tra xem máy có rảnh không để đếm số máy rảnh
        return idle_count / self.n_machines #tỉ lệ máy rãnh, idle càng thấp thì càng tốt (tức là các máy đều có việc để làm)

    def _check_concentration(self, schedule: Dict[int, List[int]]) -> float: 
        lengths = [len(tasks) for tasks in schedule.values()] #tạo list chứa số lượng task của từng máy
        if not lengths or max(lengths) == 0: #kiểm tra danh sách rỗng hoặc tất cả máy đều không có task
            return 0.0 #nếu đúng trả về 0 tức là không có concentration issue
        avg_length = sum(lengths) / len(lengths) #tính trung bình số task trên mỗi máy
        max_length = max(lengths) #tìm máy có nhiều task nhất
        ratio = max_length / avg_length if avg_length > 0 else 0 #tính tỉ lệ giữa máy nhiều task nhất và trung bình
        return max(0.0, (ratio - 1.5) / 2.0) #chuẩn hóa tỉ lệ để đưa về khoảng [0, 1], concentration càng thấp thì càng tốt có nghĩa là đang phân bổ đều

    def _compute_features(self, schedule: Dict[int, List[int]]) -> Dict[str, float]:
        return {
            "idle": self._check_idle_machines(schedule),
            "concentration": self._check_concentration(schedule),
        } #trả về dict các features 

    #tính cost của lịch và các features
    def compute_cost(self, schedule: Dict[int, List[int]]) -> Dict[str, float]: 
        base_cost = objective_function(
            schedule=schedule,
            tasks=self.tasks,
            setups=self.setups,
            precedences=self.precedences,
            energy_constraint=self.energy_constraint,
            total_resource=self.total_resource
        )
        return {
        "total_cost": base_cost,  # base_cost là int
        "features": self._compute_features(schedule)
    }

    #thực hiện nhảy có mục tiêu để cải thiện feature xấu
    def _targeted_jump(self, schedule: Dict[int, List[int]], worst_feature: str):
        schedule = copy.deepcopy(schedule)

        #nhiều máy rảnh liên tục thì phân bổ lại task
        if worst_feature == "idle":
            idle_machines = [m for m, t in schedule.items() if len(t) == 0]
            busy_machines = [m for m, t in schedule.items() if len(t) > 1]
            for idle in idle_machines: 
                if busy_machines: 
                    source = max(busy_machines, key=lambda m: len(schedule[m]))
                    task = schedule[source].pop()
                    schedule[idle].append(task)
                    if len(schedule[source]) <= 1:
                        busy_machines.remove(source)
            return schedule

        #một máy quá tải so với các máy khác thì cân bằng lại
        if worst_feature == "concentration":
            lengths = {m: len(t) for m, t in schedule.items()}
            most_loaded = max(lengths, key=lengths.get)
            least_loaded = min(lengths, key=lengths.get)
            if lengths[most_loaded] - lengths[least_loaded] > 1:
                task = schedule[most_loaded].pop()
                schedule[least_loaded].append(task)
            return schedule
        
        #mặc định random explore nếu không xác định được feature idle hoặc concentration
        return random_explore(schedule=schedule, tasks=self.tasks)

    def acceptance_probability_gls(
        self, old_cost: float, new_cost: float, temperature: float, features: Dict[str, float]
    ) -> float:
        if new_cost < old_cost:
            return 1.0
        if temperature <= 0:
            return 0.0

        #tính penalty từ features
        feature_penalty = features.get("idle", 0) + features.get("concentration", 0) 
        
        #scale penalty để có tác động rõ rệt
        gls_penalty = self.guided_intensity * feature_penalty * self.scale_factor * 100
    
        #features xấu -> penalty cao -> adjusted_delta lớn -> xác suất thấp
        #features tốt → penalty = 0 → delta không đổi → xác suất cao hơn
        adjusted_delta = (new_cost - old_cost) + gls_penalty
        
        try:
            return math.exp(-adjusted_delta / temperature)
        except OverflowError:
            return 0.0

 


    
