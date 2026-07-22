import os
import requests
from dataclasses import dataclass
from typing import Optional, Dict, List


PROXY001_API_URL = "https://proxy001.com/api/proxy/getIPlist"


def fetch_proxy_from_api(api_key: str, num: int = 1, regions: str = "GLOBAL", protocol: str = "http") -> Optional[List[Dict]]:
    try:
        params = {
            "num": num,
            "regions": regions,
            "protocol": protocol,
            "return_type": "json",
            "lb": 1,
            "sb": "",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        }
        
        url = f"{PROXY001_API_URL}?api_key={api_key}"
        for k, v in params.items():
            url += f"&{k}={v}"
        
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
        else:
            print(f"API请求失败: {resp.status_code}")
            print(f"响应内容: {resp.text[:200]}")
    except Exception as e:
        print(f"API请求异常: {str(e)}")
    
    return None


@dataclass
class ProxyConfig:
    enabled: bool = False
    host: str = ""
    port: int = 7878
    username: str = ""
    password: str = ""
    proxy_type: str = "http"
    provider: str = "proxy001"
    country: str = ""
    api_key: str = ""

    def get_proxy_url(self) -> Optional[str]:
        if not self.enabled:
            return None
        if not self.host or not self.port:
            return None

        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        elif self.username:
            auth = f"{self.username}@"
        else:
            auth = ""
        return f"http://{auth}{self.host}:{self.port}"

    def get_proxies_dict(self) -> Optional[Dict[str, str]]:
        url = self.get_proxy_url()
        if not url:
            return None
        return {
            "http": url,
            "https": url,
        }

    def fetch_and_update_from_api(self) -> bool:
        if not self.api_key:
            return False
        
        proxy_data = fetch_proxy_from_api(
            api_key=self.api_key,
            num=1,
            regions=self.country if self.country else "GLOBAL",
            protocol=self.proxy_type,
        )
        
        if proxy_data and len(proxy_data) > 0:
            proxy_info = proxy_data[0]
            if "ip" in proxy_info and "port" in proxy_info:
                self.host = proxy_info["ip"]
                self.port = int(proxy_info["port"])
                if "username" in proxy_info:
                    self.username = proxy_info["username"]
                if "password" in proxy_info:
                    self.password = proxy_info["password"]
                if "country" in proxy_info:
                    self.country = proxy_info["country"]
                self.enabled = True
                return True
        
        return False


def load_proxy_config_from_env() -> ProxyConfig:
    api_key = os.environ.get("PROXY_API_KEY", "")
    country = os.environ.get("PROXY_COUNTRY", "")
    proxy_type = os.environ.get("PROXY_TYPE", "http")
    
    config = ProxyConfig(
        enabled=False,
        api_key=api_key,
        country=country,
        proxy_type=proxy_type,
    )
    
    if api_key:
        config.fetch_and_update_from_api()
    
    return config


proxy_config = load_proxy_config_from_env()