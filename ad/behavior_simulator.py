import time
import random
import math
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device import DeviceInfo
from utils import NetworkClient

logger = logging.getLogger(__name__)


class BehaviorSimulator:
    def __init__(self, device: DeviceInfo):
        self.device = device
        self.events: List[Dict] = []
        self.last_touch_pos: Optional[Tuple[int, int]] = None
        self.last_scroll_y = 0
        self.page_start_time: Optional[int] = None

    def simulate_page_behavior(
        self,
        url: str,
        duration: float = 30.0,
        num_events: int = 8,
        network: Optional[NetworkClient] = None,
    ) -> List[Dict]:
        self.page_start_time = int(time.time() * 1000)
        events = []

        current_pos = (
            random.randint(100, self.device.browser.viewport_width - 100),
            random.randint(100, self.device.browser.viewport_height - 100),
        )
        self.last_touch_pos = current_pos
        current_scroll = 0

        events.append(self._make_event("pageload", current_pos, current_scroll))
        
        remaining = duration
        
        page_wait = random.uniform(0.5, 1.5)
        time.sleep(min(page_wait, remaining))
        remaining -= page_wait

        interaction_pattern = random.choice(["explore", "read", "scan", "focus"])
        
        if interaction_pattern == "explore":
            for i in range(min(num_events, 5)):
                target_x = random.randint(20, self.device.browser.viewport_width - 20)
                target_y = random.randint(20, self.device.browser.viewport_height - 20)
                
                move_events = self._generate_touch_movement(current_pos, current_scroll)
                events.extend(move_events)
                current_pos = (target_x, target_y)

                if random.random() > 0.4:
                    scroll_delta = random.randint(150, 500)
                    current_scroll += scroll_delta
                    events.append(self._make_event("scroll", current_pos, current_scroll))

                if random.random() > 0.7:
                    events.append(self._make_event("tap", current_pos, current_scroll))

                event_delay = min(random.uniform(0.4, 1.2), remaining)
                time.sleep(event_delay)
                remaining -= event_delay
                if remaining <= 0:
                    break
        elif interaction_pattern == "read":
            for i in range(min(num_events, 4)):
                scroll_delta = random.randint(200, 400)
                current_scroll += scroll_delta
                scroll_events, current_scroll = self._generate_scroll(current_scroll)
                events.extend(scroll_events)

                if random.random() > 0.6:
                    target_x = random.randint(50, self.device.browser.viewport_width - 50)
                    target_y = random.randint(50, self.device.browser.viewport_height - 50)
                    events.append(self._make_event("touchmove", (target_x, target_y), current_scroll))
                    current_pos = (target_x, target_y)

                event_delay = min(random.uniform(1.0, 2.0), remaining)
                time.sleep(event_delay)
                remaining -= event_delay
                if remaining <= 0:
                    break
        elif interaction_pattern == "scan":
            for i in range(min(num_events, 3)):
                target_x = random.randint(20, self.device.browser.viewport_width - 20)
                target_y = random.randint(20, self.device.browser.viewport_height - 20)
                events.append(self._make_event("touchmove", (target_x, target_y), current_scroll))
                current_pos = (target_x, target_y)

                scroll_delta = random.randint(300, 800)
                current_scroll += scroll_delta
                events.append(self._make_event("scroll", current_pos, current_scroll))

                event_delay = min(random.uniform(0.2, 0.6), remaining)
                time.sleep(event_delay)
                remaining -= event_delay
                if remaining <= 0:
                    break
        else:
            focus_y = random.randint(100, self.device.browser.viewport_height - 200)
            for i in range(min(num_events, 3)):
                target_x = random.randint(50, self.device.browser.viewport_width - 50)
                target_y = focus_y + random.randint(-50, 50)
                move_events = self._generate_touch_movement(current_pos, current_scroll)
                events.extend(move_events)
                current_pos = (target_x, target_y)

                if random.random() > 0.5:
                    events.append(self._make_event("tap", current_pos, current_scroll))

                event_delay = min(random.uniform(0.6, 1.5), remaining)
                time.sleep(event_delay)
                remaining -= event_delay
                if remaining <= 0:
                    break

        if remaining > 0:
            time.sleep(remaining)

        self.events.extend(events)
        return events

    def _make_event(self, event_type: str, pos: Tuple[int, int], scroll_y: int, **extra) -> Dict:
        t = int(time.time() * 1000)
        event = {
            "type": event_type,
            "x": pos[0],
            "y": pos[1],
            "scroll_y": scroll_y,
            "t": t,
            "ts": t - (self.page_start_time or t),
        }
        event.update(extra)
        return event

    def _generate_touch_movement(
        self,
        from_pos: Tuple[int, int],
        scroll_y: int,
    ) -> List[Dict]:
        events = []
        target_x = random.randint(20, self.device.browser.viewport_width - 20)
        target_y = random.randint(20, self.device.browser.viewport_height - 20)

        events.append(self._make_event("touchstart", from_pos, scroll_y))
        time.sleep(random.uniform(0.01, 0.03))

        distance = math.sqrt((target_x - from_pos[0]) ** 2 + (target_y - from_pos[1]) ** 2)
        steps = max(3, min(15, int(distance / 30)))

        for i in range(steps):
            progress = (i + 1) / steps
            bezier_progress = self._ease_in_out_quad(progress)
            noise_x = random.gauss(0, 3) * (1 - progress)
            noise_y = random.gauss(0, 3) * (1 - progress)

            x = int(from_pos[0] + (target_x - from_pos[0]) * bezier_progress + noise_x)
            y = int(from_pos[1] + (target_y - from_pos[1]) * bezier_progress + noise_y)

            x = max(0, min(x, self.device.browser.viewport_width))
            y = max(0, min(y, self.device.browser.viewport_height))

            events.append(self._make_event("touchmove", (x, y), scroll_y))
            time.sleep(random.uniform(0.02, 0.08))

        events.append(self._make_event("touchend", (target_x, target_y), scroll_y))
        time.sleep(random.uniform(0.01, 0.03))

        return events

    def _generate_scroll(self, current_scroll: int) -> Tuple[List[Dict], int]:
        events = []
        direction = random.choice([-1, 1]) if current_scroll > 0 else 1
        scroll_amount = direction * random.randint(100, 600)
        target_scroll = max(0, current_scroll + scroll_amount)

        scroll_steps = max(5, min(20, int(abs(scroll_amount) / 50)))
        for i in range(scroll_steps):
            progress = (i + 1) / scroll_steps
            eased_progress = self._ease_out_cubic(progress)
            pos_y = int(current_scroll + (target_scroll - current_scroll) * eased_progress)
            pos_x = random.randint(50, self.device.browser.viewport_width - 50)
            pos_y_clamped = random.randint(50, self.device.browser.viewport_height - 50)
            events.append(self._make_event("scroll", (pos_x, pos_y_clamped), pos_y))
            time.sleep(random.uniform(0.02, 0.08))

        if random.random() > 0.7:
            time.sleep(random.uniform(0.5, 2.0))

        return events, target_scroll

    def _generate_hover(self, pos: Tuple[int, int], scroll_y: int) -> Dict:
        hover_x = pos[0] + random.randint(-100, 100)
        hover_y = pos[1] + random.randint(-100, 100)
        hover_x = max(10, min(hover_x, self.device.browser.viewport_width - 10))
        hover_y = max(10, min(hover_y, self.device.browser.viewport_height - 10))

        hover_duration = random.uniform(0.3, 1.5)
        time.sleep(hover_duration)

        return self._make_event(
            "hover",
            (hover_x, hover_y),
            scroll_y,
            duration=int(hover_duration * 1000),
        )

    def _generate_element_tap(self, pos: Tuple[int, int], scroll_y: int) -> Dict:
        buttons = [
            (0.15, 0.25, 0.5, 0.08),
            (0.5, 0.65, 0.5, 0.08),
            (0.3, 0.7, 0.85, 0.1),
            (0.2, 0.8, 0.92, 0.05),
        ]
        btn = random.choice(buttons)
        btn_x = int(self.device.browser.viewport_width * random.uniform(btn[0], btn[1]))
        btn_y = int(self.device.browser.viewport_height * random.uniform(btn[2], btn[3]))

        move_to_btn = self._generate_touch_movement(pos, scroll_y)
        time.sleep(random.uniform(0.1, 0.3))

        return self._make_event(
            "tap",
            (btn_x, btn_y),
            scroll_y,
            button=0,
            movement_events=len(move_to_btn),
        )

    def _ease_in_out_quad(self, t: float) -> float:
        if t < 0.5:
            return 2 * t * t
        return 1 - ((-2 * t + 2) ** 2) / 2

    def _ease_out_cubic(self, t: float) -> float:
        return 1 - (1 - t) ** 3

    def _send_behavior_events(self, events: List[Dict], page_url: str, network: NetworkClient):
        try:
            batch_size = 5
            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]
                payload = {
                    "events": batch,
                    "url": page_url,
                    "screen": f"{self.device.hardware.screen_width}x{self.device.hardware.screen_height}",
                    "viewport": f"{self.device.browser.viewport_width}x{self.device.browser.viewport_height}",
                    "fp": self.device.device_fingerprint,
                    "t": int(time.time() * 1000),
                }
                try:
                    network.get(
                        "https://tracking.roiify.com/behavior",
                        params={"data": str(payload)[:500]},
                        is_browser=True,
                        timeout=1,
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def simulate_ad_view_interaction(self, view_duration: float) -> List[Dict]:
        events = []
        if self.page_start_time is None:
            self.page_start_time = int(time.time() * 1000)

        time.sleep(random.uniform(0.5, 2.0))
        start_pos = (
            self.device.hardware.screen_width // 2,
            self.device.hardware.screen_height // 2,
        )
        events.append(self._make_event("ad_start", start_pos, 0))

        num_touches = random.randint(0, 3)
        for _ in range(num_touches):
            touch_x = random.randint(100, self.device.hardware.screen_width - 100)
            touch_y = random.randint(100, self.device.hardware.screen_height - 200)
            time.sleep(random.uniform(2.0, min(15.0, view_duration / 2)))
            events.append(self._make_event("touch", (touch_x, touch_y), 0))

        time.sleep(max(1.0, view_duration - num_touches * 3 - 2))
        events.append(self._make_event("ad_complete", start_pos, 0))

        return events
