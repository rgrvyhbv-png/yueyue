import asyncio
import random
import time
import os
import re
from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass
class BrowserConfig:
    enabled: bool = False
    headless: bool = True
    browser_type: str = "chromium"
    proxy_host: str = ""
    proxy_port: int = 0
    proxy_username: str = ""
    proxy_password: str = ""
    user_agent: str = ""
    viewport_width: int = 375
    viewport_height: int = 812
    timezone: str = ""
    locale: str = ""
    page_timeout: int = 30
    slow_mo: int = 0


class PlaywrightBrowserEngine:
    _instance = None
    _playwright = None
    _browser = None
    _config = None
    _page_counter = 0

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PlaywrightBrowserEngine()
        return cls._instance

    def configure(self, config: BrowserConfig):
        self._config = config

    def is_enabled(self) -> bool:
        return self._config is not None and self._config.enabled

    def _build_proxy_url(self) -> Optional[str]:
        if not self._config:
            return None
        if not self._config.proxy_host or not self._config.proxy_port:
            return None
        if self._config.proxy_username and self._config.proxy_password:
            return f"http://{self._config.proxy_username}:{self._config.proxy_password}@{self._config.proxy_host}:{self._config.proxy_port}"
        return f"http://{self._config.proxy_host}:{self._config.proxy_port}"

    def _launch_browser(self):
        import asyncio
        from playwright.async_api import async_playwright

        async def _launch():
            nonlocal self
            self._playwright = await async_playwright().start()
            browser_type = getattr(self._playwright, self._config.browser_type, self._playwright.chromium)

            launch_options = {
                "headless": self._config.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials",
                    "--disable-web-security",
                    "--disable-features=BlockInsecurePrivateNetworkRequests",
                    "--disable-features=SafeBrowsing",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--window-size=1920,1080",
                    "--disable-infobars",
                    "--disable-notifications",
                    "--disable-extensions",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                ],
            }

            proxy_url = self._build_proxy_url()
            if proxy_url:
                launch_options["proxy"] = {"server": proxy_url}

            self._browser = await browser_type.launch(**launch_options)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_launch())
        loop.close()

    def _create_context(self):
        if not self._browser:
            self._launch_browser()

        context_options = {
            "viewport": {
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            },
            "user_agent": self._config.user_agent or self._generate_random_ua(),
            "locale": self._config.locale or "en-US",
            "timezone_id": self._config.timezone or "America/New_York",
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "storage_state": None,
        }

        if self._config.slow_mo > 0:
            context_options["slow_mo"] = self._config.slow_mo

        return asyncio.get_event_loop().run_until_complete(
            self._browser.new_context(**context_options)
        )

    def _generate_random_ua(self) -> str:
        android_models = [
            "SM-S918B", "SM-S235F", "Pixel 8", "Pixel 7", "SM-A546B",
            "SM-A145F", "OnePlus 12", "Xiaomi 14", "Redmi Note 13", "realme GT 5",
        ]
        android_versions = ["14", "13", "12"]
        chrome_versions = ["126", "125", "124", "123"]

        model = random.choice(android_models)
        android_version = random.choice(android_versions)
        chrome_version = random.choice(chrome_versions)

        return (
            f"Mozilla/5.0 (Linux; Android {android_version}; {model}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36"
        )

    def _apply_stealth(self, page):
        import asyncio

        async def _stealth():
            try:
                from playwright_stealth import stealth_async
                await stealth_async(page)
            except ImportError:
                await self._apply_manual_stealth(page)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_stealth())
        loop.close()

    def _apply_manual_stealth(self, page):
        import asyncio

        async def _manual():
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'zh-CN'],
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Linux armv8l',
                });
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4,
                });
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 4,
                });
                Object.defineProperty(navigator, 'maxTouchPoints', {
                    get: () => 1,
                });
                Object.defineProperty(window, 'chrome', {
                    value: {
                        runtime: {},
                        loadTimes: () => ({
                            commitLoadTime: Date.now() / 1000,
                            connectionInfo: 'http/1.1',
                            finishDocumentLoadTime: Date.now() / 1000 + 0.1,
                            finishLoadTime: Date.now() / 1000 + 0.2,
                            firstPaintTime: Date.now() / 1000 + 0.05,
                            navigationType: 'Reload',
                            npPluginCount: 3,
                            pageLoadTime: Date.now() / 1000 + 0.3,
                            startLoadTime: Date.now() / 1000 - 0.1,
                        }),
                    },
                });
            """)

            await page.add_init_script("""
                Math.random = (function() {
                    var original = Math.random;
                    var seed = 0x12345678;
                    return function() {
                        seed = (seed * 9301 + 49297) % 233280;
                        return seed / 233280;
                    };
                })();
            """)

            await page.evaluate("""
                window.crypto.getRandomValues = function(typedArray) {
                    for (var i = 0; i < typedArray.length; i++) {
                        typedArray[i] = Math.floor(Math.random() * 256);
                    }
                };
            """)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_manual())
        loop.close()

    def load_page(
        self,
        url: str,
        referrer: Optional[str] = None,
        stay_duration: float = 5.0,
        simulate_behavior: bool = True,
    ) -> Dict:
        if not self.is_enabled():
            return {
                "success": False,
                "error": "Browser not enabled",
            }

        result = {
            "success": False,
            "url": url,
            "final_url": None,
            "status_code": 200,
            "page_loaded": False,
            "content": "",
            "behavior_events": 0,
            "click_id": None,
            "duration": 0,
            "error": None,
            "browser_type": "real",
        }

        start_time = time.time()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _run():
                if not self._browser:
                    self._playwright = await async_playwright().start()
                    browser_type = getattr(self._playwright, self._config.browser_type, self._playwright.chromium)

                    launch_options = {
                        "headless": self._config.headless,
                        "args": [
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--window-size=1920,1080",
                        ],
                    }

                    proxy_url = self._build_proxy_url()
                    if proxy_url:
                        launch_options["proxy"] = {"server": proxy_url}

                    self._browser = await browser_type.launch(**launch_options)

                context = await self._browser.new_context(
                    viewport={
                        "width": self._config.viewport_width,
                        "height": self._config.viewport_height,
                    },
                    user_agent=self._config.user_agent or self._generate_random_ua(),
                    locale=self._config.locale or "en-US",
                    timezone_id=self._config.timezone or "America/New_York",
                    ignore_https_errors=True,
                )

                page = await context.new_page()

                try:
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    """)

                    try:
                        from playwright_stealth import stealth_async
                        await stealth_async(page)
                    except ImportError:
                        pass

                    if referrer:
                        await page.goto(referrer, wait_until="domcontentloaded", timeout=10000)
                        await page.wait_for_timeout(random.randint(500, 1000))

                    await page.goto(url, wait_until="domcontentloaded", timeout=self._config.page_timeout * 1000)

                    result["final_url"] = page.url
                    result["page_loaded"] = True
                    result["content"] = ""

                    click_id = None
                    for key in ["click_id", "tracking_id", "tid", "clickid", "cid", "vid"]:
                        match = re.search(rf'[?&]{key}=([^&"\']+)', page.url)
                        if match:
                            click_id = match.group(1)
                            break

                    if not click_id:
                        cookies = await context.cookies()
                        for cookie in cookies:
                            if cookie["name"].lower() in ["click_id", "tracking_id", "vid", "roiify_click_id"]:
                                click_id = cookie["value"]
                                break

                    result["click_id"] = click_id

                    if simulate_behavior:
                        scroll_count = random.randint(2, 5)
                        for _ in range(scroll_count):
                            scroll_y = random.randint(100, 600)
                            await page.evaluate(f"window.scrollBy(0, {scroll_y})")
                            await page.wait_for_timeout(random.randint(300, 800))

                        click_prob = random.random()
                        if click_prob > 0.5:
                            try:
                                buttons = await page.query_selector_all("button, a, [role='button'], .btn")
                                if buttons:
                                    button = buttons[random.randint(0, min(len(buttons) - 1, 3))]
                                    await button.click(timeout=3000)
                                    await page.wait_for_timeout(random.randint(500, 1500))
                            except Exception:
                                pass

                        await page.wait_for_timeout(int(stay_duration * 1000))
                        result["behavior_events"] = random.randint(3, 10)

                    await page.wait_for_timeout(random.randint(500, 1500))
                    result["success"] = True

                finally:
                    await page.close()
                    await context.close()

            loop.run_until_complete(_run())
            loop.close()

        except Exception as e:
            result["error"] = str(e)[:200]

        result["duration"] = time.time() - start_time
        return result

    def get_screenshot(self, url: str) -> Optional[bytes]:
        if not self.is_enabled():
            return None

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def capture():
                if not self._browser:
                    self._playwright = await async_playwright().start()
                    browser_type = getattr(self._playwright, self._config.browser_type, self._playwright.chromium)
                    self._browser = await browser_type.launch(headless=True)

                context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,
                )

                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=15000)
                screenshot = await page.screenshot(full_page=True)
                await page.close()
                await context.close()
                return screenshot

            result = loop.run_until_complete(capture())
            loop.close()
            return result
        except Exception:
            return None

    def close(self):
        if self._browser:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._browser.close())
                loop.close()
            except Exception:
                pass
        if self._playwright:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._playwright.stop())
                loop.close()
            except Exception:
                pass
        self._instance = None


browser_engine = PlaywrightBrowserEngine.get_instance()


def init_browser_engine(config: BrowserConfig) -> bool:
    global browser_engine

    browser_engine.configure(config)

    if config.enabled:
        try:
            import playwright
            playwright.__version__
            try:
                import playwright_stealth
                playwright_stealth.__version__
            except ImportError:
                pass
            return True
        except ImportError:
            return False
    return False
