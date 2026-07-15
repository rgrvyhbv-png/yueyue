import logging
import time
import random
import argparse
import sys
from typing import Optional, Dict

from .sdk import RoiifySDK
from .device import DeviceFingerprintGenerator
from .ad import ClickHandler, WebViewSimulator
from .config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("roiify")


class RoiifyAdPlayer:
    def __init__(
        self,
        platform: str = "android",
        app_package: Optional[str] = None,
        ad_format: str = "rewarded_video",
        device_seed: Optional[int] = None,
    ):
        self.platform = platform
        self.ad_format = ad_format
        self.device_seed = device_seed

        self.app_package = app_package or config.DEFAULT_APP_PACKAGE
        self.sdk = RoiifySDK(
            app_package=self.app_package,
            platform=platform,
            device_seed=device_seed,
        )
        self.device = self.sdk.get_device()
        self.click_handler = ClickHandler(device=self.device, network=self.sdk.network)
        self.webview = WebViewSimulator(device=self.device, network=self.sdk.network)
        self.current_ad = None
        self.session_id = f"session_{int(time.time())}_{random.randint(1000, 9999)}"

        logger.info(f"Initialized RoiifyAdPlayer - Session: {self.session_id}")
        logger.info(f"Platform: {platform}, Device: {self.device.hardware.brand} {self.device.hardware.model}")
        logger.info(f"Device ID ({self.device.device_id_type}): {self.device.device_id}")
        logger.info(f"Fingerprint: {self.device.device_fingerprint[:16]}...")

    def play_ad(
        self,
        ad_format: Optional[str] = None,
        auto_click: bool = True,
        simulate_conversion: bool = True,
        conversion_event: str = "register",
        conversion_value: float = 0.0,
        view_duration: Optional[float] = None,
        stay_duration: Optional[float] = None,
    ) -> Dict:
        fmt = ad_format or self.ad_format
        logger.info("=" * 60)
        logger.info(f"Phase 1: Requesting {fmt} ad from Roiify platform")
        logger.info("=" * 60)

        ad = self.sdk.request_ad(ad_format=fmt)
        if not ad:
            logger.error("Failed to get ad - SDK request phase failed")
            return {"success": False, "phase": "sdk_request", "error": "Ad request failed"}

        self.current_ad = ad
        logger.info(f"Ad received: ad_id={ad.ad_id}, creative_id={ad.creative_id}")
        logger.info(f"Click ID (通行证): {ad.click_id}")

        view_dur = view_duration or random.uniform(
            config.MIN_VIEW_TIME_BEFORE_CLICK + 5,
            min(config.MAX_VIEW_TIME_BEFORE_CLICK, 60)
        )
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Phase 1b: Simulating ad view ({view_dur:.1f}s)")
        logger.info("=" * 60)

        time.sleep(random.uniform(0.5, 2.0))
        ad.events = []
        from .ad.behavior_simulator import BehaviorSimulator
        behavior = BehaviorSimulator(self.device)
        ad_events = behavior.simulate_ad_view_interaction(view_dur)
        logger.info(f"Simulated {len(ad_events)} interaction events during ad view")

        self.sdk.send_impression(view_duration=view_dur)
        logger.info("Impression tracking sent")

        result = {
            "success": True,
            "session_id": self.session_id,
            "ad_id": ad.ad_id,
            "click_id": ad.click_id,
            "creative_id": ad.creative_id,
            "device_id": self.device.device_id,
            "device_id_type": self.device.device_id_type,
            "fingerprint": self.device.device_fingerprint,
            "impression_sent": True,
        }

        if not auto_click:
            logger.info("Auto-click disabled, ad play complete (no click)")
            result["phase_completed"] = "impression"
            return result

        logger.info("")
        logger.info("=" * 60)
        logger.info("Phase 2: Handling click - Establishing trust contract")
        logger.info("=" * 60)
        logger.info(f"View duration before click: {view_dur:.1f}s")

        final_url, redirect_chain = self.click_handler.handle_click(
            ad=ad,
            view_duration_before_click=view_dur,
            send_tracking=True,
        )

        if not final_url:
            logger.error("Click failed - no final URL obtained")
            result["success"] = False
            result["phase"] = "click"
            result["error"] = "No final URL after click"
            return result

        logger.info(f"Redirect chain completed ({len(redirect_chain)} steps)")
        for i, step in enumerate(redirect_chain):
            loc = step.get("location") or "(final)"
            logger.info(f"  Step {i+1}: {step.get('status_code')} -> {loc[:80]}...")

        click_verification = self.click_handler.verify_click_attribution()
        result["click_sent"] = True
        result["click_id_retained"] = click_verification["click_id_in_final_url"]
        result["redirect_steps"] = click_verification["redirect_steps"]
        result["final_url"] = final_url[:150] + "..." if len(final_url) > 150 else final_url

        logger.info(f"Click ID retained in final URL: {click_verification['click_id_in_final_url']}")

        logger.info("")
        logger.info("=" * 60)
        logger.info("Phase 3: Loading landing page - WebView environment")
        logger.info("=" * 60)

        stay_dur = stay_duration or random.uniform(
            config.MIN_LANDING_PAGE_STAY,
            config.MAX_LANDING_PAGE_STAY
        )
        logger.info(f"Simulating landing page visit ({stay_dur:.1f}s)")
        logger.info(f"Ensuring device fingerprint consistency...")
        logger.info(f"  - UA: {self.device.browser.user_agent[:60]}...")
        logger.info(f"  - IP: {self.device.network.ip_address}")
        logger.info(f"  - Screen: {self.device.hardware.screen_width}x{self.device.hardware.screen_height}")
        logger.info(f"  - Fingerprint: {self.device.device_fingerprint}")

        landing_result = self.webview.load_landing_page(
            url=final_url,
            referrer=self.app_package,
            simulate_behavior=True,
            stay_duration=stay_dur,
        )

        result["landing_page_loaded"] = landing_result["page_loaded"]
        result["fingerprint_sent"] = landing_result["fingerprint_sent"]
        result["tracking_pixels"] = landing_result["tracking_pixels"]
        result["behavior_events"] = landing_result["behavior_events"]
        result["page_duration"] = round(landing_result["duration"], 2)
        result["landing_success"] = landing_result["success"]

        if landing_result["success"]:
            logger.info(f"Landing page loaded successfully")
            logger.info(f"Tracking pixels fired: {landing_result['tracking_pixels']}")
            logger.info(f"Behavior events simulated: {landing_result['behavior_events']}")
        else:
            logger.warning(f"Landing page issue: {landing_result.get('error', 'unknown')}")

        if simulate_conversion:
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Phase 4: Triggering conversion event - {conversion_event}")
            logger.info("=" * 60)

            time.sleep(random.uniform(2.0, 10.0))

            conversion_result = self.webview.simulate_conversion_event(
                event_name=conversion_event,
                value=conversion_value,
                currency="USD",
            )

            result["conversion_triggered"] = conversion_result["success"]
            result["conversion_attributed"] = conversion_result["attributed"]
            result["conversion_postback"] = conversion_result["postback_sent"]
            result["conversion_event"] = conversion_event

            if conversion_result["attributed"]:
                logger.info("Conversion postback sent - attribution complete")
                logger.info("  Closed-loop attribution: SUCCESS")
            else:
                logger.warning(f"Conversion issue: {conversion_result.get('error', 'postback may have failed')}")

        logger.info("")
        logger.info("=" * 60)
        logger.info("Session Complete - Summary")
        logger.info("=" * 60)
        for key in ["ad_id", "click_id", "impression_sent", "click_sent",
                    "click_id_retained", "landing_page_loaded", "fingerprint_sent",
                    "conversion_attributed"]:
            if key in result:
                status = "✓" if result[key] else "✗"
                logger.info(f"  {status} {key}: {result[key]}")

        return result

    def run_demo_flow(self, num_ads: int = 1):
        print("\n" + "╔" + "═" * 58 + "╗")
        print("║" + " Roiify Ad Playback System - Demo Flow ".center(58) + "║")
        print("║" + " Simulating Real Device & Ad Conversion Pipeline ".center(58) + "║")
        print("╚" + "═" * 58 + "╝\n")

        results = []
        for i in range(num_ads):
            if num_ads > 1:
                logger.info(f"\n--- Ad {i+1}/{num_ads} ---\n")
                self.sdk.refresh_device()
                self.device = self.sdk.get_device()
                self.click_handler = ClickHandler(device=self.device, network=self.sdk.network)
                self.webview = WebViewSimulator(device=self.device, network=self.sdk.network)
                time.sleep(random.uniform(30, 120))

            events = ["register", "install", "purchase", "tutorial_complete"]
            result = self.play_ad(
                auto_click=True,
                simulate_conversion=True,
                conversion_event=random.choice(events),
                conversion_value=round(random.uniform(0, 50), 2) if random.random() > 0.3 else 0,
            )
            results.append(result)

        print("\n" + "=" * 60)
        print(f"Demo complete - {len(results)} ad(s) processed")
        print("=" * 60)
        return results


def main():
    parser = argparse.ArgumentParser(description="Roiify Ad Playback System - Real Device Simulation")
    parser.add_argument("--platform", type=str, default="android", choices=["android", "ios"],
                        help="Target platform (android/ios)")
    parser.add_argument("--package", type=str, default=None,
                        help="App package name")
    parser.add_argument("--format", type=str, default="rewarded_video",
                        choices=["rewarded_video", "interstitial", "banner", "native"],
                        help="Ad format")
    parser.add_argument("--count", type=int, default=1,
                        help="Number of ads to play")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible device profile")
    parser.add_argument("--no-click", action="store_true",
                        help="Don't auto-click the ad")
    parser.add_argument("--no-conversion", action="store_true",
                        help="Don't simulate conversion event")
    parser.add_argument("--conversion-event", type=str, default="register",
                        help="Conversion event name")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        player = RoiifyAdPlayer(
            platform=args.platform,
            app_package=args.package,
            ad_format=args.format,
            device_seed=args.seed,
        )

        if args.count == 1:
            player.play_ad(
                auto_click=not args.no_click,
                simulate_conversion=not args.no_conversion,
                conversion_event=args.conversion_event,
            )
        else:
            player.run_demo_flow(num_ads=args.count)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
