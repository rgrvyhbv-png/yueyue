from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RoiifyConfig:
    API_BASE_URL: str = "https://www.roiify.net"
    API_TIMEOUT: int = 30
    SDK_VERSION: str = "3.2.1"
    DEFAULT_APP_PACKAGE: str = "com.roiify.demo.game"
    DEFAULT_APP_VERSION: str = "1.2.5"
    DEFAULT_APP_VERSION_CODE: int = 125

    PLACEMENT_ID: str = "plc_dnza9sp1hxvu"
    
    PLACEMENT_IDS: List[str] = field(default_factory=lambda: [
        "plc_ureical15c9b",
        "plc_nvqz63tal1z0",
        "plc_rmiw16in7tug",
        "plc_8vlzute8yhtf",
        "plc_f6cagj0oay5j",
        "plc_pop5ecsr65hc",
        "plc_pp5n9ahjcd6g",
        "plc_04rw1flkkuu2",
        "plc_pwvy3u934auw",
    ])

    AD_SLOT_IDS: Dict[str, str] = field(default_factory=lambda: {
        "rewarded": "slot_rewarded_001",
        "interstitial": "slot_interstitial_001",
        "banner": "slot_banner_001",
        "native": "slot_native_001",
    })

    AD_FORMATS: List[str] = field(default_factory=lambda: [
        "rewarded_video",
        "interstitial",
        "banner",
        "native",
    ])

    REQUEST_SIGN_KEY: str = "roiify_sdk_sign_key_2024_v3"
    CLICK_ID_KEY: str = "click_id"
    TRACKING_PARAMS: List[str] = field(default_factory=lambda: [
        "click_id", "tracking_id", "impression_id", "request_id",
        "campaign_id", "creative_id", "adset_id", "pub_id",
        "app_id", "device_id_type", "device_id", "ts", "sign",
    ])

    MIN_VIEW_TIME_BEFORE_CLICK: int = 3
    MAX_VIEW_TIME_BEFORE_CLICK: int = 15
    MIN_LANDING_PAGE_STAY: int = 8
    MAX_LANDING_PAGE_STAY: int = 15
    MIN_BEHAVIOR_EVENTS: int = 2
    MAX_BEHAVIOR_EVENTS: int = 8

    USER_AGENT_POOL_SIZE: int = 100
    DEVICE_PROFILE_CACHE_TTL: int = 3600

    HTTP_HEADERS: Dict[str, str] = field(default_factory=lambda: {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "X-SDK-Version": "3.2.1",
        "X-Platform": "android",
    })

    ENABLE_ENVIRONMENT_VALIDATION: bool = False
    ENABLE_SIGNATURE_VALIDATION: bool = True
    ENABLE_FINGERPRINT_CHECK: bool = True
    ENABLE_BEHAVIOR_ANALYSIS: bool = True

    PROXY_ENABLED: bool = False
    PROXY_URL: Optional[str] = None

    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True

    CONVERSION_EVENTS: List[str] = field(default_factory=lambda: [
        "install", "register", "purchase", "tutorial_complete",
        "level_up", "add_to_cart", "checkout_initiated",
    ])

    # ========== 限流配置 ==========
    # 全局每分钟最大请求数（所有实例合计）
    GLOBAL_MAX_REQUESTS_PER_MINUTE: int = 60
    # 单实例每分钟最大请求数
    INSTANCE_MAX_REQUESTS_PER_MINUTE: int = 15
    # 最小请求间隔（毫秒）
    MIN_REQUEST_INTERVAL_MS: int = 3000
    # 突发请求限制
    BURST_SIZE: int = 3

    # ========== 环境隔离配置 ==========
    # 启用实例环境隔离
    ENABLE_ENVIRONMENT_ISOLATION: bool = True
    # Session最大生命周期（秒），超过后自动重建
    SESSION_MAX_LIFETIME: int = 3600
    # Cookie最大数量
    MAX_COOKIES_PER_INSTANCE: int = 50
    # Visitor ID重置间隔（请求数）
    VISITOR_ID_RESET_INTERVAL: int = 100

    # ========== 风控熔断配置 ==========
    # 启用熔断器
    ENABLE_CIRCUIT_BREAKER: bool = True
    # 连续失败触发熔断的阈值
    FAILURE_THRESHOLD: int = 5
    # 恢复超时时间（秒）
    RECOVERY_TIMEOUT: float = 30.0
    # 半开状态最大请求数
    HALF_OPEN_MAX_REQUESTS: int = 2
    # 恢复阶段持续时间（秒）
    RECOVERY_PHASE_DURATION: float = 60.0
    # 全局熔断阈值（被封禁的实例数占比）
    GLOBAL_BLOCK_THRESHOLD_RATIO: float = 0.5

    # ========== 流量优化配置 ==========
    # 跳过不必要的请求以节省流量
    SKIP_UNNECESSARY_REQUESTS: bool = True
    # 代理检测间隔（循环次数）
    PROXY_CHECK_INTERVAL: int = 100
    # 代理IP轮换间隔（请求数）
    PROXY_ROTATION_INTERVAL: int = 50
    # 落地页加载概率（0-1），降低流量消耗
    LANDING_PAGE_LOAD_PROBABILITY: float = 0.7
    # 模拟网络延迟（毫秒），添加随机性
    NETWORK_DELAY_MIN: int = 50
    NETWORK_DELAY_MAX: int = 200


config = RoiifyConfig()
