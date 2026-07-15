import time
import random
import logging
import os
import sys
from typing import Dict, Optional, List, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device import DeviceInfo, AdResponse, ClickEvent
from config import config
from utils import NetworkClient

logger = logging.getLogger(__name__)


class ClickHandler:
    def __init__(self, device: DeviceInfo, network: Optional[NetworkClient] = None):
        self.device = device
        self.network = network or NetworkClient(device=device)
        self.click_events: List[ClickEvent] = []
        self.last_click: Optional[ClickEvent] = None
        self.last_final_url: Optional[str] = None
        self.last_redirect_chain: List[Dict] = []
        self.last_click_tracking_sent: bool = False

    def handle_click(
        self,
        ad: AdResponse,
        view_duration_before_click: Optional[float] = None,
        click_x: Optional[int] = None,
        click_y: Optional[int] = None,
        send_tracking: bool = True,
    ) -> Tuple[Optional[str], List[Dict]]:
        if not ad.click_url:
            logger.error("Ad has no click URL")
            return None, []

        if view_duration_before_click is None:
            min_t = config.MIN_VIEW_TIME_BEFORE_CLICK
            max_t = min(config.MAX_VIEW_TIME_BEFORE_CLICK, 60)
            view_duration_before_click = random.uniform(min_t, max_t)

        if click_x is None:
            click_x = random.randint(50, self.device.hardware.screen_width - 50)
        if click_y is None:
            click_y = random.randint(100, self.device.hardware.screen_height - 200)

        click_time = int(time.time() * 1000)
        click_event = ClickEvent(
            click_id=ad.click_id,
            ad_id=ad.ad_id,
            device=self.device,
            click_time=click_time,
            click_x=click_x,
            click_y=click_y,
            view_time_before_click=int(view_duration_before_click * 1000),
            is_valid=True,
        )
        self.last_click = click_event
        self.last_click_tracking_sent = False

        logger.info(f"Processing click for ad {ad.ad_id}, click_id={ad.click_id}")
        logger.debug(f"View duration before click: {view_duration_before_click:.1f}s")

        if send_tracking:
            self._send_click_tracking(ad, click_event)

        initial_click_url = self._prepare_click_url(ad, click_event)

        logger.info("Following redirect chain...")
        final_url, redirect_chain = self._follow_redirects(initial_click_url, ad)

        self.last_final_url = final_url
        self.last_redirect_chain = redirect_chain

        click_id_in_url = self._check_click_id_in_url(final_url, ad.click_id)
        if not click_id_in_url:
            logger.warning("click_id may have been lost during redirect chain")
            if final_url:
                final_url = self._ensure_click_id_in_url(final_url, ad.click_id)
                logger.info("Re-added click_id to final URL")

        self.click_events.append(click_event)
        logger.info(f"Click processing complete, final URL: {final_url}")

        return final_url, redirect_chain

    def _send_click_tracking(self, ad: AdResponse, click_event: ClickEvent):
        tracking_params = {
            "click_id": click_event.click_id,
            "ad_id": ad.ad_id,
            "creative_id": ad.creative_id,
            "device_id": self.device.device_id,
            "device_id_type": self.device.device_id_type,
            "event": "click",
            "event_time": click_event.click_time,
            "click_x": click_event.click_x,
            "click_y": click_event.click_y,
            "view_duration": click_event.view_time_before_click,
            "ts": int(time.time() * 1000),
            "sdk_version": config.SDK_VERSION,
            "app_package": self.device.system.app_package_name,
        }

        click_tracking_urls = list(ad.click_tracking_urls)

        for i, url in enumerate(click_tracking_urls):
            if not url:
                continue
            try:
                final_tracker_url = self.network.add_tracking_params(url, tracking_params)
                self.network.get(final_tracker_url, is_browser=False)
                time.sleep(random.uniform(0.05, 0.15))
            except Exception as e:
                logger.debug(f"Click tracker {i} failed: {e}")

        self.last_click_tracking_sent = True

    def _prepare_click_url(self, ad: AdResponse, click_event: ClickEvent) -> str:
        url = ad.click_url
        additional_params = {
            config.CLICK_ID_KEY: click_event.click_id,
            "click_time": click_event.click_time,
            "click_x": click_event.click_x,
            "click_y": click_event.click_y,
            "device_id": self.device.device_id,
            "device_id_type": self.device.device_id_type,
            "gaid": self.device.device_id if self.device.device_id_type == "gaid" else "",
            "idfa": self.device.idfa or "",
            "idfv": self.device.idfv or "",
            "android_id": self.device.android_id or "",
            "ua": self.device.browser.user_agent,
            "lang": self.device.system.locale,
            "os": self.device.system.os_name.lower(),
            "osv": self.device.system.os_version,
            "model": self.device.hardware.model,
            "brand": self.device.hardware.brand,
            "w": self.device.hardware.screen_width,
            "h": self.device.hardware.screen_height,
            "dnt": "0",
            "ref": self.device.system.app_package_name,
        }
        return self.network.add_tracking_params(url, additional_params)

    def _follow_redirects(self, initial_url: str, ad: AdResponse) -> Tuple[Optional[str], List[Dict]]:
        redirect_chain = []
        current_url = initial_url

        try:
            final_url, chain, cookies = self.network.follow_redirect_chain(
                current_url,
                max_redirects=15,
                headers=self._get_browser_headers(),
            )
            redirect_chain = chain
            self.network.cookies.update(cookies)
            return final_url, redirect_chain
        except Exception as e:
            logger.error(f"Redirect chain failed: {e}")
            return current_url, redirect_chain

    def _get_browser_headers(self) -> Dict:
        import re
        chrome_match = re.search(r"Chrome/(\d+)", self.device.browser.user_agent)
        crios_match = re.search(r"CriOS/(\d+)", self.device.browser.user_agent)
        headers = {
            "Referer": f"android-app://{self.device.system.app_package_name}" if self.device.hardware.platform == "android" else self.device.system.app_package_name or config.DEFAULT_APP_PACKAGE,
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA-Platform": f'"{"Android" if self.device.hardware.platform == "android" else "iOS"}"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
        }
        if self.device.hardware.platform == "android":
            headers["X-Requested-With"] = self.device.system.app_package_name or config.DEFAULT_APP_PACKAGE
        if chrome_match:
            cv = chrome_match.group(1)
            headers["Sec-CH-UA"] = (
                f'"Chromium";v="{cv}", "Not=A?Brand";v="24", '
                f'"Google Chrome";v="{cv}"'
            )
        elif crios_match:
            cv = crios_match.group(1)
            headers["Sec-CH-UA"] = (
                f'"Chromium";v="{cv}", "Not=A?Brand";v="24", '
                f'"Google Chrome";v="{cv}"'
            )
        return headers

    def _check_click_id_in_url(self, url: Optional[str], click_id: str) -> bool:
        if not url:
            return False
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            for key in [config.CLICK_ID_KEY, "tracking_id", "tid", "clickid", "aff_click_id"]:
                if key in params and params[key][0] == click_id:
                    return True
            return False
        except Exception:
            return False

    def _ensure_click_id_in_url(self, url: str, click_id: str) -> str:
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            if config.CLICK_ID_KEY not in params:
                params[config.CLICK_ID_KEY] = [click_id]
            new_query = urlencode(params, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
        except Exception as e:
            logger.error(f"Failed to add click_id to URL: {e}")
            return url

    def get_stored_click_id(self) -> Optional[str]:
        if self.last_click:
            return self.last_click.click_id
        return None

    def verify_click_attribution(self, url: Optional[str] = None) -> Dict:
        result = {
            "has_click": self.last_click is not None,
            "click_id": self.get_stored_click_id(),
            "click_tracking_sent": self.last_click_tracking_sent,
            "final_url": self.last_final_url or url,
            "click_id_in_final_url": False,
            "redirect_steps": len(self.last_redirect_chain),
            "device_consistent": True,
        }
        final_url = url or self.last_final_url
        if final_url:
            result["click_id_in_final_url"] = self._check_click_id_in_url(final_url, result["click_id"] or "")
        return result
