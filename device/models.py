from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class HardwareInfo:
    brand: str
    manufacturer: str
    model: str
    device: str
    product: str
    board: str
    hardware: str
    platform: str
    screen_width: int
    screen_height: int
    screen_dpi: int
    screen_density: float
    physical_ram: int
    total_storage: int
    available_storage: int
    cpu_abi: str
    cpu_cores: int
    cpu_max_freq: int
    gpu_vendor: str
    gpu_renderer: str
    webgl_version: str
    battery_capacity: int
    battery_health_pct: int
    charge_cycle_count: int
    has_touchscreen: bool
    has_wifi: bool
    has_bluetooth: bool
    has_gps: bool
    has_nfc: bool


@dataclass
class NetworkInfo:
    ip_address: str
    ip_type: str
    connection_type: str
    mcc: str
    mnc: str
    carrier_name: str
    carrier_name_cn: str
    is_roaming: bool
    wifi_ssid: Optional[str]
    wifi_bssid: Optional[str]
    network_operator: str
    sim_operator: str
    network_country_iso: str


@dataclass
class SystemInfo:
    os_name: str
    os_version: str
    os_api_level: int
    os_build_id: str
    os_build_fingerprint: str
    os_security_patch: str
    os_boot_time: int
    device_uptime_days: int
    sdk_version: str
    app_package_name: Optional[str]
    app_version: Optional[str]
    app_version_code: Optional[int]
    app_install_time: int
    app_update_time: int
    app_first_run_time: int
    is_rooted: bool
    is_emulator: bool
    is_vpn_active: bool
    is_proxy_active: bool
    has_google_play_services: bool
    timezone: str
    locale: str
    language: str
    country: str
    time_offset: int


@dataclass
class BrowserFingerprint:
    user_agent: str
    browser_name: str
    browser_version: str
    accept_language: str
    platform: str
    vendor: str
    color_depth: int
    pixel_depth: int
    screen_width: int
    screen_height: int
    viewport_width: int
    viewport_height: int
    device_pixel_ratio: float
    cookies_enabled: bool
    cookie_count: int
    local_storage_keys_count: int
    do_not_track: Optional[str]
    canvas_fingerprint: str
    webgl_vendor: str
    webgl_renderer: str
    webgl_fingerprint: str
    audio_fingerprint: str
    fonts_list: List[str]
    plugins_list: List[Dict]
    timezone_offset: int
    touch_support: Tuple[bool, bool, int]
    hardware_concurrency: int
    device_memory: float
    max_touch_points: int
    webgl_extensions: List[str]
    cookie_ids: Dict[str, str]


@dataclass
class UserProfile:
    age_range: str
    gender: str
    interests: List[str]
    installed_apps_count: int
    session_duration_avg: int
    ad_click_rate: float
    device_usage_hours_daily: int


@dataclass
class DeviceInfo:
    device_id_type: str
    device_id: str
    android_id: Optional[str]
    imei: Optional[str]
    oaid: Optional[str]
    idfa: Optional[str]
    idfv: Optional[str]
    openudid: Optional[str]
    hardware: HardwareInfo
    network: NetworkInfo
    system: SystemInfo
    browser: BrowserFingerprint
    profile: UserProfile
    device_fingerprint: str
    created_at: int


@dataclass
class AdRequest:
    request_id: str
    device: DeviceInfo
    ad_slot_id: str
    ad_format: str
    app_package: str
    timestamp: int
    nonce: str
    sign: str = ""


@dataclass
class AdResponse:
    ad_id: str
    creative_id: str
    click_url: str
    impression_url: str
    click_tracking_urls: List[str] = field(default_factory=list)
    impression_tracking_urls: List[str] = field(default_factory=list)
    redirect_chain: List[str] = field(default_factory=list)
    click_id: str = ""
    creative_type: str = "html"
    width: int = 0
    height: int = 0


@dataclass
class ClickEvent:
    click_id: str
    ad_id: str
    device: DeviceInfo
    click_time: int
    click_x: int
    click_y: int
    view_time_before_click: int
    is_valid: bool = True


@dataclass
class ConversionEvent:
    click_id: str
    event_name: str
    event_value: float
    event_time: int
    conversion_value: float
    currency: str = "USD"
    is_attributed: bool = False
