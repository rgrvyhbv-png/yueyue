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

PROXY001_CONFIG = {
    "residential": {
        "host": "us.proxy001.com",
        "http_port": 7878,
        "socks5_port": 7879,
    },
    "static_residential": {
        "host": "us.proxy001.com",
        "http_port": 7878,
        "socks5_port": 7879,
    },
    "datacenter": {
        "host": "us.proxy001.com",
        "http_port": 7878,
        "socks5_port": 7879,
    },
}

PROXY001_COUNTRY_HOSTS = {
    "US": "us.proxy001.com",
    "GB": "gb.proxy001.com",
    "DE": "de.proxy001.com",
    "FR": "fr.proxy001.com",
    "CA": "ca.proxy001.com",
    "AU": "au.proxy001.com",
    "JP": "jp.proxy001.com",
    "SG": "sg.proxy001.com",
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
    country: str = ""
    session_id: str = ""

    def get_proxy_url(self, new_session: bool = False, country: str = "") -> Optional[str]:
        if not self.enabled:
            return None
        if not self.host or not self.port:
            return None

        import random
        username = self.username
        target_country = country or self.country

        if self.provider == "iproyal":
            parts = []
            if target_country:
                parts.append(f"-country-{target_country.upper()}")
            if new_session:
                session = self.session_id or f"session-{random.randint(1000, 9999)}"
                parts.append(f"-{session}")
            if parts:
                username = self.username + "".join(parts)

        elif self.provider == "proxy001":
            if target_country and target_country.upper() in PROXY001_COUNTRY_HOSTS:
                self.host = PROXY001_COUNTRY_HOSTS[target_country.upper()]
            username = self.username

        if username and self.password:
            auth = f"{username}:{self.password}@"
        elif username:
            auth = f"{username}@"
        else:
            auth = ""
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"

    def get_proxies_dict(self, new_session: bool = False, country: str = "") -> Optional[Dict[str, str]]:
        url = self.get_proxy_url(new_session=new_session, country=country)
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
        country: str = "",
    ):
        config = IPROYAL_CONFIG.get(proxy_plan.lower(), IPROYAL_CONFIG["residential"])
        self.enabled = True
        self.host = config["host"]
        self.port = config["http_port"] if proxy_type.lower() == "http" else config["socks5_port"]
        self.username = username
        self.password = password
        self.proxy_type = proxy_type.lower()
        self.provider = "iproyal"
        self.country = country

    def setup_proxy001(
        self,
        username: str,
        password: str,
        proxy_type: str = "http",
        proxy_plan: str = "residential",
        country: str = "",
    ):
        config = PROXY001_CONFIG.get(proxy_plan.lower(), PROXY001_CONFIG["residential"])
        self.enabled = True
        self.host = config["host"]
        self.port = config["http_port"] if proxy_type.lower() == "http" else config["socks5_port"]
        self.username = username
        self.password = password
        self.proxy_type = proxy_type.lower()
        self.provider = "proxy001"
        self.country = country


def load_proxy_config_from_env() -> ProxyConfig:
    host = os.environ.get("PROXY_HOST", "")
    port = int(os.environ.get("PROXY_PORT", "0"))
    username = os.environ.get("PROXY_USERNAME", "")
    password = os.environ.get("PROXY_PASSWORD", "")
    proxy_type = os.environ.get("PROXY_TYPE", "http")
    provider = os.environ.get("PROXY_PROVIDER", "")
    country = os.environ.get("PROXY_COUNTRY", "")

    if provider.lower() == "iproyal" and username and password:
        plan = os.environ.get("IPROYAL_PLAN", "residential")
        config = IPROYAL_CONFIG.get(plan.lower(), IPROYAL_CONFIG["residential"])
        host = config["host"]
        port = config["http_port"] if proxy_type.lower() == "http" else config["socks5_port"]

    elif provider.lower() == "proxy001" and username and password:
        plan = os.environ.get("PROXY001_PLAN", "residential")
        config = PROXY001_CONFIG.get(plan.lower(), PROXY001_CONFIG["residential"])
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
        country=country,
    )


proxy_config = load_proxy_config_from_env()
