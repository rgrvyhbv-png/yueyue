import requests
import json
import random
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

class AdsgramSDK:
    def __init__(self, block_id: str, debug: bool = False):
        self.block_id = block_id
        self.debug = debug
        self.api_origin = "https://sad.adsgram.ai"
        self.sdk_url = "https://sad.adsgram.ai/js/sad.min.js"
        self._ad_controller_initialized = False
        self._current_ad = None
        self._session_id = self._generate_session_id()

    def _generate_session_id(self) -> str:
        import uuid
        return str(uuid.uuid4())

    def get_sdk_script(self) -> str:
        return f'<script src="{self.sdk_url}"></script>'

    def get_init_script(self) -> str:
        return f"""
const AdsgramController = window.Adsgram.init({{
    blockId: "{self.block_id}",
    debug: {str(self.debug).lower()}
}});
"""

    def get_show_script(self) -> str:
        return """
AdsgramController.show()
    .then((result) => {
        console.log('Ad watched:', result);
        window.parent.postMessage({
            type: 'ADSGRAM_REWARD',
            data: result
        }, '*');
    })
    .catch((result) => {
        console.log('Ad error/skipped:', result);
        window.parent.postMessage({
            type: 'ADSGRAM_ERROR',
            data: result
        }, '*');
    });
"""

    def build_ad_request_params(self, device_info: Dict = None) -> Dict[str, Any]:
        params = {
            "blockId": self.block_id,
            "sessionId": self._session_id,
            "timestamp": int(time.time() * 1000),
            "debug": self.debug,
        }
        
        if device_info:
            params.update({
                "ua": device_info.get("user_agent", ""),
                "locale": device_info.get("locale", "en"),
                "timezone": device_info.get("timezone", "UTC"),
            })
        
        return params

    def request_ad(self, device_info: Dict = None) -> Optional[Dict[str, Any]]:
        params = self.build_ad_request_params(device_info)
        
        try:
            response = requests.get(
                f"{self.api_origin}/ad/request",
                params=params,
                headers={
                    "User-Agent": device_info.get("user_agent", "Mozilla/5.0") if device_info else "Mozilla/5.0",
                    "Accept-Language": device_info.get("locale", "en") if device_info else "en",
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
        except Exception as e:
            print(f"Adsgram request error: {e}")
            return None

    def send_impression(self, ad_id: str, view_duration: float = 0) -> bool:
        try:
            response = requests.post(
                f"{self.api_origin}/ad/impression",
                json={
                    "blockId": self.block_id,
                    "adId": ad_id,
                    "sessionId": self._session_id,
                    "viewDuration": view_duration,
                    "timestamp": int(time.time() * 1000),
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Adsgram impression error: {e}")
            return False

    def send_click(self, ad_id: str, click_url: str = "") -> bool:
        try:
            response = requests.post(
                f"{self.api_origin}/ad/click",
                json={
                    "blockId": self.block_id,
                    "adId": ad_id,
                    "sessionId": self._session_id,
                    "clickUrl": click_url,
                    "timestamp": int(time.time() * 1000),
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Adsgram click error: {e}")
            return False

    def simulate_ad_playback(self) -> Dict[str, Any]:
        outcomes = [
            {"done": True, "description": "User watched ad till the end", "state": "destroy", "error": False},
            {"done": True, "description": "User closed interstitial", "state": "destroy", "error": False},
            {"done": False, "description": "User skipped ad", "state": "destroy", "error": False},
            {"done": False, "description": "No banner available", "state": "load", "error": True},
            {"done": False, "description": "Network error", "state": "load", "error": True},
        ]
        
        weights = [0.6, 0.2, 0.15, 0.03, 0.02]
        result = random.choices(outcomes, weights=weights, k=1)[0]
        result["timestamp"] = datetime.now().isoformat()
        
        return result