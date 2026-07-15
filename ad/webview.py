import time
import random
import logging
import os
import sys
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device import DeviceInfo
from config import config
from utils import NetworkClient
from ad.behavior_simulator import BehaviorSimulator

logger = logging.getLogger(__name__)


class WebViewSimulator:
    def __init__(self, device: DeviceInfo, network: Optional[NetworkClient] = None):
        self.device = device
        self.network = network or NetworkClient(device=device)
        self.behavior = BehaviorSimulator(device)
        self.current_url: Optional[str] = None
        self.page_loaded = False
        self.page_load_time: Optional[int] = None
        self.referrer: Optional[str] = None
        self.cookies_consent_given = False
        self.fingerprint_sent = False
        self.page_scripts_executed = False
        self.page_resources_loaded: List[str] = []
        self.tracking_pixels_fired: List[str] = []
        self.session_events: List[Dict] = []

    def load_landing_page(
        self,
        url: str,
        referrer: Optional[str] = None,
        simulate_behavior: bool = True,
        stay_duration: Optional[float] = None,
    ) -> Dict:
        result = {
            "success": False,
            "url": url,
            "final_url": None,
            "status_code": None,
            "page_loaded": False,
            "fingerprint_sent": False,
            "tracking_pixels": 0,
            "behavior_events": 0,
            "click_id_retained": False,
            "duration": 0,
            "error": None,
        }

        if stay_duration is None:
            stay_duration = random.uniform(
                config.MIN_LANDING_PAGE_STAY,
                config.MAX_LANDING_PAGE_STAY
            )

        self.referrer = referrer or self.device.system.app_package_name
        self.current_url = url
        start_time = time.time()

        logger.info(f"Loading landing page: {url[:100]}...")

        max_retries = 5
        response = None
        current_network = self.network
        
        for attempt in range(max_retries):
            try:
                headers = self._get_webview_headers()
                response = current_network.get(
                    url,
                    headers=headers,
                    is_browser=True,
                    allow_redirects=True,
                    timeout=10,
                )
                result["status_code"] = response.status_code
                result["final_url"] = response.url

                if response.status_code == 200:
                    self.current_url = response.url
                    self.page_loaded = True
                    self.page_load_time = int(time.time() * 1000)
                    result["page_loaded"] = True

                    self._fire_page_view_events(response.url, referrer)
                    self._send_fingerprint_to_tracker(response.url)
                    self.fingerprint_sent = True
                    result["fingerprint_sent"] = True

                    tracking_pixels = self._detect_and_fire_tracking_pixels(response.text, response.url)
                    self.tracking_pixels_fired.extend(tracking_pixels)
                    result["tracking_pixels"] = len(tracking_pixels)

                    click_id = self._extract_click_id_from_url(response.url)
                    if click_id:
                        result["click_id_retained"] = True
                        self._fire_click_attribution_event(click_id, response.url)

                    if simulate_behavior:
                        num_events = random.randint(
                            config.MIN_BEHAVIOR_EVENTS,
                            config.MAX_BEHAVIOR_EVENTS
                        )
                        events = self.behavior.simulate_page_behavior(
                            url=response.url,
                            duration=stay_duration,
                            num_events=num_events,
                            network=self.network,
                        )
                        self.session_events.extend(events)
                        result["behavior_events"] = len(events)

                        behavior_start = time.time()
                        self._simulate_scroll_depth()
                        self._simulate_touch_interaction()
                        behavior_duration = time.time() - behavior_start
                        
                        # 发送行为事件到追踪服务器
                        self._send_behavior_events(response.url)
                        
                        remaining = max(0, stay_duration - behavior_duration)
                        if remaining > 0:
                            time.sleep(remaining)
                    else:
                        time.sleep(stay_duration)

                    result["success"] = True
                    break
                else:
                    if attempt < max_retries - 1:
                        logger.info(f"Page failed with {response.status_code}, refreshing immediately... (attempt {attempt + 1}/{max_retries})")
                        current_network = NetworkClient(device=self.device)
                        continue
                    result["error"] = f"HTTP {response.status_code}"
                    logger.warning(f"Landing page returned {response.status_code}")
                    break

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"Page load failed, user refreshing immediately... (attempt {attempt + 1}/{max_retries})")
                    current_network = NetworkClient(device=self.device)
                    continue
                result["error"] = str(e)
                logger.error(f"Failed to load landing page after {max_retries} attempts: {e}")
                break

        if not result["success"]:
            self.current_url = url
            result["final_url"] = url
            if simulate_behavior:
                time.sleep(min(3, stay_duration))
            else:
                time.sleep(1)

        result["duration"] = time.time() - start_time
        logger.info(f"Landing page session completed: {result['duration']:.1f}s")

        return result

    def _get_webview_headers(self) -> Dict:
        import re
        is_android = self.device.hardware.platform == "android"
        ua = self.device.browser.user_agent
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": self.device.browser.accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-CH-TimeZone": self.device.system.timezone,
            "Sec-CH-Locale": self.device.system.locale,
        }
        if is_android:
            headers["Referer"] = self.referrer or f"android-app://{self.device.system.app_package_name}"
            headers["X-Requested-With"] = self.device.system.app_package_name or config.DEFAULT_APP_PACKAGE
            headers["Sec-CH-UA-Mobile"] = "?1"
            headers["Sec-CH-UA-Platform"] = '"Android"'
            headers["Sec-CH-UA-Arch"] = '"arm64"'
        else:
            headers["Referer"] = self.referrer or self.device.system.app_package_name or config.DEFAULT_APP_PACKAGE
            headers["Sec-CH-UA-Mobile"] = "?1"
            headers["Sec-CH-UA-Platform"] = '"iOS"'
            headers["Sec-CH-UA-Arch"] = '"arm64"'

        chrome_match = re.search(r"Chrome/(\d+)", ua)
        crios_match = re.search(r"CriOS/(\d+)", ua)
        if chrome_match:
            cv = chrome_match.group(1)
            headers["Sec-CH-UA"] = (
                f'"Chromium";v="{cv}", "Not=A?Brand";v="24", '
                f'"Google Chrome";v="{cv}"'
            )
            headers["Sec-CH-UA-Full-Version"] = f'"{cv}.0.0.0"'
        elif crios_match:
            cv = crios_match.group(1)
            headers["Sec-CH-UA"] = (
                f'"Chromium";v="{cv}", "Not=A?Brand";v="24", '
                f'"Google Chrome";v="{cv}"'
            )
            headers["Sec-CH-UA-Full-Version"] = f'"{cv}.0.0.0"'
        return headers

    def _extract_chrome_version(self, ua: str) -> str:
        import re
        match = re.search(r"Chrome/(\d+)", ua) or re.search(r"CriOS/(\d+)", ua)
        if match:
            return match.group(1)
        return "125"

    def _fire_page_view_events(self, page_url: str, referrer: Optional[str]):
        view_event_urls = self._build_analytics_endpoints(page_url, "pageview", {
            "url": page_url,
            "ref": referrer or "",
            "t": int(time.time() * 1000),
            "screen": f"{self.device.hardware.screen_width}x{self.device.hardware.screen_height}",
            "vp": f"{self.device.browser.viewport_width}x{self.device.browser.viewport_height}",
            "de": "UTF-8",
            "sd": f"{self.device.browser.color_depth}-bit",
            "ul": self.device.system.locale.replace("-", "_"),
            "je": "1",
            "dpr": str(self.device.browser.device_pixel_ratio),
            "tz": self.device.system.timezone,
            "lang": self.device.system.language,
            "country": self.device.system.country,
            "carrier": self.device.network.carrier_name,
            "conn": self.device.network.connection_type,
            "model": self.device.hardware.model,
            "brand": self.device.hardware.brand,
            "os": self.device.system.os_name,
            "osv": self.device.system.os_version,
        })

        for url in view_event_urls:
            try:
                self.network.get(url, is_browser=True, timeout=10)
                time.sleep(random.uniform(0.1, 0.3))
            except Exception as e:
                logger.debug(f"Page view event failed: {e}")

    def _send_behavior_events(self, page_url: str):
        """发送用户行为事件到追踪服务器"""
        if not self.session_events:
            return
        click_id = self._extract_click_id_from_url(self.current_url or page_url)
        events_data = {
            "click_id": click_id or "",
            "visitor_id": self.device.device_id,
            "page_url": page_url,
            "events": self.session_events[-20:],  # 最近20条事件
            "event_count": len(self.session_events),
            "device_info": {
                "model": self.device.hardware.model,
                "os": self.device.system.os_name,
                "os_version": self.device.system.os_version,
                "screen": f"{self.device.hardware.screen_width}x{self.device.hardware.screen_height}",
            },
            "timestamp": int(time.time() * 1000),
        }
        behavior_endpoints = [
            "https://tracking.roiify.com/behavior",
            "https://events.roiify.net/collect",
        ]
        for endpoint in behavior_endpoints:
            try:
                self.network.post(
                    endpoint,
                    json=events_data,
                    is_browser=False,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                logger.debug(f"Behavior events sent to {endpoint}")
            except Exception as e:
                logger.debug(f"Behavior events send failed ({endpoint}): {e}")

    def _send_fingerprint_to_tracker(self, page_url: str):
        """发送设备指纹到追踪服务器"""
        fp_data = {
            "deviceId": self.device.device_id,
            "deviceIdType": self.device.device_id_type,
            "idfa": self.device.idfa or "",
            "gaid": self.device.device_id if self.device.device_id_type == "gaid" else "",
            "androidId": self.device.android_id or "",
            "deviceFingerprint": self.device.device_fingerprint,
            "userAgent": self.device.browser.user_agent,
            "language": self.device.system.locale,
            "timezone": self.device.system.timezone,
            "os": self.device.system.os_name,
            "osVersion": self.device.system.os_version,
            "model": self.device.hardware.model,
            "brand": self.device.hardware.brand,
            "screenWidth": self.device.hardware.screen_width,
            "screenHeight": self.device.hardware.screen_height,
            "carrier": self.device.network.carrier_name,
            "connectionType": self.device.network.connection_type,
            "ip": self.device.network.ip_address,
            "country": self.device.system.country,
            "pageUrl": page_url,
            "timestamp": int(time.time() * 1000),
        }
        fp_endpoints = [
            "https://fp.roiify.net/collect",
            "https://tracking.roiify.com/fingerprint",
        ]
        for endpoint in fp_endpoints:
            try:
                self.network.post(
                    endpoint,
                    json=fp_data,
                    is_browser=False,
                    headers={"Content-Type": "application/json"},
                    timeout=8,
                )
                logger.debug(f"Fingerprint sent to {endpoint}")
            except Exception as e:
                logger.debug(f"Fingerprint send failed ({endpoint}): {e}")
        self.fingerprint_sent = True

    def _detect_and_fire_tracking_pixels(self, page_content: str, page_url: str) -> List[str]:
        """检测并触发落地页中的第三方追踪像素"""
        import re
        pixels_fired = []
        pixel_patterns = [
            r'(?:src|href)=["\'](https?://[^"\']*(?:facebook\.com/tr|google-analytics\.com/collect|doubleclick\.net|pixel\.roiify\.com|t\.roiify\.net)[^"\']*)["\']',
            r'<img[^>]+src=["\'](https?://[^"\']*pixel[^"\']*)["\']',
        ]
        found_urls = set()
        for pattern in pixel_patterns:
            for match in re.finditer(pattern, page_content, re.IGNORECASE):
                found_urls.add(match.group(1))
        for url in found_urls:
            try:
                self.network.get(url, is_browser=True, timeout=5, allow_redirects=True)
                pixels_fired.append(url)
                self.tracking_pixels_fired.append(url)
                logger.debug(f"Tracking pixel fired: {url[:80]}")
            except Exception as e:
                logger.debug(f"Tracking pixel failed: {url[:80]} - {e}")
        return pixels_fired

    def _fire_click_attribution_event(self, click_id: str, page_url: str):
        attribution_params = {
            "click_id": click_id,
            "event": "landing",
            "device_id": self.device.device_id,
            "device_id_type": self.device.device_id_type,
            "idfa": self.device.idfa or "",
            "gaid": self.device.device_id if self.device.device_id_type == "gaid" else "",
            "idfv": self.device.idfv or "",
            "android_id": self.device.android_id or "",
            "ip": self.device.network.ip_address,
            "ua": self.device.browser.user_agent,
            "lang": self.device.system.locale,
            "os": self.device.system.os_name.lower(),
            "osv": self.device.system.os_version,
            "model": self.device.hardware.model,
            "brand": self.device.hardware.brand,
            "fp": self.device.device_fingerprint,
            "url": page_url,
            "ts": int(time.time() * 1000),
        }

        attribution_endpoints = [
            "https://tracking.roiify.com/click/land",
            "https://attribution.roiify.com/landed",
        ]

        for endpoint in attribution_endpoints:
            try:
                self.network.get(
                    endpoint,
                    params=attribution_params,
                    is_browser=True,
                    timeout=10,
                )
                time.sleep(random.uniform(0.1, 0.25))
            except Exception as e:
                logger.debug(f"Click attribution event failed: {e}")

    def _extract_click_id_from_url(self, url: str) -> Optional[str]:
        click_id = None
        if url:
            try:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                for key in [config.CLICK_ID_KEY, "tracking_id", "tid", "clickid", "aff_click_id", "cid", "visitorId", "visitor_id", "vid", "uid"]:
                    if key in params:
                        click_id = params[key][0]
                        break
                if not click_id:
                    fragment = parsed.fragment
                    if fragment:
                        frag_params = parse_qs(fragment)
                        for key in ["click_id", "tracking_id", "tid", "clickid"]:
                            if key in frag_params:
                                click_id = frag_params[key][0]
                                break
            except Exception:
                pass
        if not click_id:
            for cookie in self.network.cookies:
                if cookie.name.lower() in ["zde_vid", "click_id", "tracking_id", "roiify_click_id", "roiify_visitor_id", "visitor_id", "vid"]:
                    click_id = cookie.value
                    break
        if not click_id and hasattr(self, '_stored_click_id'):
            click_id = self._stored_click_id
        return click_id

    def set_click_id(self, click_id: str):
        self._stored_click_id = click_id

    def _build_analytics_endpoints(self, page_url: str, event_type: str, extra_params: Dict) -> List[str]:
        endpoints = []
        base_params = {
            "v": "1",
            "cid": self._generate_client_id(),
            "uip": self.device.network.ip_address,
            "ua": self.device.browser.user_agent,
            "an": self.device.system.app_package_name,
            "av": self.device.system.app_version,
            "aid": self.device.system.app_package_name,
            "cd1": self.device.hardware.model,
            "cd2": self.device.system.os_version,
        }
        base_params.update(extra_params)
        endpoints.append(("https://tracking.roiify.com/event", base_params))
        result = []
        for url, params in endpoints:
            result.append(self.network.add_tracking_params(url, params))
        return result

    def _generate_client_id(self) -> str:
        import hashlib
        raw = f"{self.device.device_id}|{self.device.browser.user_agent}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _simulate_scroll_depth(self):
        scroll_depths = [25, 50, 75, 100]
        depths_reached = sorted(random.sample(scroll_depths, random.randint(1, 3)))
        for depth in depths_reached:
            time.sleep(random.uniform(0.4, 1.0))
            self._fire_scroll_event(depth)

    def _fire_scroll_event(self, depth: int):
        scroll_params = {
            "event": "scroll",
            "depth": str(depth),
            "click_id": self._extract_click_id_from_url(self.current_url or "") or "",
            "visitor_id": self.device.device_id,
            "page_url": self.current_url or "",
            "t": int(time.time() * 1000),
        }
        try:
            self.network.get(
                "https://tracking.roiify.com/event",
                params=scroll_params,
                is_browser=True,
                timeout=5,
            )
        except Exception:
            pass
        try:
            self.network.post(
                "https://events.roiify.net/scroll",
                json=scroll_params,
                is_browser=False,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
        except Exception:
            pass

    def _simulate_touch_interaction(self):
        num_touches = random.randint(2, 6)
        for _ in range(num_touches):
            time.sleep(random.uniform(0.3, 1.2))
            start_x = random.randint(50, self.device.browser.viewport_width - 50)
            start_y = random.randint(100, self.device.browser.viewport_height - 100)
            
            self.session_events.append({
                "type": "touchstart",
                "touches": [{
                    "x": start_x,
                    "y": start_y,
                }],
                "t": int(time.time() * 1000),
            })
            
            move_count = random.randint(0, 3)
            for _ in range(move_count):
                time.sleep(random.uniform(0.05, 0.15))
                delta_x = random.randint(-30, 30)
                delta_y = random.randint(-50, 50)
                start_x = max(10, min(self.device.browser.viewport_width - 10, start_x + delta_x))
                start_y = max(10, min(self.device.browser.viewport_height - 10, start_y + delta_y))
                self.session_events.append({
                    "type": "touchmove",
                    "touches": [{
                        "x": start_x,
                        "y": start_y,
                    }],
                    "t": int(time.time() * 1000),
                })
            
            time.sleep(random.uniform(0.05, 0.2))
            self.session_events.append({
                "type": "touchend",
                "t": int(time.time() * 1000),
            })

    def simulate_conversion_event(
        self,
        event_name: str = "purchase",
        value: float = 0.0,
        currency: str = "USD",
    ) -> Dict:
        result = {
            "success": False,
            "event_name": event_name,
            "click_id": None,
            "postback_sent": False,
            "signature_valid": False,
            "attributed": False,
            "error": None,
        }

        click_id = self._extract_click_id_from_url(self.current_url or "")
        result["click_id"] = click_id

        if not click_id:
            result["error"] = "No click_id found for attribution"
            logger.error("Cannot trigger conversion: no click_id")
            return result

        logger.info(f"Triggering conversion event: {event_name}, click_id={click_id}")

        conversion_params = self._build_conversion_postback(click_id, event_name, value, currency)
        result["signature_valid"] = self._sign_conversion_event(conversion_params)

        postback_endpoints = [
            "https://postback.roiify.com/conversion",
            "https://tracking.roiify.com/postback",
        ]

        for endpoint in postback_endpoints:
            try:
                self.network.post(
                    endpoint,
                    data=conversion_params,
                    is_browser=False,
                    timeout=15,
                )
                result["postback_sent"] = True
                result["success"] = True
                result["attributed"] = True
                time.sleep(random.uniform(0.2, 0.5))
            except Exception as e:
                logger.debug(f"Conversion postback to {endpoint} failed: {e}")

        logger.info(f"Conversion event result: attributed={result['attributed']}")
        return result

    def _build_conversion_postback(
        self,
        click_id: str,
        event_name: str,
        value: float,
        currency: str,
    ) -> Dict:
        event_time = int(time.time() * 1000)
        return {
            "click_id": click_id,
            "event_name": event_name,
            "event_value": value,
            "conversion_value": value,
            "currency": currency,
            "event_time": event_time,
            "device_id": self.device.device_id,
            "device_id_type": self.device.device_id_type,
            "idfa": self.device.idfa or "",
            "gaid": self.device.device_id if self.device.device_id_type == "gaid" else "",
            "idfv": self.device.idfv or "",
            "android_id": self.device.android_id or "",
            "ip": self.device.network.ip_address,
            "ua": self.device.browser.user_agent,
            "fp": self.device.device_fingerprint,
            "os": self.device.system.os_name.lower(),
            "osv": self.device.system.os_version,
            "model": self.device.hardware.model,
            "brand": self.device.hardware.brand,
            "app_package": self.device.system.app_package_name,
            "sdk_version": config.SDK_VERSION,
            "postback_ts": event_time,
        }

    def _sign_conversion_event(self, params: Dict) -> bool:
        from utils import sign_request
        try:
            params["sign"] = sign_request(params, config.REQUEST_SIGN_KEY)
            return True
        except Exception:
            return False

    def get_session_summary(self) -> Dict:
        return {
            "url": self.current_url,
            "page_loaded": self.page_loaded,
            "tracking_pixels": len(self.tracking_pixels_fired),
            "total_events": len(self.session_events),
            "fingerprint_sent": self.fingerprint_sent,
        }
