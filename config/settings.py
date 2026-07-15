from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RoiifyConfig:
    API_BASE_URL: str = "https://ads.roiify.com"
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

    ENABLE_ENVIRONMENT_VALIDATION: bool = True
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


config = RoiifyConfig()
