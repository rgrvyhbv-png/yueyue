import os
from dataclasses import dataclass
from typing import Optional, Dict


IPROYAL_CONFIG = {
    "residential": {
        "host": "geo.iproyal.com",
        "http_port": 12321,
        "socks5_port": 32325,
    },
    "datacenter": {
        "host": "geo.iproyal.com",
        "http_port": 12323,
        "socks5_port": 12324,
    },
}


@dataclass
class ProxyConfig:
    enabled: bool = False
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    proxy_type: str = "http"
    provider: str = ""

    def get_proxy_url(self, new_session: bool = False) -> Optional[str]:
        if not self.enabled:
            return None
        if not self.host or not self.port:
            return None
        
        username = self.username
        if new_session and self.provider == "iproyal":
            import random
            session_suffix = f"-session-{random.randint(1000, 9999)}"
            username = self.username + session_suffix
        
        if username and self.password:
            auth = f"{username}:{self.password}@"
        elif username:
            auth = f"{username}@"
        else:
            auth = ""
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"

    def get_proxies_dict(self, new_session: bool = False) -> Optional[Dict[str, str]]:
        url = self.get_proxy_url(new_session=new_session)
        if not url:
            return None
        return {
            "http": url,
            "https": url,
        }

    def setup_iproyal(
        self,
        username: str,
        password: str,
        proxy_type: str = "http",
        proxy_plan: str = "residential",
    ):
        config = IPROYAL_CONFIG.get(proxy_plan.lower(), IPROYAL_CONFIG["residential"])
        self.enabled = True
        self.host = config["host"]
        self.port = config["http_port"] if proxy_type.lower() == "http" else config["socks5_port"]
        self.username = username
        self.password = password
        self.proxy_type = proxy_type.lower()
        self.provider = "iproyal"


def load_proxy_config_from_env() -> ProxyConfig:
    host = os.environ.get("PROXY_HOST", "")
    port = int(os.environ.get("PROXY_PORT", "0"))
    username = os.environ.get("PROXY_USERNAME", "")
    password = os.environ.get("PROXY_PASSWORD", "")
    proxy_type = os.environ.get("PROXY_TYPE", "http")
    provider = os.environ.get("PROXY_PROVIDER", "")

    if provider.lower() == "iproyal" and username and password:
        plan = os.environ.get("IPROYAL_PLAN", "residential")
        config = IPROYAL_CONFIG.get(plan.lower(), IPROYAL_CONFIG["residential"])
        host = config["host"]
        port = config["http_port"] if proxy_type.lower() == "http" else config["socks5_port"]

    enabled = bool(host and port)
    return ProxyConfig(
        enabled=enabled,
        host=host,
        port=port,
        username=username,
        password=password,
        proxy_type=proxy_type,
        provider=provider,
    )


proxy_config = load_proxy_config_from_env()
