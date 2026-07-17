import time
import random
import logging
import os
import sys
from typing import Dict, Optional, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device import DeviceFingerprintGenerator, DeviceInfo, AdRequest, AdResponse
from config import config
from utils import (
    generate_request_id,
    generate_click_id,
    generate_impression_id,
    sign_request,
    build_signed_params,
    NetworkClient,
)

logger = logging.getLogger(__name__)


class RoiifySDK:
    def __init__(
        self,
        app_package: Optional[str] = None,
        app_version: Optional[str] = None,
        app_version_code: Optional[int] = None,
        platform: str = "android",
        device: Optional[DeviceInfo] = None,
        device_seed: Optional[int] = None,
    ):
        self.app_package = app_package or config.DEFAULT_APP_PACKAGE
        self.app_version = app_version or config.DEFAULT_APP_VERSION
        self.app_version_code = app_version_code or config.DEFAULT_APP_VERSION_CODE
        self.platform = platform
        self.api_base = config.API_BASE_URL
        self.sdk_version = config.SDK_VERSION

        if device is not None:
            self.device = device
            self.fp_generator = None
        else:
            self.fp_generator = DeviceFingerprintGenerator(platform=platform, seed=device_seed)
            self.device = self.fp_generator.generate()

        self._update_device_app_info()

        self.network = NetworkClient(device=self.device)
        self._request_queue = []
        self._impression_sent = False
        self._click_sent = False
        self._current_ad: Optional[AdResponse] = None
        self._request_id: Optional[str] = None
        self._impression_id: Optional[str] = None
        self._click_id: Optional[str] = None
        self._ad_request_time: Optional[int] = None
        self._ad_show_time: Optional[int] = None

    def _update_device_app_info(self):
        self.device.system.app_package_name = self.app_package
        self.device.system.app_version = self.app_version
        self.device.system.app_version_code = self.app_version_code
        if self.device.hardware.platform == "ios":
            self.device.system.os_name = "iOS"
        else:
            self.device.system.os_name = "Android"

    def _validate_environment(self) -> Tuple[bool, Dict]:
        checks = {}
        all_passed = True

        checks["is_rooted"] = not self.device.system.is_rooted
        checks["is_emulator"] = not self.device.system.is_emulator
        checks["is_vpn"] = not self.device.system.is_vpn_active
        checks["is_proxy"] = not self.device.system.is_proxy_active
        checks["valid_ua"] = bool(self.device.browser.user_agent)
        checks["valid_device_id"] = bool(self.device.device_id) and len(self.device.device_id) > 10
        checks["valid_screen"] = (
            self.device.hardware.screen_width > 0 and
            self.device.hardware.screen_height > 0
        )
        checks["app_package_set"] = bool(self.app_package)

        for check_name, passed in checks.items():
            if not passed:
                all_passed = False
                logger.warning(f"Environment check failed: {check_name}")

        return all_passed, checks

    def _build_ad_request_params(
        self,
        ad_slot_id: str,
        ad_format: str,
        user_keywords: Optional[List[str]] = None,
    ) -> Dict:
        if self.fp_generator:
            base_params = self.fp_generator.get_sdk_request_params()
        else:
            base_params = self._get_device_params_direct()

        ad_params = {
            "request_id": generate_request_id(),
            "slot_id": ad_slot_id,
            "ad_format": ad_format,
            "app_package": self.app_package,
            "app_version": self.app_version,
            "app_version_code": self.app_version_code,
            "sdk_version": self.sdk_version,
            "platform": self.platform,
            "api_version": "3.0",
            "bid_floor": random.randint(100, 500) / 100.0,
            "user_age": self._get_age_from_range(self.device.profile.age_range),
            "user_gender": self.device.profile.gender,
            "user_keywords": ",".join(user_keywords or self.device.profile.interests),
            "session_depth": random.randint(1, 20),
            "session_duration": random.randint(10, 600),
            "install_age_days": int((time.time() - self.device.system.app_install_time) / 86400),
            "last_ad_time": int(time.time()) - random.randint(60, 3600) if random.random() > 0.3 else 0,
            "screen_orientation": random.choice(["portrait", "landscape"]),
            "is_prefetch": random.choice([0, 1]) if ad_format in ["banner", "native"] else 0,
            "volume_on": random.choice([0, 1]),
            "battery_level": random.randint(20, 100),
            "is_charging": random.choice([0, 1]),
            "wifi_connected": 1 if self.device.network.connection_type == "wifi" else 0,
        }

        params = {**base_params, **ad_params}
        signed_params = build_signed_params(params, config.REQUEST_SIGN_KEY)
        return signed_params

    def _get_device_params_direct(self) -> Dict:
        d = self.device
        return {
            "device_id": d.device_id,
            "device_id_type": d.device_id_type,
            "device_model": d.hardware.model,
            "device_brand": d.hardware.brand,
            "device_manufacturer": d.hardware.manufacturer,
            "os": d.system.os_name.lower(),
            "os_version": d.system.os_version,
            "os_api_level": d.system.os_api_level,
            "screen_width": d.hardware.screen_width,
            "screen_height": d.hardware.screen_height,
            "screen_dpi": d.hardware.screen_dpi,
            "pixel_ratio": d.hardware.screen_density,
            "language": d.system.language,
            "locale": d.system.locale,
            "country": d.system.country,
            "timezone": d.system.timezone,
            "time_offset": d.system.time_offset,
            "carrier": d.network.carrier_name,
            "mcc": d.network.mcc,
            "mnc": d.network.mnc,
            "connection_type": d.network.connection_type,
            "user_agent": d.browser.user_agent,
            "build_id": d.system.os_build_id,
            "build_fingerprint": d.system.os_build_fingerprint,
            "gaid": d.device_id if d.device_id_type == "gaid" else "",
            "idfa": d.idfa or "",
            "idfv": d.idfv or "",
            "android_id": d.android_id or "",
            "imei": d.imei or "",
            "oaid": d.oaid or "",
            "is_rooted": int(d.system.is_rooted),
            "is_emulator": int(d.system.is_emulator),
            "is_vpn": int(d.system.is_vpn_active),
            "is_proxy": int(d.system.is_proxy_active),
            "webgl_vendor": d.browser.webgl_vendor,
            "webgl_renderer": d.browser.webgl_renderer,
            "device_fp": d.device_fingerprint,
        }

    def _get_age_from_range(self, age_range: str) -> int:
        age_map = {
            "18-24": random.randint(18, 24),
            "25-34": random.randint(25, 34),
            "35-44": random.randint(35, 44),
            "45-54": random.randint(45, 54),
        }
        return age_map.get(age_range, random.randint(25, 45))

    def request_ad(
        self,
        ad_format: str = "rewarded_video",
        ad_slot_id: Optional[str] = None,
        user_keywords: Optional[List[str]] = None,
    ) -> Optional[AdResponse]:
        if config.ENABLE_ENVIRONMENT_VALIDATION:
            env_ok, checks = self._validate_environment()
            if not env_ok:
                logger.error("Environment validation failed, cannot request ad")
                return None

        import random as _rnd
        slot_id = ad_slot_id or _rnd.choice(config.PLACEMENT_IDS)

        self._ad_request_time = int(time.time() * 1000)
        self._request_id = generate_request_id()
        self._impression_id = generate_impression_id()
        self._click_id = generate_click_id()

        params = self._build_ad_request_params(slot_id, ad_format, user_keywords)

        logger.info(f"Requesting {ad_format} ad from slot {slot_id}")

        try:
            ad_endpoint = f"{self.api_base}/api/v3/ad/request"
            response = self.network.post(ad_endpoint, data=params)

            if response.status_code != 200:
                logger.error(f"Ad request failed: HTTP {response.status_code}")
                return self._create_demo_ad_response(slot_id, ad_format)

            try:
                resp_data = response.json()
            except Exception:
                logger.warning("Failed to parse JSON response, using demo ad")
                return self._create_demo_ad_response(slot_id, ad_format)

            if resp_data.get("code") != 0 and resp_data.get("status") != "success":
                logger.warning(f"API returned non-success: {resp_data.get('msg', 'unknown')}")
                return self._create_demo_ad_response(slot_id, ad_format)

            ad_data = resp_data.get("data", resp_data.get("ad", {}))
            ad_response = self._parse_ad_response(ad_data, slot_id, ad_format)
            self._current_ad = ad_response
            self._impression_sent = False
            self._click_sent = False
            return ad_response

        except Exception as e:
            logger.error(f"Ad request error: {e}")
            return self._create_demo_ad_response(slot_id, ad_format)

    def _create_demo_ad_response(self, slot_id: str, ad_format: str) -> AdResponse:
        demo_campaigns = [
            {
                "ad_id": "demo_ad_001",
                "creative_id": "demo_creative_001",
                "click_url": "https://example.com/click?camp=demo1",
                "impression_url": "https://example.com/impression?camp=demo1",
            },
            {
                "ad_id": "demo_ad_002",
                "creative_id": "demo_creative_002",
                "click_url": "https://example.com/click?camp=demo2",
                "impression_url": "https://example.com/impression?camp=demo2",
            },
        ]
        selected = random.choice(demo_campaigns)
        ad = AdResponse(
            ad_id=selected["ad_id"],
            creative_id=selected["creative_id"],
            click_url=selected["click_url"],
            impression_url=selected["impression_url"],
            click_tracking_urls=[],
            impression_tracking_urls=[],
            creative_type="video" if "video" in ad_format else "html",
            width=self.device.hardware.screen_width,
            height=self.device.hardware.screen_height,
            click_id=self._click_id or generate_click_id(),
        )
        self._current_ad = ad
        self._impression_sent = False
        self._click_sent = False
        return ad

    def _parse_ad_response(self, ad_data: Dict, slot_id: str, ad_format: str) -> AdResponse:
        click_url = ad_data.get("click_url", ad_data.get("landing_url", ""))
        impression_url = ad_data.get("impression_url", ad_data.get("imp_url", ""))
        click_id = ad_data.get("click_id", ad_data.get("tracking_id", self._click_id))
        self._click_id = click_id

        click_tracking_urls = ad_data.get("click_tracking_urls", [])
        impression_tracking_urls = ad_data.get("impression_tracking_urls", [])
        if isinstance(click_tracking_urls, str):
            click_tracking_urls = [click_tracking_urls]
        if isinstance(impression_tracking_urls, str):
            impression_tracking_urls = [impression_tracking_urls]

        extra_trackers = ad_data.get("trackers", {})
        if isinstance(extra_trackers, dict):
            click_tracking_urls.extend(extra_trackers.get("click", []))
            impression_tracking_urls.extend(extra_trackers.get("impression", []))

        return AdResponse(
            ad_id=ad_data.get("ad_id", ad_data.get("id", "")),
            creative_id=ad_data.get("creative_id", ad_data.get("cid", "")),
            click_url=click_url,
            impression_url=impression_url,
            click_tracking_urls=click_tracking_urls,
            impression_tracking_urls=impression_tracking_urls,
            redirect_chain=ad_data.get("redirect_chain", []),
            click_id=click_id,
            creative_type=ad_data.get("creative_type", "video" if "video" in ad_format else "html"),
            width=ad_data.get("width", self.device.hardware.screen_width),
            height=ad_data.get("height", self.device.hardware.screen_height),
        )

    def send_impression(self, view_duration: float = 0) -> bool:
        if not self._current_ad:
            logger.warning("No ad loaded, cannot send impression")
            return False
        if self._impression_sent:
            logger.warning("Impression already sent")
            return True

        self._ad_show_time = int(time.time() * 1000)
        ad = self._current_ad
        tracking_params = self._get_tracking_params()

        impression_urls = [ad.impression_url] + ad.impression_tracking_urls
        for i, url in enumerate(impression_urls):
            if not url:
                continue
            try:
                final_url = self.network.add_tracking_params(url, {
                    **tracking_params,
                    "event": "impression",
                    "event_time": int(time.time() * 1000),
                    "view_duration": int(view_duration * 1000),
                })
                self.network.get(final_url)
                time.sleep(random.uniform(0.05, 0.2))
            except Exception as e:
                logger.debug(f"Impression tracker {i} failed: {e}")

        self._impression_sent = True
        logger.info(f"Impression sent for ad {ad.ad_id}")
        return True

    def get_click_url(self) -> Optional[str]:
        if not self._current_ad:
            return None
        tracking_params = self._get_tracking_params()
        return self.network.add_tracking_params(self._current_ad.click_url, tracking_params)

    def _get_tracking_params(self) -> Dict:
        return {
            "click_id": self._click_id,
            "impression_id": self._impression_id,
            "request_id": self._request_id,
            "ad_id": self._current_ad.ad_id if self._current_ad else "",
            "creative_id": self._current_ad.creative_id if self._current_ad else "",
            "device_id": self.device.device_id,
            "device_id_type": self.device.device_id_type,
            "ts": int(time.time() * 1000),
            "sdk_version": self.sdk_version,
            "app_package": self.app_package,
        }

    def get_device(self) -> DeviceInfo:
        return self.device

    def refresh_device(self, platform: Optional[str] = None):
        if platform:
            self.platform = platform
        self.fp_generator = DeviceFingerprintGenerator(platform=self.platform)
        self.device = self.fp_generator.generate()
        self._update_device_app_info()
        self.network.update_device(self.device)
        self.reset_state()

    def reset_state(self):
        self._current_ad = None
        self._request_id = None
        self._impression_id = None
        self._click_id = None
        self._ad_request_time = None
        self._ad_show_time = None
        self._impression_sent = False
        self._click_sent = False
        self.network.reset()
