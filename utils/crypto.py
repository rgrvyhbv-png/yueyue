import hashlib
import hmac
import time
import uuid
import random
import string
from typing import Dict, Any
from urllib.parse import urlencode


def generate_nonce(length: int = 32) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_request_id() -> str:
    return str(uuid.uuid4())


def generate_click_id() -> str:
    ts = int(time.time() * 1000)
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return f"clk_{ts}_{random_part}"


def generate_impression_id() -> str:
    ts = int(time.time() * 1000)
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return f"imp_{ts}_{random_part}"


def sign_request(params: Dict[str, Any], secret_key: str, method: str = "HMAC-SHA256") -> str:
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if v is not None and str(v) != ""])
    sign_str += f"&key={secret_key}"

    if method == "HMAC-SHA256":
        signature = hmac.new(
            secret_key.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    elif method == "MD5":
        signature = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
    elif method == "SHA1":
        signature = hashlib.sha1(sign_str.encode("utf-8")).hexdigest()
    else:
        signature = hmac.new(
            secret_key.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    return signature


def build_signed_params(params: Dict[str, Any], secret_key: str) -> Dict[str, Any]:
    params = params.copy()
    params["nonce"] = generate_nonce()
    params["ts"] = int(time.time() * 1000)
    params["sign"] = sign_request(params, secret_key)
    return params


def verify_signature(params: Dict[str, Any], secret_key: str, sign: str) -> bool:
    params = params.copy()
    params.pop("sign", None)
    expected_sign = sign_request(params, secret_key)
    return hmac.compare_digest(expected_sign, sign)


def build_query_string(params: Dict[str, Any]) -> str:
    return urlencode({k: v for k, v in params.items() if v is not None})


def hash_device_id(device_id: str, salt: str = "roiify_device_salt") -> str:
    return hashlib.sha256(f"{device_id}{salt}".encode("utf-8")).hexdigest()


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
