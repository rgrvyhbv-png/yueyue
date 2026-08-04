import uuid
import time
import threading
import random
import os
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

import requests


@dataclass
class InstanceEnvironment:
    """
    实例环境 - 每个实例的独立状态
    """
    instance_id: str
    created_at: float = field(default_factory=time.time)
    
    # 独立的session
    session: Optional[requests.Session] = None
    
    # 独立的cookie
    cookies: Dict[str, str] = field(default_factory=dict)
    
    # 设备指纹缓存
    device_info: Optional[Any] = None
    device_fingerprint: str = ""
    
    # 独立的visitor_id
    visitor_id: str = ""
    
    # 代理配置
    proxy_host: str = ""
    proxy_port: int = 0
    proxy_username: str = ""
    proxy_password: str = ""
    
    # 请求历史
    request_count: int = 0
    failed_count: int = 0
    
    # IP轮换
    current_ip: str = ""
    ip_rotation_count: int = 0
    
    # 流量统计
    bytes_sent: int = 0
    bytes_received: int = 0
    
    # 风控状态
    blocked: bool = False
    block_until: float = 0
    
    def is_blocked(self) -> bool:
        """检查是否被封禁"""
        if not self.blocked:
            return False
        if time.time() > self.block_until:
            self.blocked = False
            return False
        return True
    
    def block(self, duration_seconds: int = 300):
        """封禁实例"""
        self.blocked = True
        self.block_until = time.time() + duration_seconds
    
    def unblock(self):
        """解封实例"""
        self.blocked = False
        self.block_until = 0


class EnvironmentIsolation:
    """
    环境隔离管理器 - 确保每个实例有独立的运行环境
    
    隔离内容:
    - 独立的Session和Cookie
    - 独立的Visitor ID
    - 独立的代理连接
    - 独立的设备指纹缓存
    - 独立的请求历史
    """
    
    def __init__(self):
        self._environments: Dict[str, InstanceEnvironment] = {}
        self._lock = threading.Lock()
        self._proxy_pool: List[Dict[str, Any]] = []
        self._current_proxy_index = 0
        
    def create_environment(
        self,
        instance_id: Optional[str] = None,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> InstanceEnvironment:
        """
        创建独立的实例环境
        """
        with self._lock:
            if instance_id is None:
                instance_id = f"inst_{uuid.uuid4().hex[:8]}"
            
            # 创建独立的session
            session = requests.Session()
            self._configure_session(session, proxy_config)
            
            # 生成独立的visitor_id
            visitor_id = self._generate_visitor_id()
            
            # 分配代理（轮询方式）
            if proxy_config is None and self._proxy_pool:
                proxy_config = self._get_next_proxy()
            
            env = InstanceEnvironment(
                instance_id=instance_id,
                session=session,
                visitor_id=visitor_id,
            )
            
            if proxy_config:
                env.proxy_host = proxy_config.get("host", "")
                env.proxy_port = int(proxy_config.get("port", 7878))
                env.proxy_username = proxy_config.get("username", "")
                env.proxy_password = proxy_config.get("password", "")
            
            self._environments[instance_id] = env
            return env
    
    def _configure_session(self, session: requests.Session, proxy_config: Optional[Dict] = None):
        """
        配置独立的session
        """
        # 设置独立的headers
        session.headers.update({
            "User-Agent": self._generate_instance_ua(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        
        # 配置代理
        if proxy_config:
            proxy_url = self._build_proxy_url(proxy_config)
            if proxy_url:
                session.proxies = {
                    "http": proxy_url,
                    "https": proxy_url,
                }
        
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=2,
            pool_maxsize=2,
            max_retries=0,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    
    def _generate_instance_ua(self) -> str:
        """
        生成实例独有的User-Agent
        """
        chrome_versions = ["125.0.6422.110", "124.0.6367.82", "123.0.6312.118", "122.0.6261.112"]
        chrome_ver = random.choice(chrome_versions)
        
        android_versions = ["13", "12", "11", "10", "9"]
        android_ver = random.choice(android_versions)
        
        models = [
            ("SM-S908B", "Samsung"),
            ("SM-A546B", "Samsung"),
            ("SM-G998B", "Samsung"),
            ("Pixel 8 Pro", "Google"),
            ("Pixel 7", "Google"),
            ("LM-G910", "LG"),
            ("OnePlus 12", "OnePlus"),
            ("Xiaomi 14", "Xiaomi"),
            ("POCO X6 Pro", "Xiaomi"),
            ("Redmi Note 13", "Xiaomi"),
        ]
        model, brand = random.choice(models)
        
        return (
            f"Mozilla/5.0 (Linux; Android {android_ver}; {model}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_ver} Mobile Safari/537.36"
        )
    
    def _generate_visitor_id(self) -> str:
        """
        生成实例独有的visitor ID
        """
        random_part = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=12))
        ts_part = int(time.time()).to_bytes(5, "big").hex()
        instance_part = uuid.uuid4().hex[:8]
        return f"v_{random_part}{ts_part}_{instance_part}"
    
    def _build_proxy_url(self, proxy_config: Dict) -> Optional[str]:
        """
        构建代理URL
        """
        host = proxy_config.get("host", "")
        port = proxy_config.get("port", 7878)
        username = proxy_config.get("username", "")
        password = proxy_config.get("password", "")
        
        if not host or not port:
            return None
        
        if username and password:
            return f"http://{username}:{password}@{host}:{port}"
        elif username:
            return f"http://{username}@{host}:{port}"
        else:
            return f"http://{host}:{port}"
    
    def _get_next_proxy(self) -> Optional[Dict[str, Any]]:
        """
        获取下一个代理（轮询）
        """
        if not self._proxy_pool:
            return None
        
        proxy = self._proxy_pool[self._current_proxy_index]
        self._current_proxy_index = (self._current_proxy_index + 1) % len(self._proxy_pool)
        return proxy
    
    def get_environment(self, instance_id: str) -> Optional[InstanceEnvironment]:
        """
        获取实例环境
        """
        with self._lock:
            return self._environments.get(instance_id)
    
    def remove_environment(self, instance_id: str):
        """
        移除实例环境
        """
        with self._lock:
            if instance_id in self._environments:
                env = self._environments.pop(instance_id)
                if env.session:
                    env.session.close()
    
    def get_or_create_environment(
        self,
        instance_id: str,
        proxy_config: Optional[Dict[str, str]] = None,
    ) -> InstanceEnvironment:
        """
        获取或创建实例环境
        """
        with self._lock:
            if instance_id in self._environments:
                env = self._environments[instance_id]
                # 检查是否需要重建session
                if env.session is None or env.is_blocked():
                    if env.is_blocked():
                        env.unblock()
                    session = requests.Session()
                    self._configure_session(session, proxy_config or {
                        "host": env.proxy_host,
                        "port": env.proxy_port,
                        "username": env.proxy_username,
                        "password": env.proxy_password,
                    })
                    env.session = session
                    env.visitor_id = self._generate_visitor_id()
                return env
            return self.create_environment(instance_id, proxy_config)
    
    def rotate_proxy(self, instance_id: str, new_proxy: Optional[Dict[str, str]] = None):
        """
        轮换实例的代理
        """
        with self._lock:
            env = self._environments.get(instance_id)
            if not env:
                return
            
            # 关闭旧session
            if env.session:
                env.session.close()
            
            # 获取新代理
            if new_proxy is None:
                new_proxy = self._get_next_proxy()
            
            if new_proxy:
                env.proxy_host = new_proxy.get("host", "")
                env.proxy_port = int(new_proxy.get("port", 7878))
                env.proxy_username = new_proxy.get("username", "")
                env.proxy_password = new_proxy.get("password", "")
                env.ip_rotation_count += 1
            
            # 创建新session
            session = requests.Session()
            self._configure_session(session, new_proxy)
            env.session = session
            
            # 生成新的visitor_id
            env.visitor_id = self._generate_visitor_id()
            env.cookies.clear()
    
    def update_stats(self, instance_id: str, bytes_sent: int = 0, bytes_received: int = 0):
        """
        更新流量统计
        """
        with self._lock:
            env = self._environments.get(instance_id)
            if env:
                env.bytes_sent += bytes_sent
                env.bytes_received += bytes_received
                env.request_count += 1
    
    def record_failure(self, instance_id: str):
        """
        记录请求失败
        """
        with self._lock:
            env = self._environments.get(instance_id)
            if env:
                env.failed_count += 1
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """
        获取所有实例的统计信息
        """
        with self._lock:
            stats = {}
            for inst_id, env in self._environments.items():
                stats[inst_id] = {
                    "instance_id": inst_id,
                    "created_at": env.created_at,
                    "uptime": time.time() - env.created_at,
                    "visitor_id": env.visitor_id[:16] + "...",
                    "proxy": f"{env.proxy_host}:{env.proxy_port}",
                    "request_count": env.request_count,
                    "failed_count": env.failed_count,
                    "bytes_sent": env.bytes_sent,
                    "bytes_received": env.bytes_received,
                    "blocked": env.is_blocked(),
                    "ip_rotations": env.ip_rotation_count,
                }
            return stats
    
    def get_total_traffic(self) -> Dict[str, int]:
        """
        获取总流量统计
        """
        with self._lock:
            total_sent = sum(env.bytes_sent for env in self._environments.values())
            total_received = sum(env.bytes_received for env in self._environments.values())
            total_requests = sum(env.request_count for env in self._environments.values())
            total_failed = sum(env.failed_count for env in self._environments.values())
            
            return {
                "total_instances": len(self._environments),
                "total_requests": total_requests,
                "total_failed": total_failed,
                "total_bytes_sent": total_sent,
                "total_bytes_received": total_received,
                "total_mb_sent": total_sent // (1024 * 1024),
                "total_mb_received": total_received // (1024 * 1024),
            }
    
    def add_proxy_to_pool(self, proxy: Dict[str, Any]):
        """
        添加代理到池
        """
        with self._lock:
            self._proxy_pool.append(proxy)
    
    def clear_proxy_pool(self):
        """
        清空代理池
        """
        with self._lock:
            self._proxy_pool.clear()
    
    def cleanup(self):
        """
        清理所有环境
        """
        with self._lock:
            for env in self._environments.values():
                if env.session:
                    env.session.close()
            self._environments.clear()
