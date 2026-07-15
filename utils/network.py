import time
import random
import logging
import os
import sys
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device import DeviceInfo
from config import config, proxy

logger = logging.getLogger(__name__)


class NetworkClient:
    def __init__(self, device: Optional[DeviceInfo] = None, session: Optional[requests.Session] = None):
        self.device = device
        self.session = session or self._create_session()
        self.cookies = requests.cookies.RequestsCookieJar()
        self.request_history = []

    def _create_session(self, rotate_proxy: bool = False) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if proxy.enabled:
            proxies = proxy.get_proxies_dict(new_session=rotate_proxy)
            if proxies:
                session.proxies.update(proxies)
                logger.debug(f"Proxy configured: {proxy.host}:{proxy.port}")
        elif config.PROXY_ENABLED and config.PROXY_URL:
            session.proxies = {"http": config.PROXY_URL, "https": config.PROXY_URL}

        return session

    def _get_headers(self, additional_headers: Optional[Dict] = None, is_browser: bool = False) -> Dict:
        headers = {}
        if self.device is not None:
            if is_browser:
                is_ios = "iPhone" in self.device.browser.user_agent or "iPad" in self.device.browser.user_agent
                is_android = "Android" in self.device.browser.user_agent
                chrome_version = ""
                if "Chrome/" in self.device.browser.user_agent:
                    chrome_version = self.device.browser.user_agent.split("Chrome/")[1].split(" ")[0].split(".")[0]
                elif "CriOS/" in self.device.browser.user_agent:
                    chrome_version = self.device.browser.user_agent.split("CriOS/")[1].split(" ")[0].split(".")[0]
                sec_ch_ua = ""
                sec_ch_platform = '"Windows"'
                if chrome_version:
                    if is_ios:
                        sec_ch_platform = '"iOS"'
                    elif is_android:
                        sec_ch_platform = '"Android"'
                    sec_ch_ua = f'"Chromium";v="{chrome_version}", "Not=A?Brand";v="24", "Google Chrome";v="{chrome_version}"'
                headers = {
                    "User-Agent": self.device.browser.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": self.device.browser.accept_language,
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
                if sec_ch_ua:
                    headers["Sec-Ch-Ua"] = sec_ch_ua
                    headers["Sec-Ch-Ua-Mobile"] = "?1" if (is_android or is_ios) else "?0"
                    headers["Sec-Ch-Ua-Platform"] = sec_ch_platform
            else:
                headers = config.HTTP_HEADERS.copy()
                headers["User-Agent"] = self.device.browser.user_agent
                headers["X-Device-Model"] = self.device.hardware.model
                headers["X-Device-Brand"] = self.device.hardware.brand
                headers["X-OS"] = self.device.system.os_name
                headers["X-OS-Version"] = self.device.system.os_version
                headers["X-App-Package"] = self.device.system.app_package_name or config.DEFAULT_APP_PACKAGE
                headers["X-Carrier"] = self.device.network.carrier_name
                headers["X-Connection-Type"] = self.device.network.connection_type
        else:
            headers = config.HTTP_HEADERS.copy()

        if additional_headers:
            headers.update(additional_headers)
        return headers

    def _simulate_network_delay(self, min_ms: int = 50, max_ms: int = 500):
        delay = random.uniform(min_ms, max_ms) / 1000.0
        time.sleep(delay)

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        is_browser: bool = False,
        timeout: Optional[int] = None,
        allow_redirects: bool = False,
    ) -> requests.Response:
        self._simulate_network_delay()
        request_headers = self._get_headers(headers, is_browser)
        timeout = timeout or config.API_TIMEOUT

        request_info = {
            "method": method,
            "url": url,
            "params": params,
            "timestamp": time.time(),
        }

        if config.ENABLE_REQUEST_LOGGING:
            logger.debug(f"Request: {method} {url}")

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=request_headers,
            cookies=self.cookies,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )

        self.cookies.update(response.cookies)

        request_info["status_code"] = response.status_code
        request_info["response_time"] = time.time() - request_info["timestamp"]
        self.request_history.append(request_info)

        if config.ENABLE_REQUEST_LOGGING:
            logger.debug(f"Response: {response.status_code} ({request_info['response_time']:.3f}s)")

        return response

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def follow_redirect_chain(
        self,
        url: str,
        max_redirects: int = 10,
        headers: Optional[Dict] = None,
    ) -> Tuple[str, list, requests.cookies.RequestsCookieJar]:
        current_url = url
        redirect_history = []
        final_cookies = requests.cookies.RequestsCookieJar()

        for i in range(max_redirects):
            try:
                response = self.get(
                    current_url,
                    headers=headers,
                    is_browser=True,
                    allow_redirects=False,
                )
                final_cookies.update(response.cookies)

                if response.status_code in (301, 302, 303, 307, 308):
                    next_url = response.headers.get("Location")
                    if not next_url:
                        break
                    next_url = urljoin(current_url, next_url)
                    redirect_history.append({
                        "url": current_url,
                        "status_code": response.status_code,
                        "location": next_url,
                        "step": i,
                    })
                    current_url = next_url
                    self._simulate_network_delay(100, 300)
                else:
                    redirect_history.append({
                        "url": current_url,
                        "status_code": response.status_code,
                        "location": None,
                        "step": i,
                    })
                    break
            except Exception as e:
                logger.error(f"Redirect error at {current_url}: {e}")
                break

        return current_url, redirect_history, final_cookies

    def add_tracking_params(self, url: str, params: Dict[str, Any]) -> str:
        parsed = urlparse(url)
        existing_params = parse_qs(parsed.query, keep_blank_values=True)
        for k, v in params.items():
            if v is not None:
                existing_params[k] = [str(v)]
        new_query = urlencode(existing_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def extract_tracking_params(self, url: str) -> Dict[str, str]:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        return {k: v[0] for k, v in params.items() if v}

    def update_device(self, device: DeviceInfo):
        self.device = device

    def reset(self, rotate_proxy: bool = False):
        self.session = self._create_session(rotate_proxy=rotate_proxy)
        self.cookies = requests.cookies.RequestsCookieJar()
        self.request_history = []
        if rotate_proxy:
            logger.debug("NetworkClient reset with proxy rotation")
