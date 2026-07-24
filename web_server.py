#!/usr/bin/env python3
"""Roiify Ad Simulator - Web Dashboard Server (Flask)"""

import json
import logging
import time
import os
import sys
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, Response, send_file

from device.fingerprint import DeviceFingerprintGenerator
from web.roiify_web_sdk import RoiifyWebSDK
from ad.webview import WebViewSimulator

from config import config, proxy
from browser.engine import BrowserConfig, init_browser_engine, browser_engine

logging.basicConfig(level=logging.WARNING)
server_logger = logging.getLogger("web_server")

app_logger = logging.getLogger("dashboard")
app_logger.setLevel(logging.INFO)

app = Flask(__name__, static_folder='web', static_url_path='')


class SimState:
    """Global simulation state"""
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.auto_running = False
        self.stop_requested = False
        self.result = None
        self.log_queue = queue.Queue()
        self.logs = []
        self.phase = 0
        self.error = None
        self.current_device_android = None
        self.current_device_ios = None
        self.target_impressions = 0
        self.browser_config = {
            "enabled": False,
            "headless": True,
            "browser_type": "chromium",
            "viewport_width": 375,
            "viewport_height": 812,
            "page_timeout": 30,
        }
        self.proxy_config = {
            "enabled": proxy.enabled,
            "provider": proxy.provider or "proxy001",
            "host": proxy.host,
            "port": proxy.port,
            "username": proxy.username or "cqywpu596838_custom_zone_US",
            "password": proxy.password or "pwd595247",
            "proxy_type": "http",
            "country": "US",
            "api_key": "",
        }
        self.stats = {
            "total_runs": 0,
            "success_runs": 0,
            "click_success": 0,
            "conversion_success": 0,
            "impression_success": 0,
            "landing_success": 0,
            "total_duration": 0,
            "runs": [],
        }
        self.current_run = 0
        self.used_device_models = set()

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        with self.lock:
            self.logs.append(line)
        self.log_queue.put(line)
        app_logger.info(msg)

    def set_phase(self, n):
        with self.lock:
            self.phase = n

    def start_run(self):
        with self.lock:
            self.running = True
            self.stop_requested = False
            self.result = None
            self.error = None

    def should_stop(self):
        with self.lock:
            return self.stop_requested

    def finish_run(self, result=None, error=None):
        with self.lock:
            self.running = False
            self.result = result
            self.error = error

    def reset_stats(self):
        with self.lock:
            self.stats = {
                "total_runs": 0,
                "success_runs": 0,
                "click_success": 0,
                "conversion_success": 0,
                "impression_success": 0,
                "landing_success": 0,
                "total_duration": 0,
                "runs": [],
            }

    def update_stats(self, run_data):
        with self.lock:
            self.stats["total_runs"] += 1
            if run_data.get("success"):
                self.stats["success_runs"] += 1
            if run_data.get("click_sent"):
                self.stats["click_success"] += 1
            if run_data.get("conversion_attributed"):
                self.stats["conversion_success"] += 1
            if run_data.get("impression_sent"):
                self.stats["impression_success"] += 1
            if run_data.get("landing_page_loaded"):
                self.stats["landing_success"] += 1
            if run_data.get("duration"):
                self.stats["total_duration"] += run_data["duration"]
            self.stats["runs"].append(run_data)


state = SimState()

PROXY_SAVE_FILE = os.path.expanduser("~/.roiify_proxy.json")


def save_proxy_config_to_file():
    try:
        with open(PROXY_SAVE_FILE, "w") as f:
            json.dump(state.proxy_config, f)
    except Exception:
        pass

def load_proxy_config_from_file():
    try:
        if os.path.exists(PROXY_SAVE_FILE):
            with open(PROXY_SAVE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None

_saved_proxy = load_proxy_config_from_file()
if _saved_proxy:
    state.proxy_config.update(_saved_proxy)
    # 如果加载的旧配置中的账号密码为空或使用了旧的GLOBAL账号，则使用新默认值
    old_username = state.proxy_config.get("username", "")
    if not old_username or "GLOBAL" in old_username:
        state.proxy_config["username"] = "cqywpu596838_custom_zone_US"
        state.proxy_config["password"] = "pwd595247"
        state.proxy_config["country"] = "US"
        save_proxy_config_to_file()


def generate_device(platform, device_age_days=300, country=None, exclude_models=None, max_attempts=30):
    exclude_models = exclude_models or set()
    for attempt in range(max_attempts):
        fp = DeviceFingerprintGenerator(platform=platform, device_age_days=device_age_days, country=country)
        dev = fp.generate()
        model_key = f"{dev.hardware.brand}|{dev.hardware.model}"
        if model_key not in exclude_models:
            dev.system.app_package_name = config.DEFAULT_APP_PACKAGE
            dev.system.app_version = config.DEFAULT_APP_VERSION
            dev.system.app_version_code = config.DEFAULT_APP_VERSION_CODE
            return dev
        fp.regenerate()
    fp = DeviceFingerprintGenerator(platform=platform, device_age_days=device_age_days, country=country)
    dev = fp.generate()
    dev.system.app_package_name = config.DEFAULT_APP_PACKAGE
    dev.system.app_version = config.DEFAULT_APP_VERSION
    dev.system.app_version_code = config.DEFAULT_APP_VERSION_CODE
    return dev


def _try_proxy_connection(username_override=None, max_retries=2):
    import requests
    import random
    import socket
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    test_username = username_override if username_override is not None else proxy.username
    test_username = test_username.strip() if test_username else ""

    if not proxy.host or not proxy.port:
        state.log(f"  [!] 代理配置不完整")
        return None, None

    if not test_username:
        state.log(f"  [!] 代理账号为空")
        return None, None

    if state.should_stop() or (hasattr(state, 'auto_running') and not state.auto_running):
        state.log(f"  [!] 检测到停止信号，跳过代理连接")
        return None, None

    def make_proxies(uname):
        if uname:
            auth = f"{uname}:{proxy.password}@" if proxy.password else f"{uname}@"
        else:
            auth = ""
        http_url = f"http://{auth}{proxy.host}:{proxy.port}"
        https_url = f"https://{auth}{proxy.host}:{proxy.port}"
        return {"http": http_url, "https": https_url}, uname

    test_urls = [
        "http://ip-api.com/json/?fields=status,message,country,countryCode,region,city,isp,query",
        "http://httpbin.org/ip",
    ]

    for attempt in range(max_retries):
        if state.should_stop() or (hasattr(state, 'auto_running') and not state.auto_running):
            state.log(f"  [!] 检测到停止信号，终止代理连接尝试")
            return None, None

        try:
            proxies, final_username = make_proxies(test_username)
            
            state.log(f"  正在连接代理... ({attempt + 1}/{max_retries})")
            
            session = requests.Session()
            retry_strategy = Retry(
                total=1,
                backoff_factor=0.3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            session.timeout = 10

            for url_idx, test_url in enumerate(test_urls):
                if state.should_stop() or (hasattr(state, 'auto_running') and not state.auto_running):
                    state.log(f"  [!] 检测到停止信号，终止代理连接尝试")
                    return None, None

                try:
                    state.log(f"  测试URL [{url_idx+1}/{len(test_urls)}]: {test_url}")
                    resp = session.get(
                        test_url,
                        proxies=proxies,
                        timeout=15,
                    )
                    
                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                        except Exception as json_err:
                            state.log(f"  [!] 响应解析失败: {str(json_err)[:50]}")
                            continue
                        
                        if data.get("status") == "success" or "ip" in data or data.get("query"):
                            ip_result = data.get("query", data.get("ip", "Unknown"))
                            country = data.get("country", "Unknown")
                            country_code = data.get("countryCode", "US")
                            result = {
                                "status": "success",
                                "country": country,
                                "countryCode": country_code,
                                "region": data.get("region", ""),
                                "city": data.get("city", ""),
                                "isp": data.get("isp", data.get("org", "Unknown ISP")),
                                "query": ip_result,
                                "timezone": data.get("timezone", "UTC"),
                            }
                            state.log(f"  ✓ 代理连接成功")
                            state.log(f"    IP: {ip_result}")
                            state.log(f"    国家: {country} ({country_code})")
                            state.log(f"    ISP: {result['isp']}")
                            return result, test_username
                        else:
                            err_msg = data.get("message", data.get("error", ""))
                            state.log(f"  [!] API返回错误: {err_msg}")
                            continue
                    elif resp.status_code == 407:
                        state.log(f"  [!] 代理认证失败(407): 账号密码错误")
                        return None, None
                    elif resp.status_code == 403:
                        state.log(f"  [!] 代理访问被拒绝(403): 可能IP被封禁")
                        continue
                    else:
                        state.log(f"  [!] HTTP错误: {resp.status_code}")
                        continue
                except requests.exceptions.ProxyError as e:
                    err_str = str(e)
                    if "407" in err_str:
                        state.log(f"  [!] 代理认证失败: 账号密码错误")
                        return None, None
                    elif "ECONNREFUSED" in err_str:
                        state.log(f"  [!] 代理连接被拒绝: 端口 {proxy.port} 不可达")
                        break
                    else:
                        state.log(f"  [!] 代理连接错误(URL {url_idx}): {err_str[:120]}")
                        continue
                except requests.exceptions.ConnectTimeout:
                    state.log(f"  [!] 代理连接超时(URL {url_idx}): 网络延迟过高")
                    continue
                except requests.exceptions.ConnectionError as e:
                    err_str = str(e)
                    if "Network is unreachable" in err_str:
                        state.log(f"  [!] 网络不可达: 请检查网络连接")
                        break
                    elif "Cannot assign requested address" in err_str:
                        state.log(f"  [!] 无法分配地址: 本地网络问题")
                        break
                    else:
                        state.log(f"  [!] 连接错误(URL {url_idx}): {err_str[:120]}")
                        continue
                except requests.exceptions.ReadTimeout:
                    state.log(f"  [!] 读取超时(URL {url_idx}): 代理响应过慢")
                    continue
                except Exception as e:
                    state.log(f"  [!] 未知错误(URL {url_idx}): {str(e)[:120]}")
                    continue
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                state.log(f"  [*] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                
        except Exception as e:
            state.log(f"  [!] 重试循环异常: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    state.log(f"  [!] 代理连接失败: 已尝试 {max_retries} 次，所有URL均无法访问")
    state.log(f"  [!] 请检查: 1) 代理账号密码 2) 网络连接 3) 防火墙设置")
    return None, None


def fetch_proxy_ip_info():
    if not proxy.enabled or not proxy.host or not proxy.port:
        return None
    data, used_username = _try_proxy_connection()
    if data:
        state.proxy_config["username"] = used_username
        save_proxy_config_to_file()
    return data


def apply_proxy_config():
    pc = state.proxy_config
    proxy.enabled = pc["enabled"]
    proxy_protocol = pc.get("proxy_type", "http").lower()
    
    country = pc.get("country", "US").upper()
    username = pc.get("username", "")
    password = pc.get("password", "")
    
    # 使用账号密码方式连接 proxy001 网关
    proxy.host = f"{country.lower()}.proxy001.com" if country else "us.proxy001.com"
    proxy.port = 7878
    proxy.username = username
    proxy.password = password
    proxy.country = country
    proxy.provider = "proxy001"
    proxy.proxy_type = proxy_protocol
    proxy.api_key = ""
    
    state.log(f"  [代理] 使用账号密码方式: {proxy.host}:{proxy.port} 地区: {country}")
    
    save_proxy_config_to_file()

_saved_proxy = load_proxy_config_from_file()
if _saved_proxy:
    state.proxy_config.update(_saved_proxy)
    # 如果加载的旧配置中的账号密码为空或使用了旧的GLOBAL账号，则使用新默认值
    old_username = state.proxy_config.get("username", "")
    if not old_username or "GLOBAL" in old_username:
        state.proxy_config["username"] = "cqywpu596838_custom_zone_US"
        state.proxy_config["password"] = "pwd595247"
        state.proxy_config["country"] = "US"
        save_proxy_config_to_file()
    apply_proxy_config()


def device_to_dict(dev):
    try:
        chrome_ver = "N/A"
        if "Chrome/" in dev.browser.user_agent:
            chrome_ver = dev.browser.user_agent.split("Chrome/")[1].split(" ")[0].split(".")[0]
        elif "CriOS/" in dev.browser.user_agent:
            chrome_ver = dev.browser.user_agent.split("CriOS/")[1].split(" ")[0].split(".")[0]
        elif "Version/" in dev.browser.user_agent:
            chrome_ver = dev.browser.user_agent.split("Version/")[1].split(" ")[0]

        import uuid
        aid = dev.android_id or str(uuid.uuid4()).replace("-", "")[:16]
        oaid_val = dev.oaid or str(uuid.uuid4()).replace("-", "")[:16]
        idfa_val = dev.idfa or str(uuid.uuid4()).upper()
        idfv_val = dev.idfv or str(uuid.uuid4()).upper()
        imei_val = dev.imei or ''.join([str(uuid.uuid4().int % 10) for _ in range(15)])

        return {
            "brand": dev.hardware.brand,
            "model": dev.hardware.model,
            "platform": dev.hardware.platform,
            "os": f"{dev.system.os_name} {dev.system.os_version}",
            "os_api": dev.system.os_api_level or "-",
            "device_id": dev.device_id,
            "device_id_type": dev.device_id_type,
            "android_id": aid,
            "oaid": oaid_val,
            "imei": imei_val,
            "ip": dev.network.ip_address,
            "carrier": dev.network.carrier_name,
            "connection": dev.network.connection_type,
            "battery_health": dev.hardware.battery_health_pct,
            "charge_cycles": dev.hardware.charge_cycle_count,
            "storage_total": dev.hardware.total_storage // (1024**3),
            "storage_avail": dev.hardware.available_storage // (1024**3),
            "storage_used_pct": round((1 - dev.hardware.available_storage / dev.hardware.total_storage) * 100),
            "screen": f"{dev.hardware.screen_width}x{dev.hardware.screen_height}",
            "dpi": dev.hardware.screen_dpi,
            "cpu": f"{dev.hardware.cpu_cores}核 {dev.hardware.cpu_abi}",
            "cpu_freq": f"{dev.hardware.cpu_max_freq / 1000000:.1f}GHz",
            "gpu": dev.hardware.gpu_renderer,
            "ram": f"{dev.hardware.physical_ram // (1024**3)}GB",
            "advertising_id": dev.device_id,
            "android_id_raw": aid,
            "oaid_raw": oaid_val,
            "idfa_raw": idfa_val,
            "idfv_raw": idfv_val,
            "imei_raw": imei_val,
            "cookies": dev.browser.cookie_count,
            "ls_keys": dev.browser.local_storage_keys_count,
            "apps": dev.profile.installed_apps_count,
            "webgl_fingerprint": dev.browser.webgl_fingerprint[:16] + "...",
            "canvas_fingerprint": dev.browser.canvas_fingerprint[:16] + "...",
            "audio_fingerprint": dev.browser.audio_fingerprint,
            "fingerprint": dev.device_fingerprint,
            "ua": dev.browser.user_agent,
            "locale": dev.system.locale,
            "timezone": dev.system.timezone,
            "chrome_version": chrome_ver,
            "is_rooted": dev.system.is_rooted,
            "is_emulator": dev.system.is_emulator,
            "has_gps": dev.hardware.has_gps,
            "has_nfc": dev.hardware.has_nfc,
            "touch_points": dev.browser.max_touch_points,
            "device_memory": dev.browser.device_memory,
            "hardware_concurrency": dev.browser.hardware_concurrency,
        }
    except Exception as e:
        return {"error": str(e)}


def run_simulation_thread(platform, device_age_days, system="auto"):
    try:
        import random as _rnd
        
        human_delay = _rnd.uniform(0.3, 0.8)
        state.log("═══ 开始模拟 ═══")
        system_display = {
            "auto": "自动",
            "ios": "iOS",
            "android": "安卓",
            "macos": "macOS",
            "linux": "Linux",
            "chromeos": "Chrome OS"
        }.get(system, "自动")
        state.log(f"系统: {system_display} | 平台: {'Android' if platform == 'android' else 'iOS'} | 设备年龄: {device_age_days}天")
        state.log(f"  [模拟] 用户正在打开应用... ({human_delay:.1f}秒)")
        time.sleep(human_delay)

        if state.should_stop():
            state.log("═══ 模拟已停止 ═══")
            state.finish_run(result={"stopped": True})
            return

        apply_proxy_config()
        target_country = None
        real_ip_info = None
        real_ip = None
        real_isp = None
        real_tz_name = None
        real_tz_offset = None
        proxy_actually_used = False

        if proxy.enabled:
            state.log(f"  代理已启用，正在检测出口IP...")
            if state.should_stop():
                state.log("═══ 模拟已停止 ═══")
                state.finish_run(result={"stopped": True})
                return

            real_ip_info = fetch_proxy_ip_info()
            if real_ip_info:
                real_ip = real_ip_info["query"]
                proxy_country = real_ip_info["countryCode"]
                real_isp = real_ip_info.get("isp", "Unknown ISP")
                real_tz_name = real_ip_info.get("timezone", "UTC")
                from datetime import datetime
                try:
                    from zoneinfo import ZoneInfo
                    tz = ZoneInfo(real_tz_name)
                    now = datetime.now(tz)
                    real_tz_offset = int(now.utcoffset().total_seconds() / 60)
                except Exception:
                    real_tz_offset = 0
                proxy_actually_used = True
                # 使用用户设置的国家，优先于代理检测到的国家
                target_country = state.proxy_config.get("country", proxy_country).upper()
                state.log(f"  ✓ 代理连接成功 - 所有请求将通过代理发送")
                state.log(f"  出口IP: {real_ip} | 用户设置地区: {target_country} | 代理实际地区: {proxy_country} | ISP: {real_isp}")
                state.log(f"  时区: {real_tz_name}")
            else:
                state.log(f"  [!] 代理连接失败（可能是网络/防火墙问题）")
                target_country = state.proxy_config.get("country", "US").upper()
                state.log(f"  [!] 将使用用户设置的{target_country}地区配置，但网络请求可能不走代理")
        else:
            state.log(f"  未启用代理，使用本地网络")
            target_country = state.proxy_config.get("country", "US").upper()
            state.log(f"  默认地区: {target_country}")

        state.set_phase(1)
        state.log("─ Phase 1: 生成设备指纹 ─")

        dev = generate_device(platform, device_age_days, country=target_country)
        if target_country:
            dev.system.country = target_country.lower()
            if real_tz_name:
                dev.system.timezone = real_tz_name
            if real_tz_offset is not None:
                dev.system.time_offset = real_tz_offset
            lang_map = {
                "US": "en", "GB": "en", "CA": "en", "AU": "en", "NZ": "en",
                "IE": "en", "SG": "en", "PH": "en", "IN": "en", "PK": "en",
                "BD": "en", "ZA": "en", "NG": "en", "KE": "en", "GH": "en",
                "TZ": "en", "UG": "en", "JM": "en", "TT": "en",
                "DE": "de", "AT": "de", "CH": "de", "FR": "fr", "BE": "fr",
                "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es",
                "PE": "es", "VE": "es", "EC": "es", "GT": "es", "DO": "es",
                "IT": "it", "NL": "nl", "RU": "ru", "PL": "pl", "TR": "tr",
                "PT": "pt", "BR": "pt", "GR": "el", "CZ": "cs",
                "RO": "ro", "HU": "hu", "UA": "uk", "BG": "bg", "HR": "hr",
                "SK": "sk", "SI": "sl", "LT": "lt", "LV": "lv", "EE": "et",
                "DK": "da", "FI": "fi", "NO": "no", "SE": "sv",
                "IL": "he", "SA": "ar", "AE": "ar", "EG": "ar", "QA": "ar",
                "KW": "ar", "BH": "ar", "OM": "ar", "JO": "ar", "LB": "ar",
                "IQ": "ar", "MA": "ar", "DZ": "ar", "TN": "ar", "IR": "fa",
                "JP": "ja", "KR": "ko", "CN": "zh", "TW": "zh", "HK": "zh",
                "TH": "th", "VN": "vi", "ID": "id", "MY": "ms", "MM": "my",
                "KH": "km", "LA": "lo", "MN": "mn", "NP": "ne", "LK": "si",
            }
            lang = lang_map.get(target_country, "en")
            dev.system.language = lang
            dev.system.locale = f"{lang}-{target_country}"
            dev.browser.accept_language = f"{dev.system.locale},{lang};q=0.9" + (",en;q=0.8" if lang != "en" else "")

        if real_ip:
            dev.network.ip_address = real_ip
        if real_isp:
            dev.network.carrier_name = real_isp

        if platform == "android":
            state.current_device_android = dev
        else:
            state.current_device_ios = dev

        chrome_ver = "N/A"
        if "Chrome/" in dev.browser.user_agent:
            chrome_ver = dev.browser.user_agent.split("Chrome/")[1].split(" ")[0].split(".")[0]

        state.log(f"  设备: {dev.hardware.brand} {dev.hardware.model}")
        state.log(f"  系统: {dev.system.os_name} {dev.system.os_version} (API {dev.system.os_api_level})")
        state.log(f"  Chrome: {chrome_ver}")
        from datetime import datetime, timezone, timedelta
        local_tz = timezone(timedelta(minutes=dev.system.time_offset))
        local_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
        state.log(f"  网络: {dev.network.connection_type} | 运营商: {dev.network.carrier_name}")
        state.log(f"  IP: {dev.network.ip_address}")
        state.log(f"  地区: {dev.system.country.upper()} | 语言: {dev.system.language} | 时区: {dev.system.timezone}")
        state.log(f"  本地时间: {local_time}")
        state.log(f"  电池健康: {dev.hardware.battery_health_pct}% | 充电循环: {dev.hardware.charge_cycle_count}次")
        state.log(f"  存储: {dev.hardware.available_storage//(1024**3)}GB/{dev.hardware.total_storage//(1024**3)}GB ({round((1-dev.hardware.available_storage/dev.hardware.total_storage)*100)}%已用)")
        state.log(f"  Cookies: {dev.browser.cookie_count}个 | LS: {dev.browser.local_storage_keys_count}个 | App: {dev.profile.installed_apps_count}个")
        state.log(f"  指纹: {dev.device_fingerprint[:24]}...")
        state.log(f"  Root: {'是' if dev.system.is_rooted else '否'} | 模拟器: {'是' if dev.system.is_emulator else '否'}")
        time.sleep(0.3)

        if proxy_actually_used and proxy.provider == "proxy001":
            dev_country = dev.system.country.upper()
            proxy.country = dev_country
            state.log(f"  代理国家已设置: {dev_country}")

        if state.should_stop():
            state.log("═══ 模拟已停止 ═══")
            state.finish_run(result={"stopped": True})
            return

        state.set_phase(2)
        state.log("─ Phase 2: 请求广告 ─")
        proxy_status_str = f"[通过代理: {real_ip}]" if proxy_actually_used else "[直连网络]"
        
        import random as _rnd
        placement_id = _rnd.choice(config.PLACEMENT_IDS)
        state.log(f"  {proxy_status_str} 向Roiify服务器发送广告请求...")
        state.log(f"  广告位ID: {placement_id}")
        
        web_sdk = RoiifyWebSDK(
            user_agent=dev.browser.user_agent,
            accept_language=dev.browser.accept_language,
            timezone=dev.system.timezone,
            locale=dev.system.locale,
            use_proxy=proxy_actually_used,
            device_info=dev,
        )
        ad_resp = web_sdk.request_ad(placement_id=placement_id, ad_format="banner")
        if not ad_resp:
            state.log(f"[ERROR] 广告请求失败，无法获取广告")
            state.log(f"  请检查：1) 网络连接 2) 代理配置 3) 广告位ID {placement_id} 是否有效")
            state.finish_run(error="广告请求失败")
            return
        click_url = ad_resp.get("clickUrl", "")
        impression_token = ad_resp.get("impressionToken")
        if not click_url:
            state.log(f"[ERROR] 广告响应中缺少clickUrl")
            state.finish_run(error="广告响应缺少点击URL")
            return
        state.log(f"  ✓ 广告请求成功，点击URL已获取")
        if impression_token:
            state.log(f"  ✓ 曝光Token已获取")
        else:
            state.log(f"[!] 警告：未获取到曝光Token，曝光可能无法上报")
        time.sleep(0.3)

        if state.should_stop():
            state.log("═══ 模拟已停止 ═══")
            state.finish_run(result={"stopped": True})
            return

        state.set_phase(3)
        state.log("─ Phase 3: 曝光上报 ─")
        
        view_dur = _rnd.uniform(5.0, 12.0)
        attention_level = _rnd.choice(["high", "medium", "low"])
        if attention_level == "high":
            state.log(f"  {proxy_status_str} 用户正在专注观看广告... ({view_dur:.1f}秒)")
        elif attention_level == "medium":
            state.log(f"  {proxy_status_str} 用户边浏览边观看广告... ({view_dur:.1f}秒)")
        else:
            state.log(f"  {proxy_status_str} 用户随意浏览广告... ({view_dur:.1f}秒)")
        
        for i in range(int(view_dur)):
            if state.should_stop():
                state.log("═══ 模拟已停止 ═══")
                state.finish_run(result={"stopped": True})
                return
            time.sleep(1.0)
            
        scroll_events = _rnd.randint(0, 3)
        if scroll_events > 0:
            state.log(f"  [模拟] 用户滚动屏幕 {scroll_events} 次")
            
        attention_level = _rnd.choices(["high", "medium", "low"], weights=[0.2, 0.5, 0.3], k=1)[0]
        if attention_level == "high":
            state.log(f"  [模拟] 用户高度关注广告内容")
        elif attention_level == "medium":
            state.log(f"  [模拟] 用户正常浏览广告")
        else:
            state.log(f"  [模拟] 用户分心，快速浏览广告")
            
        imp_ok = False
        if impression_token:
            imp_ok = web_sdk.send_impression(impression_token=impression_token, view_duration=view_dur)
            state.log(f"  观看时长: {view_dur:.1f}s → 曝光{'已通过代理上报' if proxy_actually_used else '已直连上报'}{'成功' if imp_ok else '失败'}")
        else:
            state.log(f"  观看时长: {view_dur:.1f}s → 无曝光Token，跳过上报")
        
        time.sleep(_rnd.uniform(0.2, 0.5))

        if state.should_stop():
            state.log("═══ 模拟已停止 ═══")
            state.finish_run(result={"stopped": True})
            return

        state.set_phase(4)
        state.log("─ Phase 4: 点击跳转 ─")
        
        reaction_delay = _rnd.uniform(0.3, 1.0)
        state.log(f"  [模拟] 用户正在考虑是否点击... ({reaction_delay:.1f}秒)")
        time.sleep(reaction_delay)
        
        conversion_values = {
            "saas_enterprise": 800.00,
            "legal_services": 700.00,
            "finance_mortgage": 600.00,
            "real_estate_investing": 500.00,
            "finance_investing_stocks": 400.00,
            "b2b_software": 380.00,
            "finance_insurance_health": 350.00,
            "finance_crypto_trading": 320.00,
            "finance_insurance_life": 280.00,
            "education_professional": 240.00,
            "finance_personal_loans": 200.00,
            "finance_credit_cards_premium": 180.00,
            "finance_debt_consolidation": 150.00,
            "software_subscription": 120.00,
            "ecommerce_high_ticket": 100.00,
        }
        categories = list(conversion_values.keys())
        
        value_weights = {
            "saas_enterprise": 3.5,
            "legal_services": 2.8,
            "finance_mortgage": 2.5,
            "real_estate_investing": 2.0,
            "finance_investing_stocks": 2.2,
            "b2b_software": 2.0,
            "finance_insurance_health": 2.0,
            "finance_crypto_trading": 1.8,
            "finance_insurance_life": 1.5,
            "education_professional": 1.2,
            "finance_personal_loans": 1.2,
            "finance_credit_cards_premium": 1.0,
            "finance_debt_consolidation": 0.8,
            "software_subscription": 0.6,
            "ecommerce_high_ticket": 0.5,
        }
        
        weighted_values = [conversion_values[c] * value_weights[c] for c in categories]
        total_weighted = sum(weighted_values)
        weights = [v / total_weighted for v in weighted_values]
        
        ad_category = _rnd.choices(categories, weights=weights, k=1)[0]
        click_success_rate = 0.01
        state.log(f"  [模拟] 广告类别: {ad_category} (价值${conversion_values[ad_category]}) | 预估点击率: {click_success_rate*100:.1f}%")
        
        will_click = _rnd.random() < click_success_rate
        
        click_retries = 0
        if not will_click:
            no_click_reasons = [
                "User not interested in this category",
                "User already has similar product",
                "User finds the offer unattractive",
                "User decides to skip the ad",
                "User is distracted by other things"
            ]
            reason = _rnd.choice(no_click_reasons)
            state.log(f"  [模拟] 用户未点击广告 - {reason}")
            click_sent = False
            final_click_url = click_url
            click_id = None
        else:
            click_motivations = [
                "User finds the offer interesting",
                "User needs this product/service",
                "The ad is well-targeted",
                "User wants to learn more",
                "Attractive pricing or offer"
            ]
            motivation = _rnd.choice(click_motivations)
            state.log(f"  [模拟] 用户决定点击广告 - {motivation}")
            
            click_delay = _rnd.uniform(0.2, 0.6)
            state.log(f"  [模拟] 用户手指移动到广告位置并点击... ({click_delay:.1f}秒)")
            time.sleep(click_delay)
            
            click_sent = False
            click_retries = 0
            max_click_retries = 3
            
            while click_retries < max_click_retries and not click_sent and not state.should_stop():
                click_retries += 1
                state.log(f"  {proxy_status_str} 发送点击请求... (尝试 {click_retries}/{max_click_retries})")
                click_url = web_sdk.get_click_url() or click_url
                if click_url:
                    click_sent = web_sdk.send_click()
                
                if click_sent:
                    state.log(f"  ✓ 点击请求发送成功")
                else:
                    state.log(f"  ✗ 点击请求发送失败")
            
            final_click_url = web_sdk.get_click_url() or click_url

            click_id = None
            from urllib.parse import urlparse, parse_qs
            try:
                parsed = urlparse(final_click_url)
                params = parse_qs(parsed.query)
                for key in ["click_id", "tracking_id", "tid", "clickid", "aff_click_id", "cid", "visitorId"]:
                    if key in params:
                        click_id = params[key][0]
                        break
            except Exception:
                pass
            
            if click_id:
                state.log(f"  提取Click ID: {click_id[:16]}...")
        time.sleep(_rnd.uniform(0.3, 0.7))

        if state.should_stop():
            state.log("═══ 模拟已停止 ═══")
            state.finish_run(result={"stopped": True})
            return

        if not click_sent:
            state.log("  [跳过] 用户未点击，跳过落地页和转化归因")
            state.log("═══ 模拟完成 ═══")
            result = {
                "success": True,
                "device": device_to_dict(dev),
                "impression_sent": impression_token is not None and imp_ok,
                "click_sent": click_sent,
                "landing_page_loaded": False,
                "conversion_attributed": False,
                "proxy_used": proxy_actually_used,
                "proxy_ip": real_ip,
                "proxy_country": target_country,
                "view_duration": round(view_dur, 1),
                "ad_category": ad_category,
                "conversion_value": 0,
            }
            state.finish_run(result=result)
            return

        state.set_phase(5)
        state.log("─ Phase 5: Landing Page ─")
        from utils.network import NetworkClient
        net_client = NetworkClient(device=dev)
        wv = WebViewSimulator(device=dev, network=net_client)
        if click_id:
            net_client.cookies.set("roiify_click_id", click_id, domain="roiify.com")
            wv.set_click_id(click_id)
        
        landing_stay = _rnd.uniform(8.0, 18.0)
        interaction_level = _rnd.choice(["deep", "medium", "light"])
        
        if interaction_level == "deep":
            state.log(f"  {proxy_status_str} 用户深入浏览落地页... (预计停留 {landing_stay:.1f}秒)")
        elif interaction_level == "medium":
            state.log(f"  {proxy_status_str} 用户适度浏览落地页内容... (预计停留 {landing_stay:.1f}秒)")
        else:
            state.log(f"  {proxy_status_str} 用户快速浏览落地页... (预计停留 {landing_stay:.1f}秒)")
        
        state.log(f"  {proxy_status_str} 加载广告主落地页...")
        landing = wv.load_landing_page(
            url=final_click_url,
            referrer="https://www.roiify.net/",
            simulate_behavior=True,
            stay_duration=landing_stay,
        )
        
        if landing.get("final_url"):
            final_domain = landing["final_url"].split("/")[2] if "://" in landing["final_url"] else ""
            state.log(f"  落地页域名: {final_domain}")
        
        if landing["success"]:
            landing_behaviors = {
                "deep": [
                    "User reads product details thoroughly",
                    "User checks pricing information",
                    "User views customer reviews",
                    "User reads FAQ section",
                ],
                "medium": [
                    "User scans main content",
                    "User views key features",
                    "User checks basic pricing",
                ],
                "light": [
                    "User quickly scrolls through page",
                    "User only views top section",
                ],
            }
            behaviors = _rnd.choice(landing_behaviors.get(interaction_level, landing_behaviors["light"]))
            state.log(f"  [模拟] {behaviors}")
            
            button_clicks = _rnd.randint(0, 2)
            if button_clicks > 0:
                click_actions = [
                    "点击'立即申请'按钮",
                    "点击'了解更多'查看详细信息",
                    "点击'计算工具'进行贷款计算",
                    "点击'联系客服'咨询",
                    "点击'查看条款'阅读协议",
                    "点击'常见问题'查看FAQ",
                ]
                for _ in range(button_clicks):
                    action = _rnd.choice(click_actions)
                    state.log(f"  [模拟] 用户{action}")
        
        state.log(f"  加载结果: {'✓ 成功' if landing['success'] else '✗ WAF拦截/网络错误'}")
        state.log(f"  停留时长: {landing['duration']:.1f}s | 行为事件: {landing.get('behavior_events', 0)}个")
        time.sleep(_rnd.uniform(0.2, 0.4))

        if state.should_stop():
            state.log("═══ 模拟已停止 ═══")
            state.finish_run(result={"stopped": True})
            return

        state.set_phase(6)
        state.log("─ Phase 6: 转化归因 ─")
        
        conv_prob = _rnd.uniform(0.01, 0.03)
        will_convert = _rnd.random() < conv_prob
        actual_value = 0
        state.log(f"  [模拟] 预估转化率: {conv_prob*100:.1f}%")
        
        if not will_convert:
            state.log(f"  [模拟] 用户未完成转化 - 离开页面或放弃注册")
            conv_ok = False
        else:
            state.log(f"  {proxy_status_str} 触发转化事件...")
            
            conv_value = conversion_values.get(ad_category, 100.00)
            
            conversion_events = [
                {"event": "register", "multiplier": 1.0, "desc": "用户注册"},
                {"event": "lead", "multiplier": 0.6, "desc": "提交线索"},
                {"event": "purchase", "multiplier": 3.0, "desc": "完成购买"},
                {"event": "subscription", "multiplier": 2.5, "desc": "订阅服务"},
                {"event": "download", "multiplier": 0.3, "desc": "下载应用"},
            ]
            
            event_weights = [50, 30, 10, 8, 2]
            total_weight = sum(event_weights)
            event_probs = [w / total_weight for w in event_weights]
            
            selected_event = _rnd.choices(conversion_events, weights=event_probs, k=1)[0]
            actual_value = round(conv_value * selected_event["multiplier"], 2)
            
            wv_conv = wv.simulate_conversion_event(event_name=selected_event["event"], value=actual_value)
            state.log(f"  转化事件: {selected_event['desc']} ({selected_event['event']})")
            state.log(f"  基础价值: ${conv_value} × 倍率: {selected_event['multiplier']}x = ${actual_value}")
            state.log(f"  广告曝光: ✓ 已上报")
            state.log(f"  广告点击: ✓ 已上报")
            state.log(f"  落地页访问: {'✓ 完成' if landing.get('success') else '✗ 被拦截'}")
            state.log(f"  代理状态: {'✓ 所有请求通过代理' if proxy_actually_used else '✗ 未使用代理（直连）'}")
            state.log(f"  说明: 转化事件需广告主落地页集成Roiify SDK后回传")
            conv_ok = click_sent and landing.get("success", False)
        time.sleep(0.2)

        state.log("═══ 模拟完成 ═══")

        result = {
            "success": True,
            "device": device_to_dict(dev),
            "impression_sent": impression_token is not None and imp_ok,
            "click_sent": click_sent,
            "landing_page_loaded": landing.get("success", False),
            "conversion_attributed": conv_ok,
            "proxy_used": proxy_actually_used,
            "proxy_ip": real_ip,
            "proxy_country": target_country,
            "view_duration": round(view_dur, 1),
            "ad_category": ad_category,
            "conversion_value": actual_value if conv_ok else 0,
        }
        state.finish_run(result=result)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        state.log(f"[ERROR] 异常: {e}")
        for line in tb.split("\n")[-5:]:
            if line.strip():
                state.log(f"  {line.strip()}")
        state.finish_run(error=str(e))


# ── Flask Routes ──

@app.route("/")
@app.route("/index.html")
def index():
    import os
    html_path = os.path.join(os.path.dirname(__file__), 'web', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    resp = app.make_response(html_content)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


@app.route("/control.html")
def control():
    import os
    html_path = os.path.join(os.path.dirname(__file__), 'web', 'control.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    resp = app.make_response(html_content)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


@app.route("/test")
def test_page():
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Test</title>
<style>body{background:#0b0b12;color:#c5c5d8;font-family:monospace;padding:40px;}
h1{color:#00e4a0;} .card{background:#141420;border:1px solid #2a2a45;border-radius:12px;padding:20px;margin:10px 0;}
a{color:#0066cc;text-decoration:underline;}</style></head>
<body><h1>Roiify Ad Simulator</h1>
<div class="card"><p>Server is running correctly.</p><p>Go to <a href="/">Dashboard</a></p></div>
</body></html>"""


@app.route("/api/device")
def api_device():
    plat = request.args.get("platform", "auto")
    age = int(request.args.get("age", "300"))
    if plat == "auto":
        import random as _rnd
        plat = _rnd.choice(["android", "ios"])
    apply_proxy_config()
    # 使用用户设置的国家，优先于代理检测到的国家
    user_country = state.proxy_config.get("country", "US").upper()
    detected_country = user_country
    ip_info = None
    if proxy.enabled:
        ip_info = fetch_proxy_ip_info()
        # 代理检测到的国家用于验证，用户设置的国家用于设备指纹
        if ip_info:
            proxy_country = ip_info.get("countryCode", "UNKNOWN")
            state.log(f"  [*] 用户设置国家: {user_country} | 代理实际国家: {proxy_country}")
    dev = generate_device(plat, age, country=detected_country)
    if ip_info:
        real_ip = ip_info.get("query")
        real_isp = ip_info.get("isp", "Unknown ISP")
        real_tz_name = ip_info.get("timezone")
        if real_ip:
            dev.network.ip_address = real_ip
        if real_isp:
            dev.network.carrier_name = real_isp
        if real_tz_name:
            dev.system.timezone = real_tz_name
    if plat == "android":
        state.current_device_android = dev
    else:
        state.current_device_ios = dev
    return jsonify(device_to_dict(dev))


@app.route("/api/state")
def api_state():
    with state.lock:
        return jsonify({
            "running": state.running,
            "auto_running": state.auto_running,
            "phase": state.phase,
            "result": state.result,
            "error": state.error,
        })


@app.route("/api/logs")
def api_logs():
    after = int(request.args.get("after", "0"))
    limit = int(request.args.get("limit", "1000"))
    total = len(state.logs)
    
    if after >= total:
        start = max(0, total - limit)
        new_logs = state.logs[start:]
    else:
        new_logs = state.logs[after:]
    
    return jsonify({"logs": new_logs, "total": total})


@app.route("/api/clear_logs", methods=["POST"])
def api_clear_logs():
    with state.lock:
        state.logs = []
        state.log_queue = queue.Queue()
    return jsonify({"success": True})


@app.route("/api/proxy", methods=["GET", "POST"])
def api_proxy():
    if request.method == "POST":
        data = request.get_json()
        for k in ("enabled", "proxy_type", "provider", "country", "api_key"):
            if k in data:
                state.proxy_config[k] = data[k]
        state.proxy_config["enabled"] = bool(data.get("enabled", False))
        apply_proxy_config()
        state.log(f"代理配置已更新: {'启用' if state.proxy_config['enabled'] else '禁用'} ({state.proxy_config.get('provider', 'proxy001')})")
    return jsonify(state.proxy_config)


@app.route("/api/proxy/delete", methods=["POST"])
def api_proxy_delete():
    state.proxy_config = {
        "enabled": False,
        "provider": "proxy001",
        "host": "",
        "port": 0,
        "username": "cqywpu596838_custom_zone_US",
        "password": "pwd595247",
        "proxy_type": "http",
        "country": "US",
        "api_key": "",
    }
    apply_proxy_config()
    return jsonify({"success": True})


@app.route("/api/browser", methods=["GET", "POST"])
def api_browser():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        for k in ("enabled", "headless", "browser_type", "viewport_width", "viewport_height", "page_timeout"):
            if k in data:
                state.browser_config[k] = data[k]
        if "enabled" in data:
            state.browser_config["enabled"] = bool(data["enabled"])
        
        bc = BrowserConfig(
            enabled=state.browser_config["enabled"],
            headless=state.browser_config["headless"],
            browser_type=state.browser_config["browser_type"],
            viewport_width=state.browser_config["viewport_width"],
            viewport_height=state.browser_config["viewport_height"],
            page_timeout=state.browser_config["page_timeout"],
            proxy_host=proxy.host,
            proxy_port=proxy.port,
            proxy_username=proxy.username,
            proxy_password=proxy.password,
        )
        
        success = init_browser_engine(bc)
        state.log(f"浏览器配置已更新: {'启用' if state.browser_config['enabled'] else '禁用'}")
        if state.browser_config["enabled"] and not success:
            state.log("[!] Playwright未安装，请先安装依赖")
    
    return jsonify(state.browser_config)


@app.route("/api/stop", methods=["GET", "POST"])
def api_stop():
    with state.lock:
        state.stop_requested = True
        state.auto_running = False
    return jsonify({"stopping": True})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    with state.lock:
        stats = state.stats.copy()
        total = stats["total_runs"]
        if total > 0:
            stats["click_rate"] = round(stats["click_success"] / total * 100, 2)
            stats["conversion_rate"] = round(stats["conversion_success"] / total * 100, 2)
            stats["avg_duration"] = round(stats["total_duration"] / total, 2)
            
            total_value = sum(r.get("conversion_value", 0) for r in stats["runs"])
            stats["total_revenue"] = round(total_value, 2)
            stats["avg_revenue"] = round(total_value / total, 2)
            if stats["click_success"] > 0:
                stats["revenue_per_click"] = round(total_value / stats["click_success"], 2)
            else:
                stats["revenue_per_click"] = 0
        else:
            stats["click_rate"] = 0
            stats["conversion_rate"] = 0
            stats["avg_duration"] = 0
            stats["total_revenue"] = 0
            stats["avg_revenue"] = 0
            stats["revenue_per_click"] = 0
        stats["auto_running"] = state.auto_running
        stats["current_run"] = state.current_run
        stats["target_impressions"] = state.target_impressions
    return jsonify(stats)


@app.route("/api/auto-start", methods=["POST"])
def api_auto_start():
    if state.running or state.auto_running:
        return jsonify({"error": "already running"}), 409
    data = request.get_json(silent=True) or {}
    target_impressions = int(data.get("target_impressions", 0))
    state.reset_stats()
    with state.lock:
        state.auto_running = True
        state.current_run = 0
        state.target_impressions = target_impressions
    if target_impressions > 0:
        state.log(f"═══ 启动自动化循环 (目标展示量: {target_impressions:,}) ═══")
    else:
        state.log("═══ 启动自动化循环 ═══")
    t = threading.Thread(target=auto_loop_thread, daemon=True)
    t.start()
    return jsonify({"started": True, "auto_running": True, "target_impressions": target_impressions})


@app.route("/api/auto-stop", methods=["POST"])
def api_auto_stop():
    with state.lock:
        state.auto_running = False
        state.stop_requested = True
    state.log("═══ 自动化循环已停止 ═══")
    return jsonify({"stopped": True})


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    if state.running:
        return jsonify({"error": "already running"}), 409
    data = request.get_json(silent=True) or {}
    platform = data.get("platform", "auto")
    age = int(data.get("age", 365))
    system = data.get("system", "auto")
    if platform == "auto":
        import random as _rnd
        platform = _rnd.choice(["android", "ios"])
    state.start_run()
    state.set_phase(1)
    t = threading.Thread(target=run_simulation_thread, args=(platform, age, system), daemon=True)
    t.start()
    return jsonify({"started": True, "platform": platform, "system": system})


INSTANCES_CONFIG = {
    "base_port": 8765,
    "max_instances": 10,
}


@app.route("/api/instances", methods=["GET"])
def api_instances():
    instances = []
    for i in range(1, INSTANCES_CONFIG["max_instances"] + 1):
        port = INSTANCES_CONFIG["base_port"] + i - 1
        pid_file = f"pids/roiify_{port}.pid"
        running = False
        pid = None
        
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    import subprocess
                    result = subprocess.run(['kill', '-0', str(pid)], capture_output=True, timeout=2)
                    if result.returncode == 0:
                        running = True
                    else:
                        os.remove(pid_file)
                        pid = None
                except:
                    os.remove(pid_file)
                    pid = None
            except:
                pid = None
        
        instances.append({
            "id": i,
            "port": port,
            "pid": pid,
            "running": running,
            "url": f"http://178.236.47.224:{port}",
        })
    return jsonify({"instances": instances})


@app.route("/api/instances/<int:instance_id>/start", methods=["POST"])
def api_instance_start(instance_id):
    if instance_id < 1 or instance_id > INSTANCES_CONFIG["max_instances"]:
        return jsonify({"error": "Invalid instance ID"}), 400
    
    port = INSTANCES_CONFIG["base_port"] + instance_id - 1
    pid_file = f"pids/roiify_{port}.pid"
    
    try:
        import subprocess
        import os
        
        os.makedirs("pids", exist_ok=True)
        
        process = subprocess.Popen(
            ["python3", "web_server.py", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        import time
        time.sleep(2)
        
        if process.poll() is None:
            return jsonify({"started": True, "instance_id": instance_id, "port": port, "pid": process.pid})
        else:
            stderr = process.stderr.read().decode('utf-8', errors='ignore')
            os.remove(pid_file)
            return jsonify({"error": f"Process exited: {stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/instances/<int:instance_id>/stop", methods=["POST"])
def api_instance_stop(instance_id):
    if instance_id < 1 or instance_id > INSTANCES_CONFIG["max_instances"]:
        return jsonify({"error": "Invalid instance ID"}), 400
    
    port = INSTANCES_CONFIG["base_port"] + instance_id - 1
    pid_file = f"pids/roiify_{port}.pid"
    
    try:
        import subprocess
        
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            subprocess.run(['kill', str(pid)], capture_output=True)
            time.sleep(1)
            subprocess.run(['kill', '-9', str(pid)], capture_output=True)
            
            if os.path.exists(pid_file):
                os.remove(pid_file)
        
        subprocess.run(['pkill', '-f', f'python web_server.py --port {port}'], capture_output=True)
        return jsonify({"stopped": True, "instance_id": instance_id, "port": port})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/instances/all/start", methods=["POST"])
def api_instances_all_start():
    import subprocess
    import os
    import time
    
    os.makedirs("pids", exist_ok=True)
    success_count = 0
    
    for i in range(1, INSTANCES_CONFIG["max_instances"] + 1):
        port = INSTANCES_CONFIG["base_port"] + i - 1
        pid_file = f"pids/roiify_{port}.pid"
        
        try:
            process = subprocess.Popen(
                ["python3", "web_server.py", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            time.sleep(0.5)
            
            if process.poll() is None:
                success_count += 1
            else:
                os.remove(pid_file)
        except:
            pass
    
    return jsonify({"started": True, "count": INSTANCES_CONFIG["max_instances"], "success": success_count})


@app.route("/api/instances/all/stop", methods=["POST"])
def api_instances_all_stop():
    import subprocess
    subprocess.run(['pkill', '-f', 'python web_server.py'], capture_output=True)
    return jsonify({"stopped": True})


@app.route("/api/instances/<int:instance_id>/stats", methods=["GET"])
def api_instance_stats(instance_id):
    if instance_id < 1 or instance_id > INSTANCES_CONFIG["max_instances"]:
        return jsonify({"error": "Invalid instance ID"}), 400
    
    port = INSTANCES_CONFIG["base_port"] + instance_id - 1
    
    try:
        import urllib.request
        url = f"http://localhost:{port}/api/stats"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read().decode('utf-8')
            return jsonify(json.loads(data))
    except Exception as e:
        return jsonify({"error": str(e), "instance_id": instance_id, "port": port}), 503


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765, help='Port to listen on')
    args = parser.parse_args()
    
    apply_proxy_config()
    port = args.port
    print(f"\n  Roiify Ad Simulator Dashboard")
    print(f"  http://localhost:{port}\n")
    if proxy.enabled:
        print(f"  Proxy enabled: {proxy.host}:{proxy.port} ({proxy.provider})")
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


def auto_loop_thread():
    import random as _rnd
    start_time = time.time()
    
    while state.auto_running:
        with state.lock:
            state.current_run += 1
            current_run_num = state.current_run
            state.stop_requested = False
        
        state.log(f"\n═══════════════════════════════════════════")
        state.log(f"  第 {current_run_num} 次循环开始")
        state.log(f"═══════════════════════════════════════════")
        
        run_start_time = time.time()
        try:
            systems = ["ios", "android", "macos", "linux", "chromeos"]
            system_weights = [30, 30, 15, 15, 10]
            system = _rnd.choices(systems, weights=system_weights, k=1)[0]
            
            if system in ["macos", "linux", "chromeos"]:
                platform = "android"
            else:
                platform = system
            
            device_age = _rnd.randint(30, 730)
            
            apply_proxy_config()
            target_country = None
            real_ip_info = None
            real_ip = None
            real_isp = None
            proxy_actually_used = False
            proxy_connect_attempts = 0
            max_proxy_attempts = 2

            if proxy.enabled:
                # 缓存代理信息，每30次循环才重新检测，减少流量消耗
                need_proxy_check = (current_run_num % 30 == 1) or (not hasattr(state, '_cached_proxy_info'))
                if need_proxy_check:
                    state.log(f"  代理已启用，正在检测出口IP...")
                    while proxy_connect_attempts < max_proxy_attempts and state.auto_running:
                        proxy_connect_attempts += 1
                        state.log(f"  [代理] 尝试 {proxy_connect_attempts}/{max_proxy_attempts}")
                        real_ip_info = fetch_proxy_ip_info()
                        
                        if real_ip_info:
                            real_ip = real_ip_info["query"]
                            proxy_country = real_ip_info["countryCode"]
                            real_isp = real_ip_info.get("isp", "Unknown ISP")
                            proxy_actually_used = True
                            target_country = state.proxy_config.get("country", proxy_country).upper()
                            state.log(f"  ✓ 代理连接成功 | IP: {real_ip} | 地区: {target_country}")
                            # 缓存代理信息
                            state._cached_proxy_info = {
                                "ip": real_ip,
                                "country": target_country,
                                "isp": real_isp,
                                "timestamp": time.time()
                            }
                            break
                        else:
                            state.log(f"  ✗ 代理连接失败")
                            if proxy_connect_attempts < max_proxy_attempts:
                                time.sleep(1)
                    
                    if not real_ip_info:
                        # 如果有缓存的代理信息，继续使用
                        if hasattr(state, '_cached_proxy_info') and time.time() - state._cached_proxy_info["timestamp"] < 3600:
                            state.log(f"  [!] 代理检测失败，使用缓存的代理信息")
                            cached = state._cached_proxy_info
                            real_ip = cached["ip"]
                            target_country = cached["country"]
                            real_isp = cached["isp"]
                            proxy_actually_used = True
                        else:
                            state.log(f"  [!] 代理连接失败，跳过本次循环")
                            run_data = {
                                "run": current_run_num,
                                "success": False,
                                "platform": platform,
                                "device": "N/A",
                                "proxy_ip": None,
                                "proxy_country": None,
                                "error": "proxy_connection_failed",
                                "duration": round(time.time() - run_start_time, 2),
                                "ad_category": "N/A",
                                "conversion_value": 0,
                            }
                            state.update_stats(run_data)
                            continue
                else:
                    # 使用缓存的代理信息
                    cached = state._cached_proxy_info
                    real_ip = cached["ip"]
                    target_country = cached["country"]
                    real_isp = cached["isp"]
                    proxy_actually_used = True
                    state.log(f"  [代理] 使用缓存 | IP: {real_ip} | 地区: {target_country}")
            else:
                target_country = state.proxy_config.get("country", "US").upper()
            
            state.log(f"  [*] 目标国家: {target_country}")

            state.set_phase(1)
            state.log("─ Phase 1: 生成设备指纹 ─")
            
            # 限制已使用设备模型数量，避免过多导致生成效率低下
            if len(state.used_device_models) > 50:
                state.used_device_models.clear()
                state.log(f"  [*] 已重置设备模型缓存")
            
            dev = generate_device(platform, device_age, target_country, exclude_models=state.used_device_models)
            model_key = f"{dev.hardware.brand}|{dev.hardware.model}"
            state.used_device_models.add(model_key)
            
            chrome_ver = "N/A"
            if "Chrome/" in dev.browser.user_agent:
                chrome_ver = dev.browser.user_agent.split("Chrome/")[1].split(" ")[0].split(".")[0]
            elif "CriOS/" in dev.browser.user_agent:
                chrome_ver = dev.browser.user_agent.split("CriOS/")[1].split(" ")[0].split(".")[0]
            
            system_display = {
                "ios": "iOS",
                "android": "安卓",
                "macos": "macOS",
                "linux": "Linux",
                "chromeos": "Chrome OS"
            }.get(system, "未知")
            state.log(f"  设备: {dev.hardware.brand} {dev.hardware.model}")
            state.log(f"  系统: {system_display} ({dev.system.os_name} {dev.system.os_version})")
            state.log(f"  Chrome: {chrome_ver}")
            state.log(f"  网络: {dev.network.connection_type} | 运营商: {dev.network.carrier_name}")
            state.log(f"  IP: {real_ip or dev.network.ip_address}")
            state.log(f"  指纹: {dev.device_fingerprint[:16]}...")

            if proxy_actually_used and proxy.provider == "proxy001":
                dev_country = dev.system.country.upper()
                proxy.country = dev_country
                state.log(f"  代理国家已设置: {dev_country}")

            if state.should_stop():
                state.log("═══ 自动化循环已停止 ═══")
                break

            session_depth = _rnd.random()
            session_depth_label = "首次访问" if session_depth < 0.3 else "回访用户" if session_depth < 0.7 else "深度用户"
            page_views_in_session = _rnd.randint(1, 12)
            avg_scroll_depth = _rnd.uniform(20, 95)
            time_on_page = _rnd.uniform(2, 30)
            
            # 增加随机跳过概率，模拟真实用户并非每次都看广告
            skip_probability = _rnd.uniform(0.02, 0.08)
            if _rnd.random() < skip_probability:
                state.log(f"  [模拟] 用户跳过广告 (概率: {skip_probability*100:.1f}%)")
                run_data = {
                    "run": current_run_num,
                    "success": False,
                    "platform": platform,
                    "device": f"{dev.hardware.brand} {dev.hardware.model}",
                    "proxy_ip": real_ip,
                    "proxy_country": target_country,
                    "error": "user_skipped",
                    "duration": round(time.time() - run_start_time, 2),
                    "ad_category": "N/A",
                    "conversion_value": 0,
                }
                state.update_stats(run_data)
                continue
            
            state.log(f"  会话状态: {session_depth_label}")
            state.log(f"  本次会话页面数: {page_views_in_session}")
            state.log(f"  平均滚动深度: {avg_scroll_depth:.0f}%")
            state.log(f"  页面停留时间: {time_on_page:.0f}秒")

            time.sleep(_rnd.uniform(0.2, 0.5))

            state.set_phase(2)
            state.log("─ Phase 2: 请求广告 ─")
            
            placement_id = _rnd.choice(config.PLACEMENT_IDS)
            state.log(f"  广告位ID: {placement_id}")
            
            web_sdk = RoiifyWebSDK(
                user_agent=dev.browser.user_agent,
                accept_language=dev.browser.accept_language,
                timezone=dev.system.timezone,
                locale=dev.system.locale,
                use_proxy=proxy_actually_used,
                device_info=dev,
            )
            ad_response = web_sdk.request_ad(placement_id=placement_id, ad_format="banner")
            
            if ad_response:
                state.log(f"  ✓ 广告请求成功")
                impression_token = ad_response.get("impressionToken")
                click_url = ad_response.get("clickUrl", "")
                if impression_token:
                    state.log(f"  ✓ 曝光Token已获取")
                if click_url:
                    state.log(f"  ✓ 点击URL已获取: {click_url[:60]}...")
            else:
                state.log(f"  ✗ 广告请求失败")
                run_data = {
                    "run": current_run_num,
                    "success": False,
                    "platform": platform,
                    "device": f"{dev.hardware.brand} {dev.hardware.model}",
                    "proxy_ip": real_ip,
                    "proxy_country": target_country,
                    "error": "ad_request_failed",
                    "duration": round(time.time() - run_start_time, 2),
                }
                state.update_stats(run_data)
                time.sleep(_rnd.uniform(5, 15))
                continue

            if state.should_stop():
                state.log("═══ 自动化循环已停止 ═══")
                break

            state.set_phase(3)
            state.log("─ Phase 3: 曝光上报 ─")
            view_dur = _rnd.uniform(4.0, 12.0)
            attention_level = _rnd.choice(["high", "medium", "low"])
            proxy_status_str = f"[通过代理: {real_ip}]" if proxy_actually_used else "[直连网络]"
            if attention_level == "high":
                state.log(f"  {proxy_status_str} 用户正在专注观看广告... ({view_dur:.1f}秒)")
            elif attention_level == "medium":
                state.log(f"  {proxy_status_str} 用户边浏览边观看广告... ({view_dur:.1f}秒)")
            else:
                state.log(f"  {proxy_status_str} 用户随意浏览广告... ({view_dur:.1f}秒)")
            view_stopped = False
            for i in range(int(view_dur)):
                if state.should_stop():
                    state.log("═══ 自动化循环已停止 ═══")
                    view_stopped = True
                    break
                time.sleep(1.0)
            if view_stopped:
                break
            scroll_events = _rnd.randint(0, 3)
            if scroll_events > 0:
                state.log(f"  [模拟] 用户滚动屏幕 {scroll_events} 次")
            imp_ok = False
            if ad_response and impression_token:
                imp_ok = web_sdk.send_impression(impression_token=impression_token, view_duration=view_dur)
                state.log(f"  观看时长: {view_dur:.1f}s → 曝光{'已通过代理上报' if proxy_actually_used else '已直连上报'}{'成功' if imp_ok else '失败'}")
            else:
                state.log(f"  观看时长: {view_dur:.1f}s → 无曝光Token，跳过上报")

            if state.should_stop():
                state.log("═══ 自动化循环已停止 ═══")
                break

            state.set_phase(4)
            state.log("─ Phase 4: 点击跳转 ─")
            
            reaction_delay = _rnd.uniform(0.3, 1.0)
            state.log(f"  [模拟] 用户正在考虑是否点击... ({reaction_delay:.1f}秒)")
            time.sleep(reaction_delay)
            
            conversion_values = {
                "saas_enterprise": 800.00,
                "legal_services": 700.00,
                "finance_mortgage": 600.00,
                "real_estate_investing": 500.00,
                "finance_investing_stocks": 400.00,
                "b2b_software": 380.00,
                "finance_insurance_health": 350.00,
                "finance_crypto_trading": 320.00,
                "finance_insurance_life": 280.00,
                "education_professional": 240.00,
                "finance_personal_loans": 200.00,
                "finance_credit_cards_premium": 180.00,
                "finance_debt_consolidation": 150.00,
                "software_subscription": 120.00,
                "ecommerce_high_ticket": 100.00,
            }
            categories = list(conversion_values.keys())
            
            value_weights = {
                "saas_enterprise": 3.5,
                "legal_services": 2.8,
                "finance_mortgage": 2.5,
                "real_estate_investing": 2.0,
                "finance_investing_stocks": 2.2,
                "b2b_software": 2.0,
                "finance_insurance_health": 2.0,
                "finance_crypto_trading": 1.8,
                "finance_insurance_life": 1.5,
                "education_professional": 1.2,
                "finance_personal_loans": 1.2,
                "finance_credit_cards_premium": 1.0,
                "finance_debt_consolidation": 0.8,
                "software_subscription": 0.6,
                "ecommerce_high_ticket": 0.5,
            }
            
            weighted_values = [conversion_values[c] * value_weights[c] for c in categories]
            weights = [v / sum(weighted_values) for v in weighted_values]
            
            ad_category = _rnd.choices(categories, weights=weights, k=1)[0]
            click_success_rate = 0.01
            state.log(f"  [模拟] 广告类别: {ad_category} (价值${conversion_values[ad_category]}) | 预估点击率: {click_success_rate*100:.1f}%")
                
            will_click = _rnd.random() < click_success_rate
            
            click_retries = 0
            if not will_click:
                no_click_reasons = [
                    "User not interested in this category",
                    "User already has similar product",
                    "User finds the offer unattractive",
                    "User decides to skip the ad",
                    "User is distracted by other things"
                ]
                reason = _rnd.choice(no_click_reasons)
                state.log(f"  [模拟] 用户未点击广告 - {reason}")
                click_sent = False
                final_click_url = ad_response.get("clickUrl", "") if ad_response else ""
                click_id = None
            else:
                click_motivations = [
                    "User finds the offer interesting",
                    "User needs this product/service",
                    "The ad is well-targeted",
                    "User wants to learn more",
                    "Attractive pricing or offer"
                ]
                motivation = _rnd.choice(click_motivations)
                state.log(f"  [模拟] 用户决定点击广告 - {motivation}")
                
                click_delay = _rnd.uniform(0.2, 0.6)
                state.log(f"  [模拟] 用户手指移动到广告位置并点击... ({click_delay:.1f}秒)")
                time.sleep(click_delay)
                
                click_sent = False
                click_retries = 0
                max_click_retries = 3
                
                while click_retries < max_click_retries and not click_sent and state.auto_running:
                    if state.should_stop():
                        state.log("═══ 自动化循环已停止 ═══")
                        break
                    click_retries += 1
                    state.log(f"  {proxy_status_str} 发送点击请求... (尝试 {click_retries}/{max_click_retries})")
                    click_url = web_sdk.get_click_url() or click_url
                    if click_url:
                        click_sent = web_sdk.send_click()
                    
                    if click_sent:
                        state.log(f"  ✓ 点击请求发送成功")
                    else:
                        state.log(f"  ✗ 点击请求发送失败")
                
                final_click_url = web_sdk.get_click_url() or click_url

                click_id = None
                from urllib.parse import urlparse, parse_qs
                try:
                    parsed = urlparse(final_click_url)
                    params = parse_qs(parsed.query)
                    for key in ["click_id", "tracking_id", "tid", "clickid", "aff_click_id", "cid", "visitorId"]:
                        if key in params:
                            click_id = params[key][0]
                            break
                except Exception:
                    pass
                
                if click_id:
                    state.log(f"  提取Click ID: {click_id[:16]}...")

            if state.should_stop():
                state.log("═══ 自动化循环已停止 ═══")
                break

            if not click_sent:
                state.log("  [跳过] 用户未点击，跳过落地页和转化归因")
                run_duration = round(time.time() - run_start_time, 2)
                state.log(f"═══ 第 {current_run_num} 次循环完成 (耗时 {run_duration}s) ═══")
                run_data = {
                    "run": current_run_num,
                    "success": True,
                    "platform": platform,
                    "device": f"{dev.hardware.brand} {dev.hardware.model}",
                    "device_fingerprint": dev.device_fingerprint[:16],
                    "proxy_ip": real_ip,
                    "proxy_country": target_country,
                    "proxy_isp": real_isp,
                    "impression_sent": imp_ok,
                    "click_sent": click_sent,
                    "landing_page_loaded": False,
                    "conversion_attributed": False,
                    "view_duration": round(view_dur, 1),
                    "duration": run_duration,
                    "ad_category": ad_category,
                    "conversion_value": 0,
                }
                state.update_stats(run_data)
                time.sleep(_rnd.uniform(5, 15))
                continue

            state.set_phase(5)
            state.log("─ Phase 5: Landing Page ─")
            from utils.network import NetworkClient
            net_client = NetworkClient(device=dev)
            wv = WebViewSimulator(device=dev, network=net_client)
            if click_id:
                net_client.cookies.set("roiify_click_id", click_id, domain="roiify.com")
                wv.set_click_id(click_id)
            
            landing_stay = _rnd.uniform(3.0, 8.0)
            interaction_level = _rnd.choice(["deep", "medium", "light"])
            
            if interaction_level == "deep":
                state.log(f"  {proxy_status_str} 用户深入浏览落地页... (预计停留 {landing_stay:.1f}秒)")
            elif interaction_level == "medium":
                state.log(f"  {proxy_status_str} 用户适度浏览落地页内容... (预计停留 {landing_stay:.1f}秒)")
            else:
                state.log(f"  {proxy_status_str} 用户快速浏览落地页... (预计停留 {landing_stay:.1f}秒)")
            
            landing = {"success": False, "final_url": None, "duration": 0, "error": None}
            landing_success = False
            landing_retries = 0
            max_landing_retries = 2
            
            while landing_retries < max_landing_retries and not landing_success and state.auto_running:
                if state.should_stop():
                    state.log("═══ 自动化循环已停止 ═══")
                    break
                landing_retries += 1
                state.log(f"  {proxy_status_str} 加载广告主落地页... (尝试 {landing_retries}/{max_landing_retries})")
                landing = wv.load_landing_page(
                    url=final_click_url,
                    referrer="https://www.roiify.net/",
                    simulate_behavior=True,
                    stay_duration=landing_stay,
                )
                landing_success = landing.get("success", False)
                
                if landing_success:
                    state.log(f"  ✓ 落地页加载成功")
                    landing_behaviors = {
                        "deep": [
                            "User reads product details thoroughly",
                            "User checks pricing information",
                            "User views customer reviews",
                            "User reads FAQ section",
                        ],
                        "medium": [
                            "User scans main content",
                            "User views key features",
                            "User checks basic pricing",
                        ],
                        "light": [
                            "User quickly scrolls through page",
                            "User only views top section",
                        ],
                    }
                    behavior = _rnd.choice(landing_behaviors.get(interaction_level, landing_behaviors["light"]))
                    state.log(f"  [模拟] {behavior}")
                    button_clicks = _rnd.randint(0, 2)
                    if button_clicks > 0:
                        click_actions = [
                            "点击'立即申请'按钮",
                            "点击'了解更多'查看详细信息",
                            "点击'计算工具'进行贷款计算",
                            "点击'联系客服'咨询",
                            "点击'查看条款'阅读协议",
                            "点击'常见问题'查看FAQ",
                        ]
                        for _ in range(button_clicks):
                            action = _rnd.choice(click_actions)
                            state.log(f"  [模拟] 用户{action}")
                else:
                    state.log(f"  ✗ 落地页加载失败: {landing.get('error', '未知错误')}")
                    if landing_retries < max_landing_retries and state.auto_running:
                        state.log(f"  [*] 立即刷新重试...")
            
            if landing.get("final_url"):
                final_domain = landing["final_url"].split("/")[2] if "://" in landing["final_url"] else ""
                state.log(f"  落地页域名: {final_domain}")
            state.log(f"  加载结果: {'✓ 成功' if landing['success'] else '✗ WAF拦截/网络错误'}")
            state.log(f"  停留时长: {landing['duration']:.1f}s | 行为事件: {landing.get('behavior_events', 0)}个")

            if state.should_stop():
                state.log("═══ 自动化循环已停止 ═══")
                break

            state.set_phase(6)
            state.log("─ Phase 6: 转化归因 ─")
            
            conv_prob = _rnd.uniform(0.01, 0.03)
            will_convert = _rnd.random() < conv_prob
            actual_value = 0
            state.log(f"  [模拟] 预估转化率: {conv_prob*100:.1f}%")
            
            if not will_convert:
                state.log(f"  [模拟] 用户未完成转化 - 离开页面或放弃注册")
                conv_ok = False
            else:
                state.log(f"  {proxy_status_str} 触发转化事件...")
                conv_value = conversion_values.get(ad_category, 100.00)
                
                conversion_events = [
                    {"event": "register", "multiplier": 1.0, "desc": "用户注册"},
                    {"event": "lead", "multiplier": 0.6, "desc": "提交线索"},
                    {"event": "purchase", "multiplier": 3.0, "desc": "完成购买"},
                    {"event": "subscription", "multiplier": 2.5, "desc": "订阅服务"},
                    {"event": "download", "multiplier": 0.3, "desc": "下载应用"},
                ]
                
                event_weights = [50, 30, 10, 8, 2]
                event_probs = [w / sum(event_weights) for w in event_weights]
                
                selected_event = _rnd.choices(conversion_events, weights=event_probs, k=1)[0]
                actual_value = round(conv_value * selected_event["multiplier"], 2)
                
                wv_conv = wv.simulate_conversion_event(event_name=selected_event["event"], value=actual_value)
                state.log(f"  转化事件: {selected_event['desc']} ({selected_event['event']})")
                state.log(f"  基础价值: ${conv_value} × 倍率: {selected_event['multiplier']}x = ${actual_value}")
                state.log(f"  广告曝光: ✓ 已上报")
                state.log(f"  广告点击: ✓ 已上报")
                state.log(f"  落地页访问: {'✓ 完成' if landing.get('success') else '✗ 被拦截'}")
                state.log(f"  代理状态: {'✓ 所有请求通过代理' if proxy_actually_used else '✗ 未使用代理（直连）'}")
                state.log(f"  说明: 转化事件需广告主落地页集成Roiify SDK后回传")
                conv_ok = click_sent and landing.get("success", False)

            run_duration = round(time.time() - run_start_time, 2)
            state.log(f"═══ 第 {current_run_num} 次循环完成 (耗时 {run_duration}s) ═══")

            run_data = {
                "run": current_run_num,
                "success": True,
                "platform": platform,
                "device": f"{dev.hardware.brand} {dev.hardware.model}",
                "device_fingerprint": dev.device_fingerprint[:16],
                "proxy_ip": real_ip,
                "proxy_country": target_country,
                "proxy_isp": real_isp,
                "impression_sent": imp_ok,
                "click_sent": click_sent,
                "click_retries": click_retries,
                "landing_page_loaded": landing.get("success", False),
                "landing_retries": landing_retries,
                "conversion_attributed": conv_ok,
                "view_duration": round(view_dur, 1),
                "landing_duration": round(landing["duration"], 1),
                "duration": run_duration,
                "ad_category": ad_category,
                "conversion_value": actual_value if conv_ok else 0,
            }
            state.update_stats(run_data)

            with state.lock:
                total = state.stats["total_runs"]
                click_rate = round(state.stats["click_success"] / total * 100, 2) if total > 0 else 0
                conv_rate = round(state.stats["conversion_success"] / total * 100, 2) if total > 0 else 0
                avg_dur = round(state.stats["total_duration"] / total, 2) if total > 0 else 0
            
            state.log(f"  累计统计: {total}次 | 点击率: {click_rate}% | 转化率: {conv_rate}% | 平均时长: {avg_dur}s")

            with state.lock:
                target_imp = state.target_impressions
            if target_imp > 0 and total >= target_imp:
                state.log(f"  ✓ 已达到目标展示量: {total}/{target_imp}")
                state.log("═══ 自动化循环已停止（目标完成） ═══")
                break

            if proxy.enabled:
                state.log(f"  [*] 准备轮换代理会话...")
            
            wait_secs = _rnd.uniform(0.5, 1.5)
            for _ in range(int(wait_secs * 10)):
                if state.should_stop() or not state.auto_running:
                    break
                time.sleep(0.1)

        except Exception as e:
            import traceback
            state.log(f"  [!] 第 {current_run_num} 次循环出错: {str(e)[:100]}")
            run_data = {
                "run": current_run_num,
                "success": False,
                "error": str(e)[:100],
                "duration": 0,
            }
            state.update_stats(run_data)
            wait_secs = _rnd.uniform(0.5, 1.5)
            for _ in range(int(wait_secs * 10)):
                if state.should_stop() or not state.auto_running:
                    break
                time.sleep(0.1)

    with state.lock:
        state.auto_running = False
        state.running = False
    state.log("═══ 自动化循环已停止 ═══")


if __name__ == "__main__":
    main()