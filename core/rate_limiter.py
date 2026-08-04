import time
import threading
import random
from typing import Optional, List, Dict
from collections import deque


class RateLimiter:
    """
    令牌桶限流器 - 支持多实例全局协调
    
    特性:
    - 基于时间窗口的请求频率控制
    - 支持突发流量限制
    - 实例级别的请求队列管理
    - 动态调整速率
    """
    
    def __init__(
        self,
        max_requests_per_minute: int = 30,
        burst_size: int = 5,
        min_interval_ms: int = 2000,
        instance_id: str = "default",
    ):
        self.max_requests_per_minute = max_requests_per_minute
        self.burst_size = burst_size
        self.min_interval_ms = min_interval_ms
        self.instance_id = instance_id
        
        self._request_timestamps: deque = deque()
        self._semaphore = threading.Semaphore(1)
        
        # 全局请求计数
        self._total_requests = 0
        self._failed_requests = 0
        self._rate_limited_requests = 0
        
        # 动态速率调整
        self._current_rate = max_requests_per_minute
        self._rate_adjustment_factor = 1.0
        
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取请求令牌，返回是否允许发送请求
        """
        with self._semaphore:
            now = time.time()
            window_start = now - 60  # 1分钟窗口
            
            # 清理过期的请求记录
            while self._request_timestamps and self._request_timestamps[0] < window_start:
                self._request_timestamps.popleft()
            
            # 检查每分钟请求数限制
            current_count = len(self._request_timestamps)
            effective_rate = int(self._current_rate * self._rate_adjustment_factor)
            
            if current_count >= effective_rate:
                # 达到速率限制，计算等待时间
                if self._request_timestamps:
                    oldest = self._request_timestamps[0]
                    wait_time = (oldest + 60) - now
                    wait_time += random.uniform(0.5, 2.0)  # 添加随机抖动
                    self._rate_limited_requests += 1
                    return False
                return False
            
            # 检查最小间隔时间
            if self._request_timestamps:
                last_request = self._request_timestamps[-1]
                elapsed_ms = (now - last_request) * 1000
                if elapsed_ms < self.min_interval_ms:
                    # 间隔太短，需要等待
                    wait_time = (self.min_interval_ms - elapsed_ms) / 1000
                    wait_time += random.uniform(0.1, 0.5)
                    self._rate_limited_requests += 1
                    return False
            
            # 检查突发限制
            if len(self._request_timestamps) >= self.burst_size:
                # 突发请求过多
                recent_requests = list(self._request_timestamps)[-self.burst_size:]
                time_span = recent_requests[-1] - recent_requests[0]
                if time_span < 10:  # 10秒内超过burst_size个请求
                    self._rate_limited_requests += 1
                    return False
            
            # 允许请求
            self._request_timestamps.append(now)
            self._total_requests += 1
            return True
    
    def wait_for_token(self, max_wait: float = 30.0) -> bool:
        """
        等待获取令牌，带超时
        """
        start_time = time.time()
        check_interval = 0.5
        
        while time.time() - start_time < max_wait:
            if self.acquire():
                return True
            time.sleep(check_interval)
            # 渐进式增加检查间隔
            check_interval = min(check_interval * 1.5, 2.0)
        
        return False
    
    def record_failure(self):
        """
        记录请求失败，可能触发速率降低
        """
        with self._semaphore:
            self._failed_requests += 1
            # 如果失败率过高，自动降低速率
            total = self._total_requests + self._failed_requests
            if total > 20:
                failure_rate = self._failed_requests / total
                if failure_rate > 0.3:  # 失败率超过30%
                    self._rate_adjustment_factor = max(0.3, self._rate_adjustment_factor * 0.8)
                    self._failed_requests = 0
                    self._total_requests = 0
    
    def record_success(self):
        """
        记录请求成功，可能触发速率恢复
        """
        with self._semaphore:
            self._failed_requests = max(0, self._failed_requests - 1)
            # 成功时缓慢恢复速率
            if self._rate_adjustment_factor < 1.0:
                self._rate_adjustment_factor = min(1.0, self._rate_adjustment_factor + 0.05)
    
    def get_stats(self) -> Dict:
        """
        获取限流器统计信息
        """
        with self._semaphore:
            now = time.time()
            window_start = now - 60
            recent_count = sum(1 for t in self._request_timestamps if t >= window_start)
            
            return {
                "instance_id": self.instance_id,
                "current_rate": self._current_rate,
                "adjusted_rate": int(self._current_rate * self._rate_adjustment_factor),
                "rate_factor": self._rate_adjustment_factor,
                "recent_requests": recent_count,
                "total_requests": self._total_requests,
                "failed_requests": self._failed_requests,
                "rate_limited_requests": self._rate_limited_requests,
            }
    
    def reset(self):
        """
        重置限流器状态
        """
        with self._semaphore:
            self._request_timestamps.clear()
            self._total_requests = 0
            self._failed_requests = 0
            self._rate_limited_requests = 0
            self._rate_adjustment_factor = 1.0
    
    def set_rate(self, rate_per_minute: int):
        """
        动态调整速率限制
        """
        with self._semaphore:
            self._current_rate = rate_per_minute


class GlobalRateCoordinator:
    """
    全局速率协调器 - 管理多个实例的请求速率
    
    确保所有实例组合起来不会触发风控
    """
    
    def __init__(self, total_max_requests_per_minute: int = 60):
        self.total_max_requests = total_max_requests_per_minute
        self._instances: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()
        self._global_timestamps: deque = deque()
        
    def create_instance(self, instance_id: str) -> RateLimiter:
        """
        创建实例级别的限流器
        """
        with self._lock:
            # 计算每个实例的速率配额
            num_instances = len(self._instances) + 1
            per_instance_rate = max(5, self.total_max_requests // num_instances)
            
            limiter = RateLimiter(
                max_requests_per_minute=per_instance_rate,
                min_interval_ms=max(1000, 3000 - num_instances * 200),
                instance_id=instance_id,
            )
            self._instances[instance_id] = limiter
            
            # 重新分配所有实例的速率
            self._redistribute_rates()
            
            return limiter
    
    def remove_instance(self, instance_id: str):
        """
        移除实例
        """
        with self._lock:
            if instance_id in self._instances:
                del self._instances[instance_id]
                self._redistribute_rates()
    
    def _redistribute_rates(self):
        """
        重新分配速率配额
        """
        num_instances = len(self._instances)
        if num_instances == 0:
            return
        
        per_instance_rate = max(5, self.total_max_requests // num_instances)
        min_interval = max(1000, 3000 - num_instances * 200)
        
        for limiter in self._instances.values():
            limiter.set_rate(per_instance_rate)
            limiter.min_interval_ms = min_interval
    
    def global_acquire(self) -> bool:
        """
        全局令牌检查
        """
        with self._lock:
            now = time.time()
            window_start = now - 60
            
            # 清理过期记录
            while self._global_timestamps and self._global_timestamps[0] < window_start:
                self._global_timestamps.popleft()
            
            if len(self._global_timestamps) >= self.total_max_requests:
                return False
            
            # 添加随机抖动，避免所有实例同时请求
            self._global_timestamps.append(now + random.uniform(-0.5, 0.5))
            return True
    
    def get_all_stats(self) -> List[Dict]:
        """
        获取所有实例的统计信息
        """
        with self._lock:
            return [limiter.get_stats() for limiter in self._instances.values()]
    
    def get_total_stats(self) -> Dict:
        """
        获取全局统计
        """
        with self._lock:
            total_requests = sum(s.get("total_requests", 0) for s in self.get_all_stats())
            total_failed = sum(s.get("failed_requests", 0) for s in self.get_all_stats())
            
            return {
                "active_instances": len(self._instances),
                "total_requests": total_requests,
                "total_failed": total_failed,
                "global_rate_limit": self.total_max_requests,
            }
