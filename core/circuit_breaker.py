import time
import threading
import enum
import random
from typing import Optional, List, Dict, Callable


class CircuitState(enum.Enum):
    """
    熔断器状态
    """
    CLOSED = "closed"          # 正常状态，允许请求
    OPEN = "open"             # 熔断状态，拒绝所有请求
    HALF_OPEN = "half_open"   # 半开状态，允许少量试探请求
    RECOVERING = "recovering" # 恢复中，逐渐恢复流量


class CircuitBreaker:
    """
    风控熔断器 - 防止被封禁
    
    策略:
    1. 连续失败达到阈值时，进入OPEN状态
    2. OPEN状态下，所有请求被拒绝
    3. 一段时间后进入HALF_OPEN状态
    4. HALF_OPEN状态下，允许少量试探请求
    5. 试探成功则进入RECOVERING，逐步恢复流量
    6. 试探失败则回到OPEN状态
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_requests: int = 2,
        recovery_phase_duration: float = 60.0,
        max_recovery_factor: float = 1.0,
        instance_id: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests
        self.recovery_phase_duration = recovery_phase_duration
        self.max_recovery_factor = max_recovery_factor
        self.instance_id = instance_id
        
        # 内部状态
        self._state = CircuitState.CLOSED
        self._state_lock = threading.Lock()
        
        # 失败计数
        self._failure_count = 0
        self._success_count = 0
        self._half_open_requests = 0
        
        # 时间戳
        self._last_failure_time = 0
        self._last_success_time = 0
        self._state_change_time = time.time()
        
        # 恢复因子 (0.1 - 1.0)
        self._recovery_factor = 0.1
        
        # 状态历史
        self._state_history: List[Dict] = []
        self._max_history = 100
        
        # 回调函数
        self._on_state_change: Optional[Callable] = None
        self._on_block: Optional[Callable] = None
        self._on_recover: Optional[Callable] = None
    
    def can_execute(self) -> bool:
        """
        判断是否允许执行请求
        """
        with self._state_lock:
            self._check_state_transitions()
            
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_requests < self.half_open_max_requests:
                    self._half_open_requests += 1
                    return True
                return False
            
            if self._state == CircuitState.RECOVERING:
                # 根据恢复因子，概率性允许请求
                return random.random() < self._recovery_factor
            
            # OPEN状态 - 拒绝所有请求
            return False
    
    def _check_state_transitions(self):
        """
        检查状态转换条件
        """
        now = time.time()
        
        if self._state == CircuitState.OPEN:
            # 检查是否到达恢复超时时间
            if now - self._state_change_time >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                self._half_open_requests = 0
                self._success_count = 0
                
        elif self._state == CircuitState.HALF_OPEN:
            # 检查半开状态是否超时
            if now - self._state_change_time >= self.recovery_timeout:
                # 超时则重新进入熔断
                self._transition_to(CircuitState.OPEN)
                
        elif self._state == CircuitState.RECOVERING:
            # 逐步恢复
            elapsed = now - self._state_change_time
            progress = min(1.0, elapsed / self.recovery_phase_duration)
            self._recovery_factor = 0.1 + (progress * 0.9)  # 从0.1增长到1.0
            
            if progress >= 1.0:
                self._transition_to(CircuitState.CLOSED)
                self._recovery_factor = self.max_recovery_factor
    
    def _transition_to(self, new_state: CircuitState):
        """
        状态转换
        """
        old_state = self._state
        self._state = new_state
        self._state_change_time = time.time()
        
        # 记录历史
        self._state_history.append({
            "from": old_state.value,
            "to": new_state.value,
            "time": self._state_change_time,
        })
        
        # 触发回调
        if self._on_state_change:
            self._on_state_change(old_state, new_state)
        
        if new_state == CircuitState.OPEN and self._on_block:
            self._on_block()
        
        if new_state == CircuitState.CLOSED and self._on_recover:
            self._on_recover()
    
    def record_success(self):
        """
        记录请求成功
        """
        with self._state_lock:
            self._check_state_transitions()
            
            self._last_success_time = time.time()
            self._success_count += 1
            
            if self._state == CircuitState.HALF_OPEN:
                # 半开状态下成功，进入恢复状态
                if self._success_count >= self.half_open_max_requests:
                    self._transition_to(CircuitState.RECOVERING)
                    self._recovery_factor = 0.1
                    
            elif self._state == CircuitState.RECOVERING:
                # 恢复状态下成功，逐步提高恢复因子
                self._recovery_factor = min(
                    self.max_recovery_factor,
                    self._recovery_factor + 0.1
                )
                
            elif self._state == CircuitState.CLOSED:
                # 正常状态下重置失败计数
                self._failure_count = 0
    
    def record_failure(self, status_code: int = 0):
        """
        记录请求失败
        """
        with self._state_lock:
            self._check_state_transitions()
            
            self._last_failure_time = time.time()
            self._failure_count += 1
            
            # 风控相关的状态码
            risk_codes = {403, 429, 456}
            is_risk_code = status_code in risk_codes
            
            if self._state == CircuitState.HALF_OPEN:
                # 半开状态下失败，立即熔断
                self._transition_to(CircuitState.OPEN)
                
            elif self._state == CircuitState.RECOVERING:
                # 恢复状态下失败，回到熔断
                self._transition_to(CircuitState.OPEN)
                
            elif self._state == CircuitState.CLOSED:
                # 正常状态下检查是否达到阈值
                threshold = self.failure_threshold
                if is_risk_code:
                    threshold = min(3, self.failure_threshold)  # 风控错误更快触发熔断
                
                if self._failure_count >= threshold:
                    self._transition_to(CircuitState.OPEN)
    
    def set_callback(
        self,
        on_state_change: Optional[Callable] = None,
        on_block: Optional[Callable] = None,
        on_recover: Optional[Callable] = None,
    ):
        """
        设置回调函数
        """
        self._on_state_change = on_state_change
        self._on_block = on_block
        self._on_recover = on_recover
    
    def get_state(self) -> CircuitState:
        """
        获取当前状态
        """
        with self._state_lock:
            return self._state
    
    def get_status(self) -> Dict:
        """
        获取完整状态信息
        """
        with self._state_lock:
            self._check_state_transitions()
            
            now = time.time()
            time_in_state = now - self._state_change_time
            
            return {
                "instance_id": self.instance_id,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "recovery_factor": self._recovery_factor,
                "time_in_state": round(time_in_state, 1),
                "last_failure": self._last_failure_time,
                "last_success": self._last_success_time,
                "can_execute": self._state != CircuitState.OPEN,
            }
    
    def reset(self):
        """
        重置熔断器
        """
        with self._state_lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_requests = 0
            self._state_change_time = time.time()
            self._recovery_factor = self.max_recovery_factor
    
    def get_history(self) -> List[Dict]:
        """
        获取状态变更历史
        """
        with self._state_lock:
            return list(self._state_history)


class MultiInstanceCircuitManager:
    """
    多实例熔断器管理器
    
    协调多个实例的熔断状态
    - 某个实例触发熔断时，通知其他实例
    - 所有实例都恢复后，统一解除限制
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        self._global_blocked = False
        self._global_block_until = 0
        self._blocked_instances: List[str] = []
    
    def create_breaker(
        self,
        instance_id: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        """
        创建实例级别的熔断器
        """
        with self._lock:
            breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                instance_id=instance_id,
            )
            
            # 设置回调
            breaker.set_callback(
                on_block=lambda: self._on_instance_blocked(instance_id),
                on_recover=lambda: self._on_instance_recovered(instance_id),
            )
            
            self._breakers[instance_id] = breaker
            return breaker
    
    def _on_instance_blocked(self, instance_id: str):
        """
        实例被封禁回调
        """
        with self._lock:
            if instance_id not in self._blocked_instances:
                self._blocked_instances.append(instance_id)
            
            # 如果超过一半实例被封禁，触发全局熔断
            if len(self._blocked_instances) >= len(self._breakers) // 2:
                self._global_blocked = True
                self._global_block_until = time.time() + 120  # 全局封禁2分钟
    
    def _on_instance_recovered(self, instance_id: str):
        """
        实例恢复回调
        """
        with self._lock:
            if instance_id in self._blocked_instances:
                self._blocked_instances.remove(instance_id)
            
            # 如果没有实例被封禁，解除全局熔断
            if not self._blocked_instances:
                self._global_blocked = False
                self._global_block_until = 0
    
    def can_execute(self, instance_id: str) -> bool:
        """
        检查实例是否可以执行
        """
        with self._lock:
            # 检查全局熔断
            if self._global_blocked:
                if time.time() < self._global_block_until:
                    return False
                else:
                    self._global_blocked = False
            
            # 检查实例级熔断
            breaker = self._breakers.get(instance_id)
            if breaker:
                return breaker.can_execute()
            return True
    
    def record_success(self, instance_id: str):
        """
        记录实例请求成功
        """
        with self._lock:
            breaker = self._breakers.get(instance_id)
            if breaker:
                breaker.record_success()
    
    def record_failure(self, instance_id: str, status_code: int = 0):
        """
        记录实例请求失败
        """
        with self._lock:
            breaker = self._breakers.get(instance_id)
            if breaker:
                breaker.record_failure(status_code)
    
    def get_all_status(self) -> Dict[str, Dict]:
        """
        获取所有熔断器状态
        """
        with self._lock:
            result = {
                "global_blocked": self._global_blocked,
                "global_block_until": self._global_block_until,
                "blocked_instances": self._blocked_instances,
                "instances": {},
            }
            for inst_id, breaker in self._breakers.items():
                result["instances"][inst_id] = breaker.get_status()
            return result
    
    def remove_breaker(self, instance_id: str):
        """
        移除熔断器
        """
        with self._lock:
            if instance_id in self._breakers:
                del self._breakers[instance_id]
            if instance_id in self._blocked_instances:
                self._blocked_instances.remove(instance_id)
    
    def reset_all(self):
        """
        重置所有熔断器
        """
        with self._lock:
            self._global_blocked = False
            self._global_block_until = 0
            self._blocked_instances.clear()
            for breaker in self._breakers.values():
                breaker.reset()
