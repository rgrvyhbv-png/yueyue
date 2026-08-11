import random
import uuid
import time
import hashlib
import string
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device.models import (
    DeviceInfo, HardwareInfo, NetworkInfo,
    BrowserFingerprint, SystemInfo, UserProfile
)
from config import config


import threading

class DeviceFingerprintGenerator:
    USED_MODELS = set()
    _used_models_lock = threading.Lock()
    _dynamic_model_counter = 0  # 动态生成机型的计数器
    ANDROID_DEVICE_PROFILES = [
        {
            "brand": "Samsung",
            "manufacturer": "samsung",
            "devices": [
                {"model": "SM-S918B", "device": "e3q", "product": "e3qxxx",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 505), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("14", "15")},
                {"model": "SM-S928B", "device": "e4q", "product": "e4qxxx",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 505), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [8, 12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("14", "15")},
                {"model": "SM-S911B", "device": "c3q", "product": "c3qxxx",
                 "board": "sm8550", "hardware": "qcom", "year": 2023,
                 "screen": (1440, 3120, 480), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3100000,
                 "battery": 4000, "os_range": ("13", "15")},
                {"model": "SM-S916B", "device": "c5q", "product": "c5qxxx",
                 "board": "sm8550", "hardware": "qcom", "year": 2023,
                 "screen": (1440, 3200, 505), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3100000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "SM-S908B", "device": "b0q", "product": "b0qxxx",
                 "board": "sm8450", "hardware": "qcom", "year": 2022,
                 "screen": (1440, 3088, 500), "gpu": ("Qualcomm", "Adreno (TM) 730", "OpenGL ES 3.2 V@0614.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3000000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "SM-G998B", "device": "o3s", "product": "o3sxxx",
                 "board": "sm8350", "hardware": "qcom", "year": 2021,
                 "screen": (1440, 3200, 515), "gpu": ("Qualcomm", "Adreno (TM) 660", "OpenGL ES 3.2 V@0502.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 2900000,
                 "battery": 5000, "os_range": ("11", "14")},
                {"model": "SM-G973F", "device": "beyond1", "product": "beyond1ltexx",
                 "board": "msm8998", "hardware": "qcom", "year": 2019,
                 "screen": (1080, 2280, 420), "gpu": ("Qualcomm", "Adreno (TM) 640", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": 8, "storage_gb": [128, 512], "cpu_cores": 8, "freq": 2800000,
                 "battery": 3400, "os_range": ("9", "12")},
                {"model": "SM-G970F", "device": "beyond0", "product": "beyond0ltexx",
                 "board": "msm8998", "hardware": "qcom", "year": 2019,
                 "screen": (1080, 2280, 420), "gpu": ("Qualcomm", "Adreno (TM) 640", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": 6, "storage_gb": [128], "cpu_cores": 8, "freq": 2700000,
                 "battery": 3100, "os_range": ("9", "12")},
                {"model": "SM-G980F", "device": "x1s", "product": "x1sltexx",
                 "board": "exynos990", "hardware": "exynos990", "year": 2020,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G77 MP11", "OpenGL ES 3.2 v1.r24p0-01eac0."),
                 "ram_gb": 8, "storage_gb": [128], "cpu_cores": 8, "freq": 2730000,
                 "battery": 4000, "os_range": ("10", "13")},
                {"model": "SM-G991B", "device": "o1s", "product": "o1sxxx",
                 "board": "sm8350", "hardware": "qcom", "year": 2021,
                 "screen": (1080, 2400, 420), "gpu": ("Qualcomm", "Adreno (TM) 660", "OpenGL ES 3.2 V@0502.0"),
                 "ram_gb": 8, "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2840000,
                 "battery": 4000, "os_range": ("11", "14")},
                {"model": "SM-A536B", "device": "a53x", "product": "a53xnaxx",
                 "board": "exynos1280", "hardware": "s5e8825", "year": 2022,
                 "screen": (1080, 2400, 450), "gpu": ("ARM", "Mali-G68 MP4", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": [4, 6, 8], "storage_gb": [64, 128, 256], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "SM-A135F", "device": "a13", "product": "a13naxx",
                 "board": "exynos850", "hardware": "s5e3830", "year": 2022,
                 "screen": (1080, 2408, 400), "gpu": ("ARM", "Mali-G52 MC2", "OpenGL ES 3.2 v1.r28p0-01eac0."),
                 "ram_gb": [3, 4, 6], "storage_gb": [32, 64, 128], "cpu_cores": 8, "freq": 2000000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "SM-M325FV", "device": "m32", "product": "m32nsxx",
                 "board": "mt6769t", "hardware": "mt6769t", "year": 2021,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G52 MC2", "OpenGL ES 3.2 v1.r28p0-01eac0."),
                 "ram_gb": [4, 6, 8], "storage_gb": [64, 128], "cpu_cores": 8, "freq": 2000000,
                 "battery": 6000, "os_range": ("11", "13")},
                {"model": "SM-S931B", "device": "p3q", "product": "p3qxxx",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3120, 495), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 4000, "os_range": ("15", "15")},
                {"model": "SM-S936B", "device": "p5q", "product": "p5qxxx",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3120, 495), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 5000, "os_range": ("15", "15")},
                {"model": "SM-A556B", "device": "a55x", "product": "a55xnx",
                 "board": "exynos1480", "hardware": "s5e8845", "year": 2024,
                 "screen": (1080, 2340, 432), "gpu": ("ARM", "Mali-G68 MP5", "OpenGL ES 3.2 v1.r36p0-01eac0."),
                 "ram_gb": [6, 8, 12], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("14", "15")},
                {"model": "SM-A356E", "device": "a35x", "product": "a35xnn",
                 "board": "exynos1380", "hardware": "s5e8835", "year": 2024,
                 "screen": (1080, 2340, 432), "gpu": ("ARM", "Mali-G68 MP5", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": [6, 8], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2200000,
                 "battery": 5000, "os_range": ("14", "15")},
            ]
        },
        {
            "brand": "Xiaomi",
            "manufacturer": "Xiaomi",
            "devices": [
                {"model": "MI 9", "device": "cepheus", "product": "cepheus",
                 "board": "msmnile", "hardware": "qcom", "year": 2019,
                 "screen": (1080, 2340, 440), "gpu": ("Qualcomm", "Adreno (TM) 640", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [6, 8], "storage_gb": [64, 128, 256], "cpu_cores": 8, "freq": 2840000,
                 "battery": 3300, "os_range": ("9", "12")},
                {"model": "Redmi Note 8", "device": "ginkgo", "product": "ginkgo",
                 "board": "trinket", "hardware": "qcom", "year": 2019,
                 "screen": (1080, 2340, 400), "gpu": ("Qualcomm", "Adreno (TM) 610", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [3, 4, 6], "storage_gb": [32, 64, 128], "cpu_cores": 8, "freq": 2000000,
                 "battery": 4000, "os_range": ("9", "12")},
                {"model": "Mi 11", "device": "venus", "product": "venus",
                 "board": "lahaina", "hardware": "qcom", "year": 2021,
                 "screen": (1080, 2400, 480), "gpu": ("Qualcomm", "Adreno (TM) 660", "OpenGL ES 3.2 V@0502.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2840000,
                 "battery": 4600, "os_range": ("11", "14")},
                {"model": "Redmi Note 11", "device": "spes", "product": "spes",
                 "board": "bengal", "hardware": "qcom", "year": 2022,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 610", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [4, 6], "storage_gb": [64, 128], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("11", "14")},
                {"model": "Redmi Note 10 Pro", "device": "sweet", "product": "sweet",
                 "board": "sm6150", "hardware": "qcom", "year": 2021,
                 "screen": (1080, 2400, 395), "gpu": ("Qualcomm", "Adreno (TM) 618", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [6, 8], "storage_gb": [64, 128], "cpu_cores": 8, "freq": 2300000,
                 "battery": 5020, "os_range": ("11", "13")},
                {"model": "POCO X3 Pro", "device": "vayu", "product": "vayu",
                 "board": "sm8150", "hardware": "qcom", "year": 2021,
                 "screen": (1080, 2400, 395), "gpu": ("Qualcomm", "Adreno (TM) 640", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [6, 8], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2960000,
                 "battery": 5160, "os_range": ("11", "13")},
                {"model": "Mi 12 Pro", "device": "zeus", "product": "zeus",
                 "board": "taro", "hardware": "qcom", "year": 2022,
                 "screen": (1440, 3200, 525), "gpu": ("Qualcomm", "Adreno (TM) 730", "OpenGL ES 3.2 V@0614.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 3000000,
                 "battery": 4600, "os_range": ("12", "14")},
                {"model": "Redmi Note 12", "device": "tapas", "product": "tapas",
                 "board": "taro", "hardware": "qcom", "year": 2023,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 619", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [4, 6, 8], "storage_gb": [64, 128, 256], "cpu_cores": 8, "freq": 2200000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "Mi 13 Pro", "device": "fuxi", "product": "fuxi",
                 "board": "taro", "hardware": "qcom", "year": 2023,
                 "screen": (1440, 3200, 525), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12, 16], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3200000,
                 "battery": 4820, "os_range": ("13", "15")},
                {"model": "Mi 14 Pro", "device": "houji", "product": "houji",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 560), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 4880, "os_range": ("14", "15")},
                {"model": "Redmi K70 Pro", "device": "manet", "product": "manet",
                 "board": "sm8550", "hardware": "qcom", "year": 2023,
                 "screen": (1440, 3200, 480), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12, 16], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "Mi 15 Pro", "device": "haotian", "product": "haotian",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3200, 560), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 6100, "os_range": ("15", "15")},
                {"model": "Redmi K80 Pro", "device": "socrates", "product": "socrates",
                 "board": "sm8750", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 480), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 6000, "os_range": ("15", "15")},
                {"model": "Redmi Note 13 Pro", "device": "garnet", "product": "garnet",
                 "board": "mt6080", "hardware": "mt6080", "year": 2024,
                 "screen": (1080, 2400, 446), "gpu": ("ARM", "Mali-G610 MC6", "OpenGL ES 3.2 v1.r38p0-01eac0."),
                 "ram_gb": [6, 8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 2600000,
                 "battery": 5100, "os_range": ("14", "15")},
                {"model": "POCO F6 Pro", "device": "vermeer", "product": "vermeer",
                 "board": "sm8550", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 480), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("14", "15")},
            ]
        },
        {
            "brand": "Google",
            "manufacturer": "Google",
            "devices": [
                {"model": "Pixel 4a", "device": "sunfish", "product": "sunfish",
                 "board": "msmnile", "hardware": "qcom", "year": 2020,
                 "screen": (1080, 2340, 440), "gpu": ("Qualcomm", "Adreno (TM) 618", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": 6, "storage_gb": [128], "cpu_cores": 8, "freq": 2200000,
                 "battery": 3140, "os_range": ("10", "13")},
                {"model": "Pixel 5", "device": "redfin", "product": "redfin",
                 "board": "sm7250", "hardware": "qcom", "year": 2020,
                 "screen": (1080, 2340, 440), "gpu": ("Qualcomm", "Adreno (TM) 620", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": 8, "storage_gb": [128], "cpu_cores": 8, "freq": 2400000,
                 "battery": 4080, "os_range": ("11", "14")},
                {"model": "Pixel 6", "device": "oriole", "product": "oriole",
                 "board": "gs101", "hardware": "tensor", "year": 2021,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 8, "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2800000,
                 "battery": 4614, "os_range": ("12", "14")},
                {"model": "Pixel 6a", "device": "bluejay", "product": "bluejay",
                 "board": "gs101", "hardware": "tensor", "year": 2022,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 6, "storage_gb": [128], "cpu_cores": 8, "freq": 2800000,
                 "battery": 4410, "os_range": ("12", "14")},
                {"model": "Pixel 7", "device": "panther", "product": "panther",
                 "board": "gs201", "hardware": "tensor", "year": 2022,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 8, "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2800000,
                 "battery": 4355, "os_range": ("13", "15")},
                {"model": "Pixel 7 Pro", "device": "cheetah", "product": "cheetah",
                 "board": "gs201", "hardware": "tensor", "year": 2022,
                 "screen": (1440, 3120, 480), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 12, "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 2800000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "Pixel 8", "device": "lynx", "product": "lynx",
                 "board": "gs301", "hardware": "tensor", "year": 2023,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 8, "storage_gb": [128, 256], "cpu_cores": 8, "freq": 3000000,
                 "battery": 4575, "os_range": ("14", "15")},
                {"model": "Pixel 8 Pro", "device": "husky", "product": "husky",
                 "board": "gs301", "hardware": "tensor", "year": 2023,
                 "screen": (1440, 3120, 480), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 12, "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3000000,
                 "battery": 5050, "os_range": ("14", "15")},
                {"model": "Pixel 9 Pro", "device": "comet", "product": "comet",
                 "board": "gs401", "hardware": "tensor", "year": 2024,
                 "screen": (1440, 3120, 480), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 12, "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3200000,
                 "battery": 4700, "os_range": ("15", "15")},
                {"model": "Pixel 9a", "device": "tegu", "product": "tegu",
                 "board": "gs401", "hardware": "tensor", "year": 2025,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 8, "storage_gb": [128, 256], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5100, "os_range": ("15", "15")},
                {"model": "Pixel 10 Pro", "device": "blazer", "product": "blazer",
                 "board": "gs501", "hardware": "tensor", "year": 2025,
                 "screen": (1440, 3120, 480), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r36p0-01eac0."),
                 "ram_gb": [12, 16], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3400000,
                 "battery": 5200, "os_range": ("16", "16")},
            ]
        },
        {
            "brand": "OnePlus",
            "manufacturer": "OnePlus",
            "devices": [
                {"model": "HD1903", "device": "guacamoleb", "product": "OnePlus7",
                 "board": "msmnile", "hardware": "qcom", "year": 2019,
                 "screen": (1080, 2340, 400), "gpu": ("Qualcomm", "Adreno (TM) 640", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [6, 8], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2840000,
                 "battery": 3700, "os_range": ("9", "12")},
                {"model": "LE2123", "device": "OnePlus9Pro", "product": "OnePlus9Pro_EEA",
                 "board": "lahaina", "hardware": "qcom", "year": 2021,
                 "screen": (1440, 3216, 525), "gpu": ("Qualcomm", "Adreno (TM) 660", "OpenGL ES 3.2 V@0502.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2840000,
                 "battery": 4500, "os_range": ("11", "14")},
                {"model": "NE2213", "device": "OnePlus10Pro", "product": "OnePlus10Pro_EEA",
                 "board": "taro", "hardware": "qcom", "year": 2022,
                 "screen": (1440, 3216, 525), "gpu": ("Qualcomm", "Adreno (TM) 730", "OpenGL ES 3.2 V@0614.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 3000000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "CPH2581", "device": "OnePlus12Pro", "product": "OnePlus12Pro_EEA",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 560), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5400, "os_range": ("14", "15")},
                {"model": "CPH2487", "device": "OnePlus11", "product": "OnePlus11_EEA",
                 "board": "sm8550", "hardware": "qcom", "year": 2023,
                 "screen": (1440, 3216, 525), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12, 16], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "CPH2651", "device": "OnePlus13", "product": "OnePlus13_EEA",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3168, 560), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16, 24], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 6000, "os_range": ("15", "15")},
            ]
        },
        {
            "brand": "HUAWEI",
            "manufacturer": "HUAWEI",
            "devices": [
                {"model": "ELE-L29", "device": "HWERE", "product": "ELE-L29",
                 "board": "kirin980", "hardware": "kirin980", "year": 2019,
                 "screen": (1080, 2340, 440), "gpu": ("ARM", "Mali-G76 MP10", "OpenGL ES 3.2 v1.r23p0-01eac0."),
                 "ram_gb": [6, 8], "storage_gb": [128], "cpu_cores": 8, "freq": 2600000,
                 "battery": 3650, "os_range": ("9", "10")},
                {"model": "ELS-NX9", "device": "HWELS", "product": "ELS-NX9",
                 "board": "kirin990", "hardware": "kirin990", "year": 2020,
                 "screen": (1200, 2640, 480), "gpu": ("ARM", "Mali-G76 MP16", "OpenGL ES 3.2 v1.r23p0-01eac0."),
                 "ram_gb": 8, "storage_gb": [256], "cpu_cores": 8, "freq": 2860000,
                 "battery": 4200, "os_range": ("10", "11")},
                {"model": "JAD-LX9", "device": "HWPALA", "product": "JAD-LX9",
                 "board": "kirin9000", "hardware": "kirin9000", "year": 2021,
                 "screen": (1228, 2700, 450), "gpu": ("ARM", "Mali-G78 MP24", "OpenGL ES 3.2 v1.r32p1-01eac0."),
                 "ram_gb": 8, "storage_gb": [128, 256], "cpu_cores": 8, "freq": 3130000,
                 "battery": 4360, "os_range": ("11", "12")},
            ]
        },
        {
            "brand": "OPPO",
            "manufacturer": "OPPO",
            "devices": [
                {"model": "CPH1931", "device": "CPH1931", "product": "CPH1931",
                 "board": "mt6771", "hardware": "mt6771", "year": 2019,
                 "screen": (720, 1600, 320), "gpu": ("ARM", "Mali-G72 MP3", "OpenGL ES 3.2 v1.r23p0-01eac0."),
                 "ram_gb": [3, 4], "storage_gb": [64], "cpu_cores": 8, "freq": 2000000,
                 "battery": 4230, "os_range": ("8.1", "10")},
                {"model": "CPH2173", "device": "OP4F2FL1", "product": "CPH2173EEA",
                 "board": "sm6150", "hardware": "qcom", "year": 2020,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 618", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [6, 8], "storage_gb": [128], "cpu_cores": 8, "freq": 2300000,
                 "battery": 4300, "os_range": ("10", "12")},
                {"model": "CPH2305", "device": "OP5323L1", "product": "CPH2305EEA",
                 "board": "sm4350", "hardware": "qcom", "year": 2021,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 619", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [4, 6], "storage_gb": [64, 128], "cpu_cores": 8, "freq": 2200000,
                 "battery": 5000, "os_range": ("11", "13")},
            ]
        },
        {
            "brand": "vivo",
            "manufacturer": "vivo",
            "devices": [
                {"model": "V1901A", "device": "PD1901", "product": "PD1901",
                 "board": "mt6765", "hardware": "mt6765", "year": 2019,
                 "screen": (720, 1544, 270), "gpu": ("ARM", "Mali-G72 MP3", "OpenGL ES 3.2 v1.r23p0-01eac0."),
                 "ram_gb": [3, 4], "storage_gb": [32, 64], "cpu_cores": 8, "freq": 2300000,
                 "battery": 5000, "os_range": ("9", "11")},
                {"model": "V2027", "device": "PD2034", "product": "PD2034_EX",
                 "board": "mt6853", "hardware": "mt6853", "year": 2021,
                 "screen": (1080, 2408, 400), "gpu": ("ARM", "Mali-G57 MC3", "OpenGL ES 3.2 v1.r26p0-01eac0."),
                 "ram_gb": [4, 6, 8], "storage_gb": [64, 128], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("11", "13")},
                {"model": "V2203", "device": "PD2170", "product": "PD2170_EX",
                 "board": "sm4350", "hardware": "qcom", "year": 2022,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 619", "OpenGL ES 3.2 V@415.0"),
                 "ram_gb": [6, 8], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "V2309A", "device": "PD2317", "product": "PD2317",
                 "board": "sm8550", "hardware": "qcom", "year": 2023,
                 "screen": (1440, 3200, 480), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "V2403A", "device": "PD2418", "product": "PD2418",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3200, 560), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5500, "os_range": ("14", "15")},
            ]
        },
        {
            "brand": "HONOR",
            "manufacturer": "HONOR",
            "devices": [
                {"model": "PGT-AN10", "device": "PGTAN", "product": "PGT-AN10",
                 "board": "qcom", "hardware": "qcom", "year": 2022,
                 "screen": (1080, 2400, 432), "gpu": ("Qualcomm", "Adreno (TM) 642L", "OpenGL ES 3.2 V@0432.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 2600000,
                 "battery": 4800, "os_range": ("12", "14")},
                {"model": "CMA-AN00", "device": "CMA", "product": "CMA-AN00",
                 "board": "sm8475", "hardware": "qcom", "year": 2023,
                 "screen": (1080, 2700, 432), "gpu": ("Qualcomm", "Adreno (TM) 730", "OpenGL ES 3.2 V@0614.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "PGT-AN20", "device": "PGTAN20", "product": "PGT-AN20",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1080, 2700, 432), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5600, "os_range": ("14", "15")},
                {"model": "BVL-AN16", "device": "BVL", "product": "BVL-AN16",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1080, 2704, 437), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16, 24], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 5850, "os_range": ("15", "15")},
            ]
        },
        {
            "brand": "Realme",
            "manufacturer": "Realme",
            "devices": [
                {"model": "RMX3700", "device": "RE58C2L1", "product": "RMX3700",
                 "board": "mt6983", "hardware": "mt6983", "year": 2022,
                 "screen": (1440, 3216, 526), "gpu": ("ARM", "Mali-G710 MC10", "OpenGL ES 3.2 v1.r34p0-01eac0."),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3000000,
                 "battery": 5000, "os_range": ("12", "14")},
                {"model": "RMX3800", "device": "RE58B9L1", "product": "RMX3800",
                 "board": "sm8475", "hardware": "qcom", "year": 2023,
                 "screen": (1080, 2772, 450), "gpu": ("Qualcomm", "Adreno (TM) 730", "OpenGL ES 3.2 V@0614.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5240, "os_range": ("14", "15")},
                {"model": "RMX3900", "device": "RE58A4L1", "product": "RMX3900",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1080, 2780, 450), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3300000,
                 "battery": 5500, "os_range": ("15", "15")},
            ]
        },
        {
            "brand": "Motorola",
            "manufacturer": "Motorola",
            "devices": [
                {"model": "XT2301-3", "device": "penang5g", "product": "penang5g_cn",
                 "board": "sm6450", "hardware": "qcom", "year": 2023,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 710", "OpenGL ES 3.2 V@0515.0"),
                 "ram_gb": [6, 8], "storage_gb": [128, 256], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("13", "14")},
                {"model": "XT2351-2", "device": "pennga5g", "product": "pennga5g_cn",
                 "board": "sm7475", "hardware": "qcom", "year": 2024,
                 "screen": (1080, 2400, 400), "gpu": ("Qualcomm", "Adreno (TM) 710", "OpenGL ES 3.2 V@0515.0"),
                 "ram_gb": [6, 8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 2600000,
                 "battery": 5000, "os_range": ("14", "15")},
                {"model": "XT2401-1", "device": "rtwo", "product": "rtwo_cn",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1440, 3120, 480), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [8, 12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3300000,
                 "battery": 4400, "os_range": ("14", "15")},
                {"model": "XT2501-1", "device": "sunstone", "product": "sunstone_cn",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3120, 480), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 4600, "os_range": ("15", "15")},
            ]
        },
        {
            "brand": "Sony",
            "manufacturer": "Sony",
            "devices": [
                {"model": "XQ-AS72", "device": "bengal", "product": "XQ-AS72",
                 "board": "sm8550", "hardware": "qcom", "year": 2023,
                 "screen": (1080, 2520, 450), "gpu": ("Qualcomm", "Adreno (TM) 740", "OpenGL ES 3.2 V@0700.0"),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("13", "15")},
                {"model": "XQ-AS82", "device": "lisbon", "product": "XQ-AS82",
                 "board": "sm8650", "hardware": "qcom", "year": 2024,
                 "screen": (1080, 2520, 450), "gpu": ("Qualcomm", "Adreno (TM) 750", "OpenGL ES 3.2 V@0705.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5000, "os_range": ("14", "15")},
            ]
        },
        {
            "brand": "Samsung",
            "manufacturer": "samsung",
            "devices": [
                {"model": "SM-S948B", "device": "q3q", "product": "q3qxxx",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3120, 495), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16, 24], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 4000, "os_range": ("15", "15")},
                {"model": "SM-S946B", "device": "q4q", "product": "q4qxxx",
                 "board": "sm8750", "hardware": "qcom", "year": 2025,
                 "screen": (1440, 3120, 495), "gpu": ("Qualcomm", "Adreno (TM) 830", "OpenGL ES 3.2 V@0800.0"),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 5000, "os_range": ("15", "15")},
                {"model": "SM-A566B", "device": "a56x", "product": "a56xnx",
                 "board": "exynos1580", "hardware": "s5e8855", "year": 2025,
                 "screen": (1080, 2340, 432), "gpu": ("ARM", "Mali-G720 MC5", "OpenGL ES 3.2 v1.r40p0-01eac0."),
                 "ram_gb": [6, 8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 2400000,
                 "battery": 5000, "os_range": ("15", "15")},
            ]
        },
        {
            "brand": "Google",
            "manufacturer": "Google",
            "devices": [
                {"model": "Pixel 10", "device": "panther", "product": "panther",
                 "board": "gs501", "hardware": "tensor", "year": 2025,
                 "screen": (1080, 2400, 420), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r36p0-01eac0."),
                 "ram_gb": [8, 12], "storage_gb": [128, 256, 512], "cpu_cores": 8, "freq": 3200000,
                 "battery": 5050, "os_range": ("16", "16")},
                {"model": "Pixel 10 Pro XL", "device": "caiman", "product": "caiman",
                 "board": "gs501", "hardware": "tensor", "year": 2025,
                 "screen": (1440, 3120, 480), "gpu": ("ARM", "Mali-G78 MP20", "OpenGL ES 3.2 v1.r36p0-01eac0."),
                 "ram_gb": [12, 16], "storage_gb": [256, 512, 1024], "cpu_cores": 8, "freq": 3400000,
                 "battery": 5200, "os_range": ("16", "16")},
            ]
        },
    ]

    IOS_DEVICE_PROFILES = [
        {"model_id": "iPhone11,8", "model_name": "iPhone XR", "year": 2018,
         "screen": (828, 1792, 326), "ram_gb": 3, "storage_gb": [64, 128, 256],
         "battery": 2942, "os_range": ("12.0", "17.0")},
        {"model_id": "iPhone11,14", "model_name": "iPhone XS", "year": 2018,
         "screen": (1125, 2436, 458), "ram_gb": 4, "storage_gb": [64, 256, 512],
         "battery": 2658, "os_range": ("12.0", "17.0")},
        {"model_id": "iPhone11,16", "model_name": "iPhone XS Max", "year": 2018,
         "screen": (1242, 2688, 458), "ram_gb": 4, "storage_gb": [64, 256, 512],
         "battery": 3174, "os_range": ("12.0", "17.0")},
        {"model_id": "iPhone12,1", "model_name": "iPhone 11", "year": 2019,
         "screen": (828, 1792, 326), "ram_gb": 4, "storage_gb": [64, 128, 256],
         "battery": 3110, "os_range": ("13.0", "17.0")},
        {"model_id": "iPhone12,3", "model_name": "iPhone 11 Pro", "year": 2019,
         "screen": (1125, 2436, 458), "ram_gb": 4, "storage_gb": [64, 256, 512],
         "battery": 3046, "os_range": ("13.0", "17.0")},
        {"model_id": "iPhone12,5", "model_name": "iPhone 11 Pro Max", "year": 2019,
         "screen": (1242, 2688, 458), "ram_gb": 4, "storage_gb": [64, 256, 512],
         "battery": 3969, "os_range": ("13.0", "17.0")},
        {"model_id": "iPhone13,2", "model_name": "iPhone 12", "year": 2020,
         "screen": (1170, 2532, 460), "ram_gb": 4, "storage_gb": [64, 128, 256],
         "battery": 2815, "os_range": ("14.1", "17.0")},
        {"model_id": "iPhone13,3", "model_name": "iPhone 12 Pro", "year": 2020,
         "screen": (1170, 2532, 460), "ram_gb": 6, "storage_gb": [128, 256, 512],
         "battery": 2815, "os_range": ("14.1", "17.0")},
        {"model_id": "iPhone13,4", "model_name": "iPhone 12 Pro Max", "year": 2020,
         "screen": (1284, 2778, 460), "ram_gb": 6, "storage_gb": [128, 256, 512],
         "battery": 3687, "os_range": ("14.1", "17.0")},
        {"model_id": "iPhone14,2", "model_name": "iPhone 13 Pro", "year": 2021,
         "screen": (1170, 2532, 460), "ram_gb": 6, "storage_gb": [128, 256, 512, 1024],
         "battery": 3095, "os_range": ("15.0", "17.0")},
        {"model_id": "iPhone14,3", "model_name": "iPhone 13 Pro Max", "year": 2021,
         "screen": (1284, 2778, 460), "ram_gb": 6, "storage_gb": [128, 256, 512, 1024],
         "battery": 4352, "os_range": ("15.0", "17.0")},
        {"model_id": "iPhone14,5", "model_name": "iPhone 13", "year": 2021,
         "screen": (1170, 2532, 460), "ram_gb": 4, "storage_gb": [128, 256, 512],
         "battery": 3227, "os_range": ("15.0", "17.0")},
        {"model_id": "iPhone14,6", "model_name": "iPhone 13 mini", "year": 2021,
         "screen": (1080, 2340, 476), "ram_gb": 4, "storage_gb": [128, 256, 512],
         "battery": 2406, "os_range": ("15.0", "17.0")},
        {"model_id": "iPhone15,2", "model_name": "iPhone 14 Pro", "year": 2022,
         "screen": (1179, 2556, 460), "ram_gb": 6, "storage_gb": [128, 256, 512, 1024],
         "battery": 3200, "os_range": ("16.0", "17.0")},
        {"model_id": "iPhone15,3", "model_name": "iPhone 14 Pro Max", "year": 2022,
         "screen": (1290, 2796, 460), "ram_gb": 6, "storage_gb": [128, 256, 512, 1024],
         "battery": 4323, "os_range": ("16.0", "17.0")},
        {"model_id": "iPhone15,4", "model_name": "iPhone 14", "year": 2022,
         "screen": (1170, 2532, 460), "ram_gb": 6, "storage_gb": [128, 256, 512],
         "battery": 3200, "os_range": ("16.0", "17.0")},
        {"model_id": "iPhone15,5", "model_name": "iPhone 14 Plus", "year": 2022,
         "screen": (1284, 2778, 460), "ram_gb": 6, "storage_gb": [128, 256, 512],
         "battery": 3200, "os_range": ("16.0", "17.0")},
        {"model_id": "iPhone16,1", "model_name": "iPhone 15", "year": 2023,
         "screen": (1179, 2556, 460), "ram_gb": 6, "storage_gb": [128, 256, 512],
         "battery": 3349, "os_range": ("17.0", "17.0")},
        {"model_id": "iPhone16,2", "model_name": "iPhone 15 Plus", "year": 2023,
         "screen": (1290, 2796, 460), "ram_gb": 6, "storage_gb": [128, 256, 512],
         "battery": 3349, "os_range": ("17.0", "17.0")},
        {"model_id": "iPhone17,1", "model_name": "iPhone 15 Pro", "year": 2023,
         "screen": (1179, 2556, 460), "ram_gb": 8, "storage_gb": [128, 256, 512, 1024],
         "battery": 3561, "os_range": ("17.0", "17.0")},
        {"model_id": "iPhone17,2", "model_name": "iPhone 15 Pro Max", "year": 2023,
         "screen": (1290, 2796, 460), "ram_gb": 8, "storage_gb": [128, 256, 512, 1024],
         "battery": 4441, "os_range": ("17.0", "17.0")},
        {"model_id": "iPhone17,3", "model_name": "iPhone 16", "year": 2024,
         "screen": (1242, 2710, 460), "ram_gb": 8, "storage_gb": [128, 256, 512],
         "battery": 3561, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone17,4", "model_name": "iPhone 16 Plus", "year": 2024,
         "screen": (1320, 2874, 460), "ram_gb": 8, "storage_gb": [128, 256, 512],
         "battery": 4674, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone18,1", "model_name": "iPhone 16 Pro", "year": 2024,
         "screen": (1242, 2710, 460), "ram_gb": 8, "storage_gb": [128, 256, 512, 1024],
         "battery": 3582, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone18,2", "model_name": "iPhone 16 Pro Max", "year": 2024,
         "screen": (1320, 2874, 460), "ram_gb": 8, "storage_gb": [128, 256, 512, 1024],
         "battery": 4685, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone19,1", "model_name": "iPhone 17", "year": 2025,
         "screen": (1242, 2710, 460), "ram_gb": 8, "storage_gb": [128, 256, 512],
         "battery": 3561, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone19,2", "model_name": "iPhone 17 Plus", "year": 2025,
         "screen": (1320, 2874, 460), "ram_gb": 8, "storage_gb": [128, 256, 512],
         "battery": 4674, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone20,1", "model_name": "iPhone 17 Pro", "year": 2025,
         "screen": (1242, 2710, 460), "ram_gb": 12, "storage_gb": [256, 512, 1024],
         "battery": 3582, "os_range": ("18.0", "18.0")},
        {"model_id": "iPhone20,2", "model_name": "iPhone 17 Pro Max", "year": 2025,
         "screen": (1320, 2874, 460), "ram_gb": 12, "storage_gb": [256, 512, 1024],
         "battery": 4685, "os_range": ("18.0", "18.0")},
    ]

    ANDROID_VERSIONS = [
        ("8.0", 26, "26", "2017-08-01", "OPR1"),
        ("8.1", 27, "27", "2017-12-05", "OPM1"),
        ("9", 28, "28", "2018-08-06", "PPR1"),
        ("10", 29, "29", "2019-09-03", "QP1A"),
        ("11", 30, "30", "2020-09-08", "RP1A"),
        ("12", 31, "31", "2021-10-04", "SP1A"),
        ("12L", 32, "32", "2022-03-07", "SL2D"),
        ("13", 33, "33", "2022-08-15", "TP1A"),
        ("14", 34, "34", "2023-10-04", "UP1A"),
    ]

    CHROME_VERSIONS = [
        "93.0.4577.63",
        "95.0.4638.74",
        "96.0.4664.45",
        "97.0.4692.99",
        "98.0.4758.102",
        "99.0.4844.51",
        "100.0.4896.127",
        "101.0.4951.64",
        "102.0.5005.61",
        "103.0.5060.134",
        "104.0.5112.97",
        "105.0.5195.125",
        "106.0.5249.119",
        "107.0.5304.87",
        "108.0.5359.128",
        "109.0.5414.119",
        "110.0.5481.177",
        "111.0.5563.64",
        "112.0.5615.136",
        "113.0.5672.63",
        "114.0.5735.110",
        "115.0.5790.102",
        "116.0.5845.163",
        "117.0.5938.134",
        "118.0.5993.88",
        "119.0.6045.105",
        "120.0.6099.230",
        "121.0.6167.139",
        "122.0.6261.94",
        "123.0.6312.105",
        "124.0.6367.60",
        "125.0.6422.110",
        "126.0.6478.182",
        "127.0.6533.100",
        "128.0.6613.137",
    ]

    LOCALE_CONFIGS = [
        # ── 东亚 ──
        {"locale": "zh-CN", "lang": "zh", "country": "CN", "tz": "Asia/Shanghai", "offset": -480,
         "carriers": [("46000", "中国移动", "China Mobile"), ("46001", "中国联通", "China Unicom"),
                      ("46003", "中国电信", "China Telecom")]},
        {"locale": "zh-TW", "lang": "zh", "country": "TW", "tz": "Asia/Taipei", "offset": -480,
         "carriers": [("46692", "中华电信", "Chunghwa Telecom"), ("46697", "台湾大哥大", "Taiwan Mobile"),
                      ("46689", "远传电信", "FarEasTone")]},
        {"locale": "zh-HK", "lang": "zh", "country": "HK", "tz": "Asia/Hong_Kong", "offset": -480,
         "carriers": [("45400", "CSL", "CSL Mobile"), ("45403", "3", "Hutchison 3G"),
                      ("45406", "SmarTone", "SmarTone"), ("45412", "CMHK", "China Mobile HK")]},
        {"locale": "ja-JP", "lang": "ja", "country": "JP", "tz": "Asia/Tokyo", "offset": -540,
         "carriers": [("44010", "docomo", "NTT DOCOMO"), ("44020", "SoftBank", "SoftBank Mobile"),
                      ("44050", "au", "KDDI au")]},
        {"locale": "ko-KR", "lang": "ko", "country": "KR", "tz": "Asia/Seoul", "offset": -540,
         "carriers": [("45008", "KT", "KT Corporation"), ("45006", "LG U+", "LG Uplus"),
                      ("45002", "SKT", "SK Telecom")]},
        # ── 东南亚 ──
        {"locale": "th-TH", "lang": "th", "country": "TH", "tz": "Asia/Bangkok", "offset": -420,
         "carriers": [("52000", "AIS", "AIS"), ("52015", "TrueMove", "TrueMove H"),
                      ("52005", "DTAC", "dtac"), ("52099", "NT", "National Telecom")]},
        {"locale": "vi-VN", "lang": "vi", "country": "VN", "tz": "Asia/Ho_Chi_Minh", "offset": -420,
         "carriers": [("45201", "MobiFone", "MobiFone"), ("45202", "Vinaphone", "Vinaphone"),
                      ("45204", "Viettel", "Viettel"), ("45207", "Vietnamobile", "Vietnamobile")]},
        {"locale": "id-ID", "lang": "id", "country": "ID", "tz": "Asia/Jakarta", "offset": -420,
         "carriers": [("51001", "Telkomsel", "Telkomsel"), ("51010", "XL", "XL Axiata"),
                      ("51009", "Indosat", "Indosat Ooredoo"), ("51008", "3", "Hutchison 3")]},
        {"locale": "en-SG", "lang": "en", "country": "SG", "tz": "Asia/Singapore", "offset": -480,
         "carriers": [("52501", "Singtel", "Singtel"), ("52502", "StarHub", "StarHub"),
                      ("52503", "M1", "M1")]},
        {"locale": "en-MY", "lang": "ms", "country": "MY", "tz": "Asia/Kuala_Lumpur", "offset": -480,
         "carriers": [("50212", "Maxis", "Maxis"), ("50216", "Digi", "Digi"),
                      ("50219", "Celcom", "Celcom"), ("50213", "U Mobile", "U Mobile")]},
        {"locale": "en-PH", "lang": "en", "country": "PH", "tz": "Asia/Manila", "offset": -480,
         "carriers": [("51502", "Globe", "Globe Telecom"), ("51503", "Smart", "Smart Communications"),
                      ("51505", "DITO", "DITO Telecommunity")]},
        # ── 南亚 ──
        {"locale": "en-IN", "lang": "en", "country": "IN", "tz": "Asia/Kolkata", "offset": -330,
         "carriers": [("40445", "Airtel", "Bharti Airtel"), ("40440", "Jio", "Reliance Jio"),
                      ("40420", "Vi", "Vodafone Idea"), ("40484", "BSNL", "BSNL")]},
        {"locale": "en-PK", "lang": "ur", "country": "PK", "tz": "Asia/Karachi", "offset": -300,
         "carriers": [("41001", "Jazz", "Mobilink"), ("41003", "Zong", "Zong"),
                      ("41004", "Telenor", "Telenor PK"), ("41006", "Ufone", "Ufone")]},
        {"locale": "en-BD", "lang": "bn", "country": "BD", "tz": "Asia/Dhaka", "offset": -360,
         "carriers": [("47001", "Grameenphone", "Grameenphone"), ("47002", "Robi", "Robi"),
                      ("47003", "Banglalink", "Banglalink")]},
        # ── 北美 ──
        {"locale": "en-US", "lang": "en", "country": "US", "tz": "America/New_York", "offset": 300,
         "carriers": [("310260", "T-Mobile", "T-Mobile US"), ("310410", "AT&T", "AT&T Mobility"),
                      ("310120", "Verizon", "Verizon Wireless")]},
        {"locale": "en-CA", "lang": "en", "country": "CA", "tz": "America/Toronto", "offset": 300,
         "carriers": [("302220", "Rogers", "Rogers"), ("302610", "Bell", "Bell Mobility"),
                      ("302720", "Telus", "TELUS"), ("302490", "Freedom", "Freedom Mobile")]},
        {"locale": "es-MX", "lang": "es", "country": "MX", "tz": "America/Mexico_City", "offset": 360,
         "carriers": [("334020", "Telcel", "Telcel"), ("334030", "Movistar", "Movistar MX"),
                      ("334050", "AT&T", "AT&T MX")]},
        # ── 南美 ──
        {"locale": "pt-BR", "lang": "pt", "country": "BR", "tz": "America/Sao_Paulo", "offset": 180,
         "carriers": [("72405", "Claro", "Claro Brasil"), ("72406", "Vivo", "Vivo"),
                      ("72410", "TIM", "TIM Brasil"), ("72416", "Oi", "Oi")]},
        {"locale": "es-AR", "lang": "es", "country": "AR", "tz": "America/Argentina/Buenos_Aires", "offset": 180,
         "carriers": [("72207", "Movistar", "Movistar AR"), ("72234", "Personal", "Telecom Personal"),
                      ("722310", "Claro", "Claro AR")]},
        {"locale": "es-CO", "lang": "es", "country": "CO", "tz": "America/Bogota", "offset": 300,
         "carriers": [("732101", "Claro", "Claro CO"), ("732103", "Movistar", "Movistar CO"),
                      ("732130", "Tigo", "Tigo CO")]},
        {"locale": "es-CL", "lang": "es", "country": "CL", "tz": "America/Santiago", "offset": 240,
         "carriers": [("73001", "Entel", "Entel Chile"), ("73002", "Movistar", "Movistar CL"),
                      ("73003", "Claro", "Claro CL"), ("73010", "WOM", "WOM")]},
        {"locale": "es-PE", "lang": "es", "country": "PE", "tz": "America/Lima", "offset": 300,
         "carriers": [("71606", "Movistar", "Movistar PE"), ("71610", "Claro", "Claro PE"),
                      ("71601", "Entel", "Entel PE"), ("71617", "Bitel", "Bitel")]},
        # ── 欧洲 ──
        {"locale": "en-GB", "lang": "en", "country": "GB", "tz": "Europe/London", "offset": 0,
         "carriers": [("23410", "O2", "O2 UK"), ("23420", "Three", "Three UK"),
                      ("23430", "EE", "EE Limited"), ("23415", "Vodafone", "Vodafone UK")]},
        {"locale": "de-DE", "lang": "de", "country": "DE", "tz": "Europe/Berlin", "offset": -60,
         "carriers": [("26201", "Telekom", "Deutsche Telekom"), ("26202", "Vodafone", "Vodafone DE"),
                      ("26203", "O2", "O2 Germany")]},
        {"locale": "fr-FR", "lang": "fr", "country": "FR", "tz": "Europe/Paris", "offset": -60,
         "carriers": [("20801", "Orange", "Orange France"), ("20810", "SFR", "SFR"),
                      ("20815", "Free", "Free Mobile"), ("20820", "Bouygues", "Bouygues Telecom")]},
        {"locale": "es-ES", "lang": "es", "country": "ES", "tz": "Europe/Madrid", "offset": -60,
         "carriers": [("21401", "Vodafone", "Vodafone ES"), ("21403", "Orange", "Orange ES"),
                      ("21407", "Movistar", "Movistar ES"), ("21404", "Yoigo", "Yoigo")]},
        {"locale": "it-IT", "lang": "it", "country": "IT", "tz": "Europe/Rome", "offset": -60,
         "carriers": [("22201", "TIM", "TIM IT"), ("22210", "Vodafone", "Vodafone IT"),
                      ("22288", "WindTre", "WindTre"), ("22250", "Iliad", "Iliad IT")]},
        {"locale": "nl-NL", "lang": "nl", "country": "NL", "tz": "Europe/Amsterdam", "offset": -60,
         "carriers": [("20404", "Vodafone", "Vodafone NL"), ("20408", "KPN", "KPN"),
                      ("20416", "T-Mobile", "T-Mobile NL")]},
        {"locale": "ru-RU", "lang": "ru", "country": "RU", "tz": "Europe/Moscow", "offset": -180,
         "carriers": [("25001", "MTS", "MTS"), ("25002", "MegaFon", "MegaFon"),
                      ("25099", "Beeline", "Beeline"), ("25020", "Tele2", "Tele2 RU")]},
        {"locale": "pl-PL", "lang": "pl", "country": "PL", "tz": "Europe/Warsaw", "offset": -60,
         "carriers": [("26001", "Plus", "Plus"), ("26002", "T-Mobile", "T-Mobile PL"),
                      ("26003", "Orange", "Orange PL"), ("26006", "Play", "Play")]},
        {"locale": "tr-TR", "lang": "tr", "country": "TR", "tz": "Europe/Istanbul", "offset": -180,
         "carriers": [("28601", "Turkcell", "Turkcell"), ("28602", "Vodafone", "Vodafone TR"),
                      ("28603", "Türk Telekom", "Türk Telekom")]},
        {"locale": "sv-SE", "lang": "sv", "country": "SE", "tz": "Europe/Stockholm", "offset": -60,
         "carriers": [("24001", "Telia", "Telia SE"), ("24002", "Tele2", "Tele2 SE"),
                      ("24008", "Telenor", "Telenor SE"), ("24006", "3", "Tre SE")]},
        {"locale": "pt-PT", "lang": "pt", "country": "PT", "tz": "Europe/Lisbon", "offset": 0,
         "carriers": [("26801", "Vodafone", "Vodafone PT"), ("26803", "NOS", "NOS"),
                      ("26806", "MEO", "MEO")]},
        {"locale": "el-GR", "lang": "el", "country": "GR", "tz": "Europe/Athens", "offset": -120,
         "carriers": [("20201", "Cosmote", "Cosmote"), ("20205", "Vodafone", "Vodafone GR"),
                      ("20210", "Nova", "Nova")]},
        {"locale": "cs-CZ", "lang": "cs", "country": "CZ", "tz": "Europe/Prague", "offset": -60,
         "carriers": [("23001", "T-Mobile", "T-Mobile CZ"), ("23002", "O2", "O2 CZ"),
                      ("23003", "Vodafone", "Vodafone CZ")]},
        {"locale": "ro-RO", "lang": "ro", "country": "RO", "tz": "Europe/Bucharest", "offset": -120,
         "carriers": [("22601", "Vodafone", "Vodafone RO"), ("22603", "Telekom", "Telekom RO"),
                      ("22610", "Orange", "Orange RO"), ("22605", "DIGI", "DIGI Mobil")]},
        {"locale": "hu-HU", "lang": "hu", "country": "HU", "tz": "Europe/Budapest", "offset": -60,
         "carriers": [("21601", "Telenor", "Yettel"), ("21630", "Telekom", "Magyar Telekom"),
                      ("21670", "Vodafone", "Vodafone HU")]},
        {"locale": "uk-UA", "lang": "uk", "country": "UA", "tz": "Europe/Kyiv", "offset": -120,
         "carriers": [("25501", "Vodafone", "Vodafone UA"), ("25503", "Kyivstar", "Kyivstar"),
                      ("25506", "Lifecell", "lifecell")]},
        # ── 大洋洲 ──
        {"locale": "en-AU", "lang": "en", "country": "AU", "tz": "Australia/Sydney", "offset": -600,
         "carriers": [("50501", "Telstra", "Telstra"), ("50502", "Optus", "Optus"),
                      ("50503", "Vodafone", "Vodafone AU")]},
        {"locale": "en-NZ", "lang": "en", "country": "NZ", "tz": "Pacific/Auckland", "offset": -720,
         "carriers": [("53001", "Vodafone", "One NZ"), ("53005", "Spark", "Spark"),
                      ("53024", "2degrees", "2degrees")]},
        # ── 中东 ──
        {"locale": "ar-SA", "lang": "ar", "country": "SA", "tz": "Asia/Riyadh", "offset": -180,
         "carriers": [("42001", "STC", "STC"), ("42003", "Mobily", "Mobily"),
                      ("42004", "Zain", "Zain SA")]},
        {"locale": "ar-AE", "lang": "ar", "country": "AE", "tz": "Asia/Dubai", "offset": -240,
         "carriers": [("42402", "Etisalat", "Etisalat"), ("42403", "du", "du")]},
        {"locale": "en-IL", "lang": "he", "country": "IL", "tz": "Asia/Jerusalem", "offset": -120,
         "carriers": [("42501", "Pelephone", "Pelephone"), ("42502", "Cellcom", "Cellcom"),
                      ("42505", "Partner", "Partner")]},
        {"locale": "ar-EG", "lang": "ar", "country": "EG", "tz": "Africa/Cairo", "offset": -120,
         "carriers": [("60201", "Orange", "Orange EG"), ("60202", "Vodafone", "Vodafone EG"),
                      ("60203", "Etisalat", "Etisalat EG")]},
        # ── 非洲 ──
        {"locale": "en-ZA", "lang": "en", "country": "ZA", "tz": "Africa/Johannesburg", "offset": -120,
         "carriers": [("65501", "Vodacom", "Vodacom"), ("65510", "MTN", "MTN SA"),
                      ("65507", "Cell C", "Cell C"), ("65502", "Telkom", "Telkom SA")]},
        {"locale": "en-NG", "lang": "en", "country": "NG", "tz": "Africa/Lagos", "offset": -60,
         "carriers": [("62120", "Airtel", "Airtel NG"), ("62130", "MTN", "MTN NG"),
                      ("62150", "Glo", "Globacom"), ("62160", "9mobile", "9mobile")]},
        {"locale": "en-KE", "lang": "sw", "country": "KE", "tz": "Africa/Nairobi", "offset": -180,
         "carriers": [("63902", "Safaricom", "Safaricom"), ("63903", "Airtel", "Airtel KE"),
                      ("63907", "Telkom", "Telkom KE")]},
    ]

    WEBGL_UNMASKED_RENDERERS = {
        "Adreno (TM) 640": ["ANGLE (Qualcomm, Adreno (TM) 640, OpenGL ES 3.2)"],
        "Adreno (TM) 660": ["ANGLE (Qualcomm, Adreno (TM) 660, OpenGL ES 3.2)"],
        "Adreno (TM) 730": ["ANGLE (Qualcomm, Adreno (TM) 730, OpenGL ES 3.2)"],
        "Adreno (TM) 610": ["ANGLE (Qualcomm, Adreno (TM) 610, OpenGL ES 3.2)"],
        "Adreno (TM) 618": ["ANGLE (Qualcomm, Adreno (TM) 618, OpenGL ES 3.2)"],
        "Adreno (TM) 619": ["ANGLE (Qualcomm, Adreno (TM) 619, OpenGL ES 3.2)"],
        "Adreno (TM) 620": ["ANGLE (Qualcomm, Adreno (TM) 620, OpenGL ES 3.2)"],
        "Mali-G77 MP11": ["ANGLE (ARM, Mali-G77 MP11, OpenGL ES 3.2)"],
        "Mali-G78 MP20": ["ANGLE (ARM, Mali-G78 MP20, OpenGL ES 3.2)"],
        "Mali-G78 MP24": ["ANGLE (ARM, Mali-G78 MP24, OpenGL ES 3.2)"],
        "Mali-G76 MP10": ["ANGLE (ARM, Mali-G76 MP10, OpenGL ES 3.2)"],
        "Mali-G76 MP16": ["ANGLE (ARM, Mali-G76 MP16, OpenGL ES 3.2)"],
        "Mali-G72 MP3": ["ANGLE (ARM, Mali-G72 MP3, OpenGL ES 3.2)"],
        "Mali-G68 MP4": ["ANGLE (ARM, Mali-G68 MP4, OpenGL ES 3.2)"],
        "Mali-G57 MC3": ["ANGLE (ARM, Mali-G57 MC3, OpenGL ES 3.2)"],
        "Mali-G52 MC2": ["ANGLE (ARM, Mali-G52 MC2, OpenGL ES 3.2)"],
        "Apple A15 GPU": ["Apple M1"],
        "Apple A16 GPU": ["Apple M2"],
        "Apple A17 Pro GPU": ["Apple M3"],
    }

    def __init__(self, platform: str = "android", device_age_days: Optional[int] = None,
                 seed: Optional[int] = None, country: Optional[str] = None):
        if seed is not None:
            random.seed(seed)
        self.platform = platform.lower()
        self.device_age_days = device_age_days or random.randint(60, 540)
        self.forced_country = country.upper() if country else None
        self._cached_fingerprint: Optional[DeviceInfo] = None

    # 动态时区映射：国家代码 → 时区（用于未在 LOCALE_CONFIGS 中列出的国家）
    _DYNAMIC_TIMEZONE_MAP = {
        "US": "America/New_York", "CA": "America/Toronto", "MX": "America/Mexico_City",
        "BR": "America/Sao_Paulo", "AR": "America/Argentina/Buenos_Aires",
        "CO": "America/Bogota", "CL": "America/Santiago", "PE": "America/Lima",
        "GB": "Europe/London", "DE": "Europe/Berlin", "FR": "Europe/Paris",
        "ES": "Europe/Madrid", "IT": "Europe/Rome", "NL": "Europe/Amsterdam",
        "RU": "Europe/Moscow", "PL": "Europe/Warsaw", "TR": "Europe/Istanbul",
        "SE": "Europe/Stockholm", "PT": "Europe/Lisbon", "GR": "Europe/Athens",
        "CZ": "Europe/Prague", "RO": "Europe/Bucharest", "HU": "Europe/Budapest",
        "UA": "Europe/Kyiv", "AT": "Europe/Vienna", "BE": "Europe/Brussels",
        "CH": "Europe/Zurich", "DK": "Europe/Copenhagen", "FI": "Europe/Helsinki",
        "NO": "Europe/Oslo", "IE": "Europe/Dublin", "BG": "Europe/Sofia",
        "HR": "Europe/Zagreb", "SK": "Europe/Bratislava", "SI": "Europe/Ljubljana",
        "LT": "Europe/Vilnius", "LV": "Europe/Riga", "EE": "Europe/Tallinn",
        "CN": "Asia/Shanghai", "TW": "Asia/Taipei", "HK": "Asia/Hong_Kong",
        "JP": "Asia/Tokyo", "KR": "Asia/Seoul", "TH": "Asia/Bangkok",
        "VN": "Asia/Ho_Chi_Minh", "ID": "Asia/Jakarta", "SG": "Asia/Singapore",
        "MY": "Asia/Kuala_Lumpur", "PH": "Asia/Manila", "IN": "Asia/Kolkata",
        "PK": "Asia/Karachi", "BD": "Asia/Dhaka", "LK": "Asia/Colombo",
        "MM": "Asia/Yangon", "KH": "Asia/Phnom_Penh", "LA": "Asia/Vientiane",
        "MN": "Asia/Ulaanbaatar", "NP": "Asia/Kathmandu",
        "AU": "Australia/Sydney", "NZ": "Pacific/Auckland",
        "SA": "Asia/Riyadh", "AE": "Asia/Dubai", "IL": "Asia/Jerusalem",
        "EG": "Africa/Cairo", "QA": "Asia/Qatar", "KW": "Asia/Kuwait",
        "BH": "Asia/Bahrain", "OM": "Asia/Muscat", "JO": "Asia/Amman",
        "LB": "Asia/Beirut", "IQ": "Asia/Baghdad", "IR": "Asia/Tehran",
        "ZA": "Africa/Johannesburg", "NG": "Africa/Lagos", "KE": "Africa/Nairobi",
        "MA": "Africa/Casablanca", "DZ": "Africa/Algiers", "TN": "Africa/Tunis",
        "GH": "Africa/Accra", "ET": "Africa/Addis_Ababa", "TZ": "Africa/Dar_es_Salaam",
        "UG": "Africa/Kampala", "RW": "Africa/Kigali", "SN": "Africa/Dakar",
        "CI": "Africa/Abidjan", "CM": "Africa/Douala", "AO": "Africa/Luanda",
    }

    # 动态语言映射：国家代码 → 语言代码
    _DYNAMIC_LANG_MAP = {
        "US": "en", "CA": "en", "GB": "en", "AU": "en", "NZ": "en",
        "IE": "en", "SG": "en", "PH": "en", "IN": "en", "PK": "en",
        "BD": "en", "ZA": "en", "NG": "en", "KE": "en", "GH": "en",
        "TZ": "en", "UG": "en", "CM": "en", "JM": "en", "TT": "en",
        "CN": "zh", "TW": "zh", "HK": "zh", "SG": "zh",
        "JP": "ja", "KR": "ko", "TH": "th", "VN": "vi",
        "ID": "id", "MY": "ms", "MM": "my", "KH": "km", "LA": "lo",
        "DE": "de", "AT": "de", "CH": "de",
        "FR": "fr", "BE": "fr", "CI": "fr", "SN": "fr",
        "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es",
        "PE": "es", "VE": "es", "EC": "es", "GT": "es", "DO": "es",
        "IT": "it", "NL": "nl", "RU": "ru", "PL": "pl", "TR": "tr",
        "SE": "sv", "PT": "pt", "BR": "pt", "GR": "el", "CZ": "cs",
        "RO": "ro", "HU": "hu", "UA": "uk", "BG": "bg", "HR": "hr",
        "SK": "sk", "SI": "sl", "LT": "lt", "LV": "lv", "ET": "et",
        "DK": "da", "FI": "fi", "NO": "no", "HE": "he", "IL": "he",
        "SA": "ar", "AE": "ar", "EG": "ar", "QA": "ar", "KW": "ar",
        "BH": "ar", "OM": "ar", "JO": "ar", "LB": "ar", "IQ": "ar",
        "MA": "ar", "DZ": "ar", "TN": "ar", "IR": "fa",
        "MN": "mn", "NP": "ne", "LK": "si",
    }

    @classmethod
    def _generate_dynamic_android_device(cls) -> None:
        """当所有机型用完时，动态生成新的安卓机型并添加到列表"""
        cls._dynamic_model_counter += 1
        
        # 选择品牌
        brands_config = [
            ("Samsung", "samsung", "SM-DYN"),
            ("Xiaomi", "Xiaomi", "MI-DYN"),
            ("Google", "Google", "Pixel-DYN"),
            ("OnePlus", "OnePlus", "OP-DYN"),
            ("HONOR", "HONOR", "HONOR-DYN"),
            ("Realme", "Realme", "RMX-DYN"),
            ("Motorola", "Motorola", "XT-DYN"),
        ]
        brand_name, manufacturer, model_prefix = random.choice(brands_config)
        
        # 生成新机型名
        new_model = f"{model_prefix}{cls._dynamic_model_counter:04d}"
        new_device_codename = f"dyn_{cls._dynamic_model_counter:04d}"
        
        # 随机年份 (2023-2025)
        year = random.choice([2023, 2024, 2025])
        
        # 根据年份选择SoC
        if year == 2025:
            board = "sm8750"
            gpu_vendor = "Qualcomm"
            gpu_name = "Adreno (TM) 830"
            webgl = "OpenGL ES 3.2 V@0800.0"
            cpu_freq = 3400000
        elif year == 2024:
            board = "sm8650"
            gpu_vendor = "Qualcomm"
            gpu_name = "Adreno (TM) 750"
            webgl = "OpenGL ES 3.2 V@0705.0"
            cpu_freq = 3200000
        else:
            board = "sm8550"
            gpu_vendor = "Qualcomm"
            gpu_name = "Adreno (TM) 740"
            webgl = "OpenGL ES 3.2 V@0700.0"
            cpu_freq = 3100000
        
        # 随机屏幕配置
        screen_options = [
            (1440, 3200, 480),
            (1440, 3120, 480),
            (1440, 3088, 500),
            (1080, 2400, 400),
        ]
        screen = random.choice(screen_options)
        
        # 随机内存和存储
        ram_options = [8, 12, 16]
        storage_options = [128, 256, 512, 1024]
        
        # 构建新设备配置
        new_device = {
            "model": new_model,
            "device": new_device_codename,
            "product": f"{new_device_codename}_us",
            "board": board,
            "hardware": "qcom",
            "year": year,
            "screen": screen,
            "gpu": (gpu_vendor, gpu_name, webgl),
            "ram_gb": ram_options,
            "storage_gb": storage_options,
            "cpu_cores": 8,
            "freq": cpu_freq,
            "battery": random.choice([4000, 4500, 5000, 5500]),
            "os_range": ("13", "15") if year <= 2023 else ("14", "15"),
        }
        
        # 添加到对应品牌的设备列表
        for bp in cls.ANDROID_DEVICE_PROFILES:
            if bp["brand"] == brand_name:
                bp["devices"].append(new_device)
                return
        
        # 如果品牌不存在，创建新品牌
        cls.ANDROID_DEVICE_PROFILES.append({
            "brand": brand_name,
            "manufacturer": manufacturer,
            "devices": [new_device],
        })

    @classmethod
    def _build_locale_config(cls, country_code: str) -> dict:
        """为任意国家代码动态构建locale配置"""
        cc = country_code.upper()
        for cfg in cls.LOCALE_CONFIGS:
            if cfg["country"] == cc:
                return cfg
        lang = cls._DYNAMIC_LANG_MAP.get(cc, "en")
        tz = cls._DYNAMIC_TIMEZONE_MAP.get(cc, "UTC")
        try:
            from zoneinfo import ZoneInfo
            from datetime import datetime
            tz_obj = ZoneInfo(tz)
            now = datetime.now(tz_obj)
            tz_offset = int(now.utcoffset().total_seconds() / 60)
        except Exception:
            tz_offset = 0
        generic_carrier = f"{cc}00"
        return {
            "locale": f"{lang}-{cc}",
            "lang": lang,
            "country": cc,
            "tz": tz,
            "offset": tz_offset,
            "carriers": [(generic_carrier, f"Carrier {cc}", f"Carrier {cc}")],
        }

    GEO_TIER_WEIGHTS = {
        "US": 8.0, "CA": 3.5, "GB": 3.0, "AU": 2.5, "NZ": 1.2,
        "DE": 1.8, "FR": 1.5, "NL": 1.2, "SE": 1.0, "CH": 1.5,
        "NO": 1.0, "DK": 0.9, "FI": 0.8, "IE": 1.0, "AT": 0.9,
        "BE": 0.8, "LU": 0.5, "SG": 1.8, "JP": 1.5, "KR": 1.0,
        "HK": 1.0, "TW": 0.8, "AE": 1.2, "SA": 0.8, "IL": 1.0,
        "IT": 1.0, "ES": 0.9, "PT": 0.7, "PL": 0.5, "CZ": 0.4,
        "HU": 0.3, "RO": 0.3, "GR": 0.4, "RU": 0.6, "TR": 0.5,
        "UA": 0.3, "CN": 0.5, "IN": 0.6, "ID": 0.3, "TH": 0.3,
        "VN": 0.3, "PH": 0.3, "MY": 0.3, "MX": 0.4, "BR": 0.5,
        "AR": 0.2, "CO": 0.2, "CL": 0.2, "PE": 0.2,
        "ZA": 0.3, "NG": 0.2, "EG": 0.2, "PK": 0.2, "BD": 0.1,
    }

    def _get_locale_weight(self, cfg):
        return self.GEO_TIER_WEIGHTS.get(cfg["country"], 0.3)

    def _get_locale_config(self):
        if self.forced_country:
            for cfg in self.LOCALE_CONFIGS:
                if cfg["country"] == self.forced_country:
                    return cfg
            return self._build_locale_config(self.forced_country)
        weights = [self._get_locale_weight(cfg) for cfg in self.LOCALE_CONFIGS]
        return random.choices(self.LOCALE_CONFIGS, weights=weights, k=1)[0]

    def generate(self) -> DeviceInfo:
        now = int(time.time())

        if self.platform == "android":
            device = self._generate_android_device(now)
        elif self.platform == "ios":
            device = self._generate_ios_device(now)
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

        self._cached_fingerprint = device
        return device

    def regenerate(self) -> DeviceInfo:
        self._cached_fingerprint = None
        return self.generate()

    def _pick_android_version_for_year(self, min_year: int, max_year: int) -> tuple:
        """根据设备发布年份选择合理的OS版本"""
        candidate_versions = []
        for ver in self.ANDROID_VERSIONS:
            os_ver, api_level, sdk, patch_date, build_prefix = ver
            patch_year = int(patch_date.split("-")[0])
            if patch_year >= min_year - 1 and patch_year <= max_year + 1:
                candidate_versions.append(ver)
        if not candidate_versions:
            candidate_versions = self.ANDROID_VERSIONS[-3:]
        return random.choice(candidate_versions)

    def _generate_android_device(self, now: int) -> DeviceInfo:
        with self._used_models_lock:
            available_devices = []
            for bp in self.ANDROID_DEVICE_PROFILES:
                for dev in bp["devices"]:
                    # 使用更精细的key: 机型+存储+RAM
                    storages = dev["storage_gb"] if isinstance(dev["storage_gb"], list) else [dev["storage_gb"]]
                    rams = dev["ram_gb"] if isinstance(dev["ram_gb"], list) else [dev["ram_gb"]]
                    for storage_gb in storages:
                        for ram_gb in rams:
                            key = f"{dev['model']}|{storage_gb}GB|{ram_gb}GB"
                            if key not in self.USED_MODELS:
                                available_devices.append((bp, dev, storage_gb, ram_gb, key))
            
            if not available_devices:
                # 组合用完了，动态添加新机型
                self._generate_dynamic_android_device()
                # 重新获取可用机型
                for bp in self.ANDROID_DEVICE_PROFILES:
                    for dev in bp["devices"]:
                        storages = dev["storage_gb"] if isinstance(dev["storage_gb"], list) else [dev["storage_gb"]]
                        rams = dev["ram_gb"] if isinstance(dev["ram_gb"], list) else [dev["ram_gb"]]
                        for storage_gb in storages:
                            for ram_gb in rams:
                                key = f"{dev['model']}|{storage_gb}GB|{ram_gb}GB"
                                if key not in self.USED_MODELS:
                                    available_devices.append((bp, dev, storage_gb, ram_gb, key))
                # 如果还是没有（理论上不会），清空重新开始
                if not available_devices:
                    self.USED_MODELS.clear()
                    for bp in self.ANDROID_DEVICE_PROFILES:
                        for dev in bp["devices"]:
                            storages = dev["storage_gb"] if isinstance(dev["storage_gb"], list) else [dev["storage_gb"]]
                            rams = dev["ram_gb"] if isinstance(dev["ram_gb"], list) else [dev["ram_gb"]]
                            for storage_gb in storages:
                                for ram_gb in rams:
                                    key = f"{dev['model']}|{storage_gb}GB|{ram_gb}GB"
                                    available_devices.append((bp, dev, storage_gb, ram_gb, key))
            
            brand_profile, dev, selected_storage, selected_ram, used_key = random.choice(available_devices)
            brand = brand_profile["brand"]
            manufacturer = brand_profile["manufacturer"]
            model = dev["model"]
            self.USED_MODELS.add(used_key)
        device_codename = dev["device"]
        product = dev["product"]
        board = dev["board"]
        hw_name = dev["hardware"]
        release_year = dev["year"]
        screen_w, screen_h, dpi = dev["screen"]
        gpu_vendor, gpu_renderer, webgl_ver = dev["gpu"]

        min_os_year = release_year
        max_os_year = min(2024, release_year + 3)
        os_ver, api_level, build_sdk, security_patch, build_prefix = self._pick_android_version_for_year(
            min_os_year, max_os_year
        )

        compatible_chromes = [
            v for v in self.CHROME_VERSIONS
            if self._chrome_compatible_with_os(chrome_ver=v, os_api=api_level)
        ]
        if compatible_chromes:
            age_days = self.device_age_days
            if age_days > 365:
                idx_max = max(1, len(compatible_chromes) - 2)
                idx = random.randint(0, idx_max)
            elif age_days > 180:
                idx_max = max(1, len(compatible_chromes) - 1)
                idx = random.randint(0, idx_max)
            else:
                idx = random.randint(max(0, len(compatible_chromes) - 3), len(compatible_chromes) - 1)
            chrome_ver = compatible_chromes[min(idx, len(compatible_chromes) - 1)]
        else:
            chrome_ver = self.CHROME_VERSIONS[-2]

        ram_gb = selected_ram
        storage_gb = selected_storage

        locale_cfg = self._get_locale_config()
        locale, lang_code, country, timezone_name, tz_offset = (
            locale_cfg["locale"], locale_cfg["lang"], locale_cfg["country"],
            locale_cfg["tz"], locale_cfg["offset"]
        )
        mcc_mnc, carrier_cn, carrier_en = random.choice(locale_cfg["carriers"])

        android_id = self._generate_android_id()
        gaid = str(uuid.uuid4())
        imei = self._generate_imei()
        oaid = self._generate_oaid()
        openudid = ''.join(random.choices('0123456789abcdef', k=40))

        build_id = self._generate_build_id(build_prefix)
        build_fingerprint = self._generate_build_fingerprint(
            manufacturer, product, model, device_codename, os_ver, build_id, build_sdk
        )

        ua_template = random.choice([
            "Mozilla/5.0 (Linux; Android {os_ver}; {model} Build/{build_id}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android {os_ver}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
        ])
        user_agent = ua_template.format(
            os_ver=os_ver, model=model, build_id=build_id, chrome_ver=chrome_ver
        )

        device_age_seconds = self.device_age_days * 86400
        total_charge_cycles = int(self.device_age_days * random.uniform(0.3, 0.8))
        battery_health = max(70, min(100, int(100 - self.device_age_days * random.uniform(0.01, 0.04))))
        available_storage_gb = max(1, int(storage_gb * random.uniform(0.15, 0.6)))
        install_days_ago = random.randint(
            max(1, self.device_age_days - 30),
            self.device_age_days
        )
        last_update_days_ago = random.randint(1, min(60, self.device_age_days))
        uptime_days = random.randint(0, 14)
        boot_time = now - uptime_days * 86400 - random.randint(0, 86400)

        is_rooted = random.random() < 0.01
        has_gps = random.random() < 0.95
        has_nfc = dev["year"] >= 2020 or random.random() < 0.3
        is_vpn_active = random.random() < 0.03

        platform_nav = "Linux armv8l" if "v8a" in dev.get("abi", "arm64-v8a") else "Linux armv7l"
        if gpu_vendor == "Qualcomm" and "64" not in gpu_renderer and "73" not in gpu_renderer:
            if api_level <= 28:
                platform_nav = "Linux armv7l" if random.random() < 0.3 else "Linux armv8l"

        cookie_count = min(80, random.randint(8, 20) + int(self.device_age_days * 0.08))
        ls_count = min(60, random.randint(5, 15) + int(self.device_age_days * 0.05))
        cookie_ids = self._generate_cookie_ids(now - install_days_ago * 86400, now)

        webgl_unmasked = random.choice(
            self.WEBGL_UNMASKED_RENDERERS.get(gpu_renderer, ["ANGLE (" + gpu_vendor + ", " + gpu_renderer + ", OpenGL ES 3.2)"])
        )

        hardware = HardwareInfo(
            brand=brand,
            manufacturer=manufacturer,
            model=model,
            device=device_codename,
            product=product,
            board=board,
            hardware=hw_name,
            platform="android",
            screen_width=screen_w,
            screen_height=screen_h,
            screen_dpi=dpi,
            screen_density=round(dpi / 160.0, 2),
            physical_ram=ram_gb * 1024 * 1024 * 1024,
            total_storage=storage_gb * 1024 * 1024 * 1024,
            available_storage=available_storage_gb * 1024 * 1024 * 1024,
            cpu_abi="arm64-v8a" if ram_gb >= 4 and release_year >= 2020 else random.choice(["arm64-v8a", "armeabi-v7a"]),
            cpu_cores=dev["cpu_cores"],
            cpu_max_freq=dev["freq"],
            gpu_vendor=gpu_vendor,
            gpu_renderer=gpu_renderer,
            webgl_version=webgl_ver,
            battery_capacity=dev["battery"],
            battery_health_pct=battery_health,
            charge_cycle_count=total_charge_cycles,
            has_touchscreen=True,
            has_wifi=True,
            has_bluetooth=True,
            has_gps=has_gps,
            has_nfc=has_nfc,
        )

        network = NetworkInfo(
            ip_address=self._generate_ip_address(country),
            ip_type="ipv4",
            connection_type=random.choice(["wifi", "4g", "5g"]) if release_year >= 2020 else random.choice(["wifi", "4g"]),
            mcc=mcc_mnc[:3],
            mnc=mcc_mnc[3:],
            carrier_name=carrier_en,
            carrier_name_cn=carrier_cn,
            is_roaming=random.random() < 0.05,
            wifi_ssid=random.choice(["Home-WiFi", "MyNetwork", "TP-LINK_", None, None, None]) if random.random() < 0.4 else None,
            wifi_bssid=None,
            network_operator=mcc_mnc,
            sim_operator=mcc_mnc,
            network_country_iso=country.lower(),
        )

        system = SystemInfo(
            os_name="Android",
            os_version=os_ver,
            os_api_level=api_level,
            os_build_id=build_id,
            os_build_fingerprint=build_fingerprint,
            os_security_patch=security_patch,
            os_boot_time=boot_time,
            device_uptime_days=uptime_days,
            sdk_version=config.SDK_VERSION,
            app_package_name=config.DEFAULT_APP_PACKAGE,
            app_version=config.DEFAULT_APP_VERSION,
            app_version_code=125,
            app_install_time=now - install_days_ago * 86400 - random.randint(0, 86400),
            app_update_time=now - last_update_days_ago * 86400 - random.randint(0, 86400),
            app_first_run_time=now - install_days_ago * 86400 + random.randint(60, 3600),
            is_rooted=is_rooted,
            is_emulator=False,
            is_vpn_active=is_vpn_active,
            is_proxy_active=False,
            has_google_play_services=not is_rooted or random.random() < 0.5,
            timezone=timezone_name,
            locale=locale,
            language=lang_code,
            country=country,
            time_offset=tz_offset,
        )

        plugins = self._generate_plugins_list("chrome")
        browser_name = "Chrome"
        browser_version = user_agent.split("Chrome/")[1].split(" ")[0].split(".")[0] if "Chrome/" in user_agent else "125"
        
        browser = BrowserFingerprint(
            user_agent=user_agent,
            browser_name=browser_name,
            browser_version=browser_version,
            accept_language=f"{locale},{lang_code};q=0.9" + (",en;q=0.8" if lang_code != "en" else ""),
            platform=platform_nav,
            vendor="Google Inc.",
            color_depth=24,
            pixel_depth=24,
            screen_width=screen_w,
            screen_height=screen_h,
            viewport_width=screen_w,
            viewport_height=screen_h - random.randint(140, 300),
            device_pixel_ratio=round(dpi / 160.0, 2),
            cookies_enabled=True,
            cookie_count=cookie_count,
            local_storage_keys_count=ls_count,
            do_not_track=random.choice([None, None, None, "0", "1"]),
            canvas_fingerprint=self._generate_canvas_fingerprint(webgl_unmasked),
            webgl_vendor=gpu_vendor,
            webgl_renderer=webgl_unmasked,
            webgl_fingerprint=self._generate_webgl_fingerprint(gpu_vendor, gpu_renderer),
            audio_fingerprint=self._generate_audio_fingerprint(),
            fonts_list=self._generate_fonts_list("android"),
            plugins_list=plugins,
            timezone_offset=tz_offset,
            touch_support=(True, True, random.randint(1, 10)),
            hardware_concurrency=hardware.cpu_cores,
            device_memory=round(ram_gb, 1),
            max_touch_points=random.choice([5, 10]),
            webgl_extensions=self._generate_webgl_extensions(gpu_vendor, gpu_renderer),
            cookie_ids=cookie_ids,
        )

        installed_apps_base = {
            2019: random.randint(60, 150),
            2020: random.randint(70, 180),
            2021: random.randint(80, 220),
            2022: random.randint(90, 260),
        }
        installed_count = installed_apps_base.get(release_year, random.randint(100, 300))

        profile = UserProfile(
            age_range=random.choices(
                ["18-24", "25-34", "35-44", "45-54", "55+"],
                weights=[0.25, 0.3, 0.2, 0.15, 0.1]
            )[0],
            gender=random.choice(["male", "female"]),
            interests=random.sample(
                ["games", "shopping", "entertainment", "sports", "news", "finance",
                 "education", "travel", "food", "health", "tech", "beauty"],
                random.randint(2, 5)
            ),
            installed_apps_count=installed_count,
            session_duration_avg=random.randint(60, 900),
            ad_click_rate=round(random.uniform(0.005, 0.06), 4),
            device_usage_hours_daily=random.randint(2, 10),
        )

        return DeviceInfo(
            device_id_type="gaid",
            device_id=gaid,
            android_id=android_id,
            imei=imei,
            oaid=oaid,
            idfa=None,
            idfv=None,
            openudid=openudid,
            hardware=hardware,
            network=network,
            system=system,
            browser=browser,
            profile=profile,
            device_fingerprint=self._generate_device_fingerprint(android_id, hardware),
            created_at=now - device_age_seconds + random.randint(0, 86400),
        )

    def _generate_ios_device(self, now: int) -> DeviceInfo:
        with self._used_models_lock:
            available_devices = []
            for dev in self.IOS_DEVICE_PROFILES:
                # 使用更精细的key: 机型+存储+iOS版本
                for storage in dev["storage_gb"] if isinstance(dev["storage_gb"], list) else [dev["storage_gb"]]:
                    for ios_ver in ["15.0", "15.5", "15.7", "16.0", "16.3", "16.5", "16.6", "17.0", "17.2", "17.5"]:
                        key = f"{dev['model_name']}|{storage}GB|iOS{ios_ver}"
                        if key not in self.USED_MODELS:
                            available_devices.append((dev, storage, ios_ver, key))
            
            if not available_devices:
                # 所有组合用完了，清空重新开始
                self.USED_MODELS.clear()
                for dev in self.IOS_DEVICE_PROFILES:
                    for storage in dev["storage_gb"] if isinstance(dev["storage_gb"], list) else [dev["storage_gb"]]:
                        for ios_ver in ["15.0", "15.5", "15.7", "16.0", "16.3", "16.5", "16.6", "17.0", "17.2", "17.5"]:
                            key = f"{dev['model_name']}|{storage}GB|iOS{ios_ver}"
                            available_devices.append((dev, storage, ios_ver, key))
            
            dev, storage_gb_val, os_ver, used_key = random.choice(available_devices)
            self.USED_MODELS.add(used_key)
        model_id = dev["model_id"]
        model_name = dev["model_name"]
        release_year = dev["year"]
        screen_w, screen_h, dpi = dev["screen"]
        ram_gb = dev["ram_gb"]
        battery_cap = dev["battery"]

        os_ver_ios = os_ver.replace(".", "_")

        locale_cfg = self._get_locale_config()
        locale, lang_code, country, timezone_name, tz_offset = (
            locale_cfg["locale"], locale_cfg["lang"], locale_cfg["country"],
            locale_cfg["tz"], locale_cfg["offset"]
        )
        mcc_mnc, carrier_cn, carrier_en = random.choice(locale_cfg["carriers"])

        idfa = str(uuid.uuid4()).upper()
        idfv = str(uuid.uuid4()).upper()
        openudid = ''.join(random.choices('0123456789abcdef', k=40))

        age_days = self.device_age_days
        if age_days > 365:
            ios_chrome_pool = self.CHROME_VERSIONS[:5]
        elif age_days > 180:
            ios_chrome_pool = self.CHROME_VERSIONS[2:7]
        else:
            ios_chrome_pool = self.CHROME_VERSIONS[-4:]
        chrome_ver = random.choice(ios_chrome_pool)
        safari_ver = os_ver.rsplit(".", 1)[0]

        is_chrome = random.random() < 0.3
        if is_chrome:
            user_agent = (
                f"Mozilla/5.0 (iPhone; CPU iPhone OS {os_ver_ios} like Mac OS X) "
                f"AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1"
            )
        else:
            user_agent = (
                f"Mozilla/5.0 (iPhone; CPU iPhone OS {os_ver_ios} like Mac OS X) "
                f"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_ver} Mobile/15E148 Safari/604.1"
            )

        device_age_seconds = self.device_age_days * 86400
        total_charge_cycles = int(self.device_age_days * random.uniform(0.25, 0.6))
        battery_health = max(78, min(100, int(100 - self.device_age_days * random.uniform(0.008, 0.03))))
        available_storage_gb = max(2, int(storage_gb_val * random.uniform(0.2, 0.65)))
        install_days_ago = random.randint(max(1, self.device_age_days - 60), self.device_age_days)
        last_update_days_ago = random.randint(1, min(45, self.device_age_days))
        uptime_days = random.randint(0, 7)
        boot_time = now - uptime_days * 86400 - random.randint(0, 86400)

        webgl_unmasked = "Apple GPU"
        cookie_count = min(80, random.randint(10, 25) + int(self.device_age_days * 0.08))
        ls_count = min(60, random.randint(8, 20) + int(self.device_age_days * 0.05))
        cookie_ids = self._generate_cookie_ids(now - install_days_ago * 86400, now)

        build_id = self._generate_ios_build_id(os_ver)

        hardware = HardwareInfo(
            brand="Apple",
            manufacturer="Apple",
            model=model_name,
            device=model_id,
            product=f"{model_id}AP",
            board=model_id,
            hardware="DCPAP",
            platform="ios",
            screen_width=screen_w,
            screen_height=screen_h,
            screen_dpi=dpi,
            screen_density=3.0,
            physical_ram=ram_gb * 1024 * 1024 * 1024,
            total_storage=storage_gb_val * 1024 * 1024 * 1024,
            available_storage=available_storage_gb * 1024 * 1024 * 1024,
            cpu_abi="arm64e",
            cpu_cores=6,
            cpu_max_freq=random.choice([3200000, 3460000, 3780000]),
            gpu_vendor="Apple",
            gpu_renderer=webgl_unmasked,
            webgl_version="WebKit WebGL",
            battery_capacity=battery_cap,
            battery_health_pct=battery_health,
            charge_cycle_count=total_charge_cycles,
            has_touchscreen=True,
            has_wifi=True,
            has_bluetooth=True,
            has_gps=True,
            has_nfc=True,
        )

        network = NetworkInfo(
            ip_address=self._generate_ip_address(country),
            ip_type="ipv4",
            connection_type=random.choice(["wifi", "4g", "5g"]) if release_year >= 2020 else random.choice(["wifi", "4g"]),
            mcc=mcc_mnc[:3],
            mnc=mcc_mnc[3:],
            carrier_name=carrier_en,
            carrier_name_cn=carrier_cn,
            is_roaming=random.random() < 0.03,
            wifi_ssid=random.choice(["Home", "MyNetwork", None, None]),
            wifi_bssid=None,
            network_operator=mcc_mnc,
            sim_operator=mcc_mnc,
            network_country_iso=country.lower(),
        )

        system = SystemInfo(
            os_name="iOS",
            os_version=os_ver,
            os_api_level=int(os_ver.split(".")[0]),
            os_build_id=build_id,
            os_build_fingerprint=f"{model_id}/{os_ver}/{build_id}",
            os_security_patch="",
            os_boot_time=boot_time,
            device_uptime_days=uptime_days,
            sdk_version=config.SDK_VERSION,
            app_package_name=config.DEFAULT_APP_PACKAGE,
            app_version=config.DEFAULT_APP_VERSION,
            app_version_code=125,
            app_install_time=now - install_days_ago * 86400,
            app_update_time=now - last_update_days_ago * 86400,
            app_first_run_time=now - install_days_ago * 86400 + random.randint(60, 3600),
            is_rooted=random.random() < 0.02,
            is_emulator=False,
            is_vpn_active=random.random() < 0.04,
            is_proxy_active=False,
            has_google_play_services=False,
            timezone=timezone_name,
            locale=locale,
            language=lang_code,
            country=country,
            time_offset=tz_offset,
        )

        browser_name = "Safari"
        browser_version = user_agent.split("Version/")[1].split(" ")[0] if "Version/" in user_agent else "17.4"
        
        browser = BrowserFingerprint(
            user_agent=user_agent,
            browser_name=browser_name,
            browser_version=browser_version,
            accept_language=f"{locale},{lang_code};q=0.9" + (",en;q=0.8" if lang_code != "en" else ""),
            platform="iPhone",
            vendor="Apple Computer, Inc.",
            color_depth=24,
            pixel_depth=24,
            screen_width=screen_w,
            screen_height=screen_h,
            viewport_width=screen_w,
            viewport_height=screen_h - random.randint(180, 350),
            device_pixel_ratio=3.0,
            cookies_enabled=True,
            cookie_count=cookie_count,
            local_storage_keys_count=ls_count,
            do_not_track=random.choice([None, None, None, "0", "1"]),
            canvas_fingerprint=self._generate_canvas_fingerprint(webgl_unmasked),
            webgl_vendor="Apple Inc.",
            webgl_renderer=webgl_unmasked,
            webgl_fingerprint=self._generate_webgl_fingerprint("Apple", "Apple GPU"),
            audio_fingerprint=self._generate_audio_fingerprint(),
            fonts_list=self._generate_fonts_list("ios"),
            plugins_list=[],
            timezone_offset=tz_offset,
            touch_support=(True, True, 5),
            hardware_concurrency=hardware.cpu_cores,
            device_memory=round(ram_gb, 1),
            max_touch_points=5,
            webgl_extensions=self._generate_webgl_extensions("Apple", "Apple GPU"),
            cookie_ids=cookie_ids,
        )

        profile = UserProfile(
            age_range=random.choices(
                ["18-24", "25-34", "35-44", "45-54"],
                weights=[0.25, 0.3, 0.2, 0.25]
            )[0],
            gender=random.choice(["male", "female"]),
            interests=random.sample(
                ["games", "shopping", "entertainment", "sports", "news", "finance",
                 "education", "travel", "food", "health", "tech"],
                random.randint(2, 4)
            ),
            installed_apps_count=random.randint(80, 250),
            session_duration_avg=random.randint(60, 600),
            ad_click_rate=round(random.uniform(0.005, 0.05), 4),
            device_usage_hours_daily=random.randint(2, 9),
        )

        return DeviceInfo(
            device_id_type="idfa",
            device_id=idfa,
            android_id=None,
            imei=None,
            oaid=None,
            idfa=idfa,
            idfv=idfv,
            openudid=openudid,
            hardware=hardware,
            network=network,
            system=system,
            browser=browser,
            profile=profile,
            device_fingerprint=self._generate_device_fingerprint(idfv, hardware),
            created_at=now - device_age_seconds + random.randint(0, 86400),
        )

    def _chrome_compatible_with_os(self, chrome_ver: str, os_api: int) -> bool:
        major = int(chrome_ver.split(".")[0])
        return major >= max(80, os_api * 3 + 10)

    def _generate_android_id(self) -> str:
        return ''.join(random.choices('0123456789abcdef', k=16))

    def _generate_imei(self) -> str:
        imei_base = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        return imei_base + self._calculate_luhn(imei_base)

    def _calculate_luhn(self, number: str) -> str:
        digits = [int(d) for d in number]
        checksum = 0
        for i in range(len(digits) - 1, -1, -1):
            d = digits[i]
            if (len(digits) - i) % 2 == 0:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return str((10 - (checksum % 10)) % 10)

    def _generate_oaid(self) -> str:
        return str(uuid.uuid4())

    def _generate_build_id(self, prefix: str) -> str:
        return f"{prefix}.{random.randint(190000, 240000)}.{random.randint(100, 999)}"

    def _generate_build_fingerprint(
        self, manufacturer: str, product: str, model: str, device: str,
        os_ver: str, build_id: str, sdk_ver: str
    ) -> str:
        os_release_map = {
            "8.0": "O", "8.1": "O_MR1",
            "9": "P", "10": "Q", "11": "R", "12": "S", "12L": "S_V2",
            "13": "T", "14": "U",
        }
        release_letter = os_release_map.get(os_ver, "T")
        return (
            f"{manufacturer}/{product}/{device}:{os_ver}/{build_id}:user/release-keys"
        )

    def _generate_ios_build_id(self, os_ver: str) -> str:
        major = os_ver.split(".")[0]
        build_map = {
            "15": ["19A346", "19F77", "19H12"],
            "16": ["20A362", "20D47", "20F66"],
            "17": ["21A329", "21C62", "21F79"],
        }
        return random.choice(build_map.get(major, ["21A329"]))

    def _generate_cookie_ids(self, start_ts: int, end_ts: int) -> Dict[str, str]:
        cookie_ids = {}
        cookie_names = [
            "_ga", "_gid", "_fbp", "_gcl_au", "theme", "lang_pref",
            "session_id", "visitor_id", "user_pref", "_uetvid"
        ]
        now = int(time.time())
        for name in random.sample(cookie_names, random.randint(4, len(cookie_names))):
            if name == "_ga":
                cookie_ids[name] = f"GA1.2.{random.randint(100000000, 999999999)}.{random.randint(start_ts // 1000, end_ts // 1000)}"
            elif name == "_fbp":
                cookie_ids[name] = f"fb.1.{random.randint(start_ts // 1000, end_ts // 1000)}.{random.randint(1000000000, 9999999999)}"
            elif name == "_gcl_au":
                cookie_ids[name] = f"1.1.{random.randint(1000000000, 9999999999)}.{random.randint(start_ts // 1000, end_ts // 1000)}"
            else:
                cookie_ids[name] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(8, 24)))
        return cookie_ids

    def _generate_canvas_fingerprint(self, renderer: str = "") -> str:
        seed_data = f"{renderer}|{random.random()}|{uuid.uuid4()}"
        return hashlib.sha256(seed_data.encode()).hexdigest()[:32]

    def _generate_webgl_fingerprint(self, vendor: str, renderer: str) -> str:
        seed = f"{vendor}|{renderer}|{random.random()}"
        return hashlib.md5(seed.encode()).hexdigest()

    def _generate_audio_fingerprint(self) -> str:
        seed = f"{random.random()}|{uuid.uuid4()}|{random.uniform(0.01, 0.1):.6f}"
        return hashlib.sha1(seed.encode()).hexdigest()[:16]

    def _generate_ip_address(self, country: str) -> str:
        """生成与运营商国家匹配的真实IP地址"""
        country_ranges = {
            "us": [("4.0.0.0", "4.255.255.255"), ("8.0.0.0", "8.255.255.255"),
                   ("47.0.0.0", "47.255.255.255"), ("104.0.0.0", "104.255.255.255")],
            "cn": [("36.0.0.0", "36.255.255.255"), ("110.0.0.0", "110.255.255.255"),
                   ("112.0.0.0", "112.255.255.255"), ("114.0.0.0", "114.255.255.255")],
            "jp": [("126.0.0.0", "126.255.255.255"), ("133.0.0.0", "133.255.255.255")],
            "gb": [("51.0.0.0", "51.255.255.255"), ("81.0.0.0", "81.255.255.255")],
            "de": [("53.0.0.0", "53.255.255.255"), ("79.0.0.0", "79.255.255.255")],
            "in": [("43.0.0.0", "43.255.255.255"), ("103.0.0.0", "103.255.255.255")],
            "br": [("177.0.0.0", "177.255.255.255"), ("189.0.0.0", "189.255.255.255")],
            "kr": [("14.0.0.0", "14.255.255.255"), ("121.0.0.0", "121.255.255.255")],
            "fr": [("37.0.0.0", "37.255.255.255"), ("90.0.0.0", "90.255.255.255")],
            "ca": [("24.0.0.0", "24.255.255.255"), ("70.0.0.0", "70.255.255.255")],
            "id": [("36.64.0.0", "36.95.255.255"), ("103.0.0.0", "103.31.255.255")],
            "ru": [("5.0.0.0", "5.255.255.255"), ("95.0.0.0", "95.255.255.255")],
            "au": [("1.0.0.0", "1.255.255.255"), ("49.0.0.0", "49.255.255.255")],
            "mx": [("187.0.0.0", "187.255.255.255"), ("189.128.0.0", "189.255.255.255")],
            "vn": [("14.160.0.0", "14.191.255.255"), ("113.160.0.0", "113.191.255.255")],
            "th": [("49.0.0.0", "49.255.255.255"), ("171.0.0.0", "171.255.255.255")],
            "ph": [("49.144.0.0", "49.159.255.255"), ("112.198.0.0", "112.211.255.255")],
            "my": [("42.0.0.0", "42.255.255.255"), ("115.128.0.0", "115.135.255.255")],
            "sg": [("103.0.0.0", "103.31.255.255"), ("202.0.0.0", "202.95.255.255")],
        }
        ranges = country_ranges.get(country.lower(), [("10.0.0.0", "10.255.255.255"), ("172.16.0.0", "172.31.255.255")])
        start, end = random.choice(ranges)
        def ip_to_int(ip):
            parts = [int(p) for p in ip.split(".")]
            return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
        def int_to_ip(n):
            return f"{(n >> 24) & 0xFF}.{(n >> 16) & 0xFF}.{(n >> 8) & 0xFF}.{n & 0xFF}"
        s = ip_to_int(start)
        e = ip_to_int(end)
        return int_to_ip(random.randint(s, e))

    def _generate_device_fingerprint(self, stable_id: str, hardware: HardwareInfo) -> str:
        fp_data = (
            f"{stable_id}|{hardware.brand}|{hardware.model}|"
            f"{hardware.screen_width}x{hardware.screen_height}|{hardware.cpu_abi}|"
            f"{hardware.gpu_renderer}"
        )
        return hashlib.sha256(fp_data.encode()).hexdigest()

    def _generate_fonts_list(self, platform: str) -> List[str]:
        if platform == "android":
            all_fonts = [
                "sans-serif", "sans-serif-light", "sans-serif-thin", "sans-serif-condensed",
                "sans-serif-medium", "serif", "monospace", "Roboto", "Noto Sans CJK SC",
                "Droid Sans", "Droid Serif", "Droid Sans Mono", "Roboto Condensed",
                "Roboto Light", "Roboto Medium", "Noto Color Emoji"
            ]
            return random.sample(all_fonts, random.randint(7, min(12, len(all_fonts))))
        else:
            all_fonts = [
                ".SF NS Text", ".SF NS Display", ".SF NS Mono", "Helvetica Neue",
                "Helvetica", "Arial", "San Francisco", "PingFang SC", "PingFang HK",
                "Hiragino Sans GB", "Hiragino Mincho ProN", "Times New Roman",
                "Courier New", "Apple Color Emoji"
            ]
            return all_fonts

    def _generate_plugins_list(self, browser_type: str) -> List[Dict]:
        if browser_type == "chrome":
            return [
                {"name": "Chrome PDF Plugin", "filename": "internal-pdf-viewer",
                 "description": "Portable Document Format"},
                {"name": "Chrome PDF Viewer", "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                 "description": ""},
                {"name": "Native Client", "filename": "internal-nacl-plugin",
                 "description": ""},
            ]
        return []

    def _generate_webgl_extensions(self, vendor: str, renderer: str) -> List[str]:
        common_extensions = [
            "ANGLE_instanced_arrays", "EXT_blend_minmax", "EXT_color_buffer_half_float",
            "EXT_disjoint_timer_query", "EXT_float_blend", "EXT_frag_depth",
            "EXT_shader_texture_lod", "EXT_texture_compression_bptc",
            "EXT_texture_compression_rgtc", "EXT_texture_filter_anisotropic",
            "EXT_sRGB", "KHR_parallel_shader_compile", "OES_element_index_uint",
            "OES_fbo_render_mipmap", "OES_standard_derivatives", "OES_texture_float",
            "OES_texture_float_linear", "OES_texture_half_float",
            "OES_texture_half_float_linear", "OES_vertex_array_object",
            "WEBGL_color_buffer_float", "WEBGL_compressed_texture_astc",
            "WEBGL_compressed_texture_etc", "WEBGL_compressed_texture_etc1",
            "WEBGL_compressed_texture_s3tc", "WEBGL_compressed_texture_s3tc_srgb",
            "WEBGL_debug_renderer_info", "WEBGL_debug_shaders",
            "WEBGL_depth_texture", "WEBGL_draw_buffers",
            "WEBGL_lose_context", "WEBGL_multi_draw",
        ]
        if vendor == "Qualcomm" and "Adreno" in renderer:
            common_extensions.extend([
                "EXT_texture_compression_astc_decode_mode",
                "WEBGL_compressed_texture_astc",
            ])
        count = random.randint(26, len(common_extensions))
        return random.sample(common_extensions, count)

    def get_sdk_request_params(self) -> Dict:
        device = self.generate()
        params = {
            "device_id": device.device_id,
            "device_id_type": device.device_id_type,
            "device_model": device.hardware.model,
            "device_brand": device.hardware.brand,
            "device_manufacturer": device.hardware.manufacturer,
            "os": device.system.os_name.lower(),
            "os_version": device.system.os_version,
            "os_api_level": device.system.os_api_level,
            "screen_width": device.hardware.screen_width,
            "screen_height": device.hardware.screen_height,
            "screen_dpi": device.hardware.screen_dpi,
            "pixel_ratio": device.hardware.screen_density,
            "language": device.system.language,
            "locale": device.system.locale,
            "country": device.system.country,
            "timezone": device.system.timezone,
            "time_offset": device.system.time_offset,
            "carrier": device.network.carrier_name,
            "mcc": device.network.mcc,
            "mnc": device.network.mnc,
            "connection_type": device.network.connection_type,
            "user_agent": device.browser.user_agent,
            "build_id": device.system.os_build_id,
            "build_fingerprint": device.system.os_build_fingerprint,
            "security_patch": device.system.os_security_patch,
            "app_package": device.system.app_package_name,
            "app_version": device.system.app_version,
            "app_install_ts": device.system.app_install_time,
            "sdk_version": device.system.sdk_version,
            "gaid": device.device_id if device.device_id_type == "gaid" else "",
            "idfa": device.idfa or "",
            "idfv": device.idfv or "",
            "android_id": device.android_id or "",
            "imei": device.imei or "",
            "oaid": device.oaid or "",
            "device_age_days": self.device_age_days,
            "battery_health": device.hardware.battery_health_pct,
            "charge_cycles": device.hardware.charge_cycle_count,
            "available_storage_gb": round(device.hardware.available_storage / (1024**3)),
            "is_rooted": int(device.system.is_rooted),
            "is_emulator": int(device.system.is_emulator),
            "is_vpn": int(device.system.is_vpn_active),
            "is_proxy": int(device.system.is_proxy_active),
            "has_gps": int(device.hardware.has_gps),
            "has_nfc": int(device.hardware.has_nfc),
            "webgl_vendor": device.browser.webgl_vendor,
            "webgl_renderer": device.browser.webgl_renderer,
            "canvas_fp": device.browser.canvas_fingerprint,
            "webgl_fp": device.browser.webgl_fingerprint,
            "audio_fp": device.browser.audio_fingerprint,
            "device_fp": device.device_fingerprint,
            "installed_apps": device.profile.installed_apps_count,
            "uptime_days": device.system.device_uptime_days,
            "ts": int(time.time() * 1000),
        }
        return {k: v for k, v in params.items() if v is not None and v != ""}

    def get_click_headers(self) -> Dict:
        device = self.generate()
        headers = {
            "User-Agent": device.browser.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": device.browser.accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA-Platform": f'"{"Android" if device.hardware.platform == "android" else "iOS"}"',
            "X-Forwarded-For": device.network.ip_address,
            "X-Real-IP": device.network.ip_address,
            "X-Device-Model": device.hardware.model,
            "X-Device-Brand": device.hardware.brand,
            "X-OS-Version": device.system.os_version,
            "X-Screen-Size": f"{device.hardware.screen_width}x{device.hardware.screen_height}",
        }
        if "Chrome" in device.browser.user_agent and "CriOS" not in device.browser.user_agent:
            try:
                chrome_major = int(device.browser.user_agent.split("Chrome/")[1].split(".")[0])
                headers["Sec-CH-UA"] = (
                    f'"Chromium";v="{chrome_major}", "Not=A?Brand";v="24", '
                    f'"Google Chrome";v="{chrome_major}"'
                )
            except (IndexError, ValueError):
                pass
        elif "CriOS" in device.browser.user_agent:
            try:
                crios_major = int(device.browser.user_agent.split("CriOS/")[1].split(".")[0])
                headers["Sec-CH-UA"] = (
                    f'"Chromium";v="{crios_major}", "Not=A?Brand";v="24", '
                    f'"Google Chrome";v="{crios_major}"'
                )
            except (IndexError, ValueError):
                pass
        return headers


class DeviceFingerprintScheduler:
    """
    设备指纹定时更新调度器
    
    特性:
    - 定时清理已使用的机型缓存
    - 动态添加新的设备机型
    - 定期刷新Chrome版本池
    - 管理指纹池的多样性
    """
    
    def __init__(self, refresh_interval_seconds: int = 3600):
        self.refresh_interval = refresh_interval_seconds
        self._last_refresh_time = time.time()
        self._refresh_count = 0
        self._lock = threading.RLock()  # 可重入锁，避免 force_refresh 内部调用 get_status 时死锁
        self._chrome_versions_pool = [
            "131.0.6778.200", "131.0.6778.139", "131.0.6778.108",
            "130.0.6723.117", "130.0.6723.86", "130.0.6723.73",
            "129.0.6668.100", "129.0.6668.89", "129.0.6668.70",
            "128.0.6613.138", "128.0.6613.120", "128.0.6613.84",
            "127.0.6533.120", "127.0.6533.99", "127.0.6533.88",
            "126.0.6478.126", "126.0.6478.111", "126.0.6478.71",
        ]
        self._ios_versions_pool = [
            "18.0", "18.1", "18.2", "18.3",
            "17.0", "17.1", "17.2", "17.3", "17.4", "17.5", "17.6",
            "16.6", "16.5", "16.4", "16.3", "16.2",
            "15.7", "15.6", "15.5",
        ]
        self._android_versions_pool = [
            ("14", 34, "34", "2023-10-01", "UP1A"),
            ("14", 34, "34", "2023-11-01", "UP1A"),
            ("13", 33, "33", "2022-08-01", "TP1A"),
            ("13", 33, "33", "2022-10-01", "TP1A"),
            ("12", 32, "32", "2022-03-01", "SP1A"),
            ("11", 30, "30", "2020-09-01", "RP1A"),
        ]
    
    def check_and_refresh(self) -> bool:
        """
        检查是否需要刷新，如果需要则执行刷新
        返回是否执行了刷新
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_refresh_time
            
            if elapsed < self.refresh_interval:
                return False
            
            # 执行刷新
            self._perform_refresh()
            self._last_refresh_time = now
            self._refresh_count += 1
            return True
    
    def _perform_refresh(self):
        """
        执行指纹池刷新
        """
        # 1. 清理已使用机型缓存（保留最近200条），让之前用过的机型可以再次被选中
        with DeviceFingerprintGenerator._used_models_lock:
            models_list = list(DeviceFingerprintGenerator.USED_MODELS)
            if len(models_list) > 200:
                # 只保留最近的200条
                DeviceFingerprintGenerator.USED_MODELS = set(models_list[-200:])
            else:
                # 缓存较少时直接清空，最大化机型多样性
                DeviceFingerprintGenerator.USED_MODELS.clear()
        
        # 2. 更新Chrome版本池
        self._refresh_chrome_versions()
        
        # 3. 更新iOS版本池
        self._refresh_ios_versions()
    
    def _refresh_chrome_versions(self):
        """
        刷新Chrome版本池
        """
        # 以池中最高版本为基础，生成相近的新版本号（Chrome每月约+1大版本）
        try:
            current_majors = sorted(
                {int(v.split(".")[0]) for v in self._chrome_versions_pool if v.split(".")[0].isdigit()},
                reverse=True,
            )
        except (ValueError, IndexError):
            current_majors = [131]
        base_major = current_majors[0] if current_majors else 131
        
        new_versions = []
        for major in (base_major, base_major + 1):
            for _ in range(2):
                minor = random.randint(6500, 6900)
                patch = random.randint(70, 200)
                new_versions.append(f"{major}.0.{minor}.{patch}")
        
        # 合并去重，保留池中原有的部分版本
        new_versions.extend(self._chrome_versions_pool[:12])
        self._chrome_versions_pool = list(set(new_versions))
    
    def _refresh_ios_versions(self):
        """
        刷新iOS版本池
        """
        # 随机补充 iOS 17/18 的子版本，增加多样性
        new_ios_versions = [
            f"18.{random.randint(0, 3)}",
            f"17.{random.randint(0, 6)}",
        ]
        self._ios_versions_pool = list(set(new_ios_versions + self._ios_versions_pool[:10]))
    
    def get_status(self) -> Dict:
        """
        获取调度器状态
        """
        with self._lock:
            now = time.time()
            next_refresh = self._last_refresh_time + self.refresh_interval
            elapsed = now - self._last_refresh_time
            
            return {
                "refresh_count": self._refresh_count,
                "last_refresh_time": self._last_refresh_time,
                "next_refresh_time": next_refresh,
                "time_until_next_refresh": max(0, next_refresh - now),
                "elapsed_since_refresh": elapsed,
                "chrome_versions_count": len(self._chrome_versions_pool),
                "ios_versions_count": len(self._ios_versions_pool),
                "used_models_count": len(DeviceFingerprintGenerator.USED_MODELS),
                "dynamic_devices_added": DeviceFingerprintGenerator._dynamic_model_counter,
            }
    
    def force_refresh(self) -> Dict:
        """
        强制执行刷新
        """
        with self._lock:
            self._perform_refresh()
            self._last_refresh_time = time.time()
            self._refresh_count += 1
            return self.get_status()
    
    def get_chrome_version(self) -> str:
        """
        获取随机Chrome版本
        """
        return random.choice(self._chrome_versions_pool)
    
    def get_ios_version(self) -> str:
        """
        获取随机iOS版本
        """
        return random.choice(self._ios_versions_pool)
    
    def get_android_version(self) -> tuple:
        """
        获取随机Android版本信息
        """
        version_info = random.choice(self._android_versions_pool)
        # 随机选择一个版本
        major_ver = version_info[0]
        api_level = int(version_info[1])
        sdk_level = version_info[2]
        return (major_ver, api_level, sdk_level)


# 全局调度器实例
fingerprint_scheduler = DeviceFingerprintScheduler(refresh_interval_seconds=1800)
