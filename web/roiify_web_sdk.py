import time
import random
import string
import json
import logging
import os
import sys
from typing import Dict, Optional, Any
from urllib.parse import urljoin

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, proxy, ProxyConfig

logger = logging.getLogger(__name__)


class RoiifyWebSDK:
    """
    Roiify Web SDK 真实协议客户端
    
    对应官方 JS SDK 的 Python 实现，协议完全一致：
    - POST /ad/request (请求广告)
    - POST /ad/impression (曝光上报)
    - clickUrl?visitorId=xxx (点击跳转)
    """

    API_ORIGIN = "https://www.roiify.net"
    VISITOR_ID_KEY = "zde_vid"
    
    FINANCIAL_KEYWORDS = {
        "saas_enterprise": [
            "Enterprise SaaS solutions", "Business software for enterprises",
            "Enterprise resource planning", "ERP software for businesses",
            "CRM enterprise solutions", "Business intelligence platforms",
            "Cloud computing for enterprises", "Enterprise security software",
            "SaaS for large corporations", "Enterprise workflow automation",
            "Business management software", "Enterprise collaboration tools",
            "Enterprise software licensing", "Business application platforms",
            "Enterprise IT solutions", "Corporate software solutions"
        ],
        "mortgage": [
            "Home mortgage loans", "Mortgage refinancing", "Best mortgage rates",
            "Home loan comparison", "Mortgage lenders comparison",
            "Fixed rate mortgage", "Adjustable rate mortgage",
            "First time home buyer loans", "Jumbo mortgage loans",
            "Reverse mortgage", "Home equity loans", "Mortgage calculators",
            "Refinance mortgage rates", "Mortgage pre-approval",
            "Home purchase loans", "Mortgage terms explained"
        ],
        "investing_stocks": [
            "Stock trading platforms", "Online stock brokerage",
            "Best stock trading apps", "Stock market investing",
            "Day trading stocks", "Long term stock investments",
            "Stock analysis tools", "Investing in blue chip stocks",
            "Stock portfolio management", "Dividend investing",
            "Growth stocks", "Value investing strategies",
            "Stock market research", "Investment analysis software"
        ],
        "insurance_health": [
            "Health insurance plans", "Best health insurance companies",
            "Affordable health insurance", "Individual health insurance",
            "Family health insurance", "Group health insurance",
            "Health insurance quotes", "Medical insurance coverage",
            "Health insurance marketplace", "Obamacare health plans",
            "Short term health insurance", "Dental and vision insurance",
            "Health savings account", "Health insurance deductibles"
        ],
        "crypto_trading": [
            "Cryptocurrency trading", "Bitcoin trading platform",
            "Crypto exchange comparison", "Digital currency trading",
            "Best crypto trading app", "Cryptocurrency investment",
            "Altcoin trading", "Crypto trading strategies",
            "Bitcoin wallet", "Crypto portfolio management",
            "DeFi trading", "NFT marketplace",
            "Cryptocurrency mining", "Crypto trading signals"
        ],
        "insurance_life": [
            "Term life insurance", "Whole life insurance",
            "Life insurance quotes", "Best life insurance companies",
            "Permanent life insurance", "Universal life insurance",
            "Life insurance for seniors", "Family life insurance",
            "Life insurance policy comparison", "Affordable life insurance",
            "Life insurance benefits", "Life insurance riders",
            "Group life insurance", "Life insurance underwriting"
        ],
        "personal_loans": [
            "Personal Loans", "Bad Credit Loans", "Debt Consolidation", 
            "Mortgage Refinance", "Best personal loans for bad credit",
            "How to consolidate credit card debt", "Current mortgage refinance rates today",
            "Fast cash loans for emergencies", "Emergency loans",
            "Installment loans", "Secured loans", "Unsecured loans",
            "Personal loan comparison", "Loan eligibility requirements",
            "Fixed rate personal loans", "Flexible repayment loans"
        ],
        "credit_cards_premium": [
            "Premium credit cards", "Black credit cards", "Luxury credit cards",
            "Platinum credit cards", "Best premium travel credit cards",
            "High limit credit cards", "Business premium credit cards",
            "Exclusive credit card benefits", "Premium rewards programs",
            "Concierge credit cards", "First class credit cards",
            "Elite credit cards", "Premium credit card lounge access",
            "VIP credit cards", "Premium credit card perks"
        ],
        "b2b_software": [
            "B2B software solutions", "Enterprise software for business",
            "Business software tools", "B2B SaaS platforms",
            "Sales automation software", "Marketing automation tools",
            "Customer relationship management", "Supply chain management",
            "B2B ecommerce platforms", "Business intelligence software",
            "Data analytics tools", "Enterprise project management",
            "B2B integration software", "Business process automation"
        ],
        "legal_services": [
            "Legal services online", "Personal injury lawyer",
            "Best law firms", "Criminal defense attorney",
            "Family law services", "Business legal services",
            "Immigration lawyer", "Estate planning attorney",
            "Legal consultation", "Lawyer referral service",
            "Accident attorney", "Workers compensation lawyer",
            "Bankruptcy attorney", "Divorce lawyer"
        ],
        "real_estate_investing": [
            "Real estate investing", "Rental property investment",
            "Real estate crowdfunding", "Property investment strategies",
            "Commercial real estate", "Residential property investment",
            "Real estate REIT investments", "House flipping guide",
            "Real estate investment trust", "Property management tips",
            "Real estate market analysis", "Investment property loans"
        ],
        "debt_consolidation": [
            "Debt consolidation loans", "Debt consolidation services",
            "Best debt consolidation companies", "Credit card debt consolidation",
            "Debt management plans", "Debt consolidation programs",
            "Debt relief options", "Consolidate debt online",
            "Debt consolidation calculator", "Debt settlement vs consolidation",
            "Bad credit debt consolidation", "Debt consolidation reviews",
            "Debt consolidation loans for bad credit", "Debt consolidation tips"
        ],
        "software_subscription": [
            "Software as a service", "SaaS subscription", "Cloud software",
            "Productivity software subscription", "Project management software",
            "Accounting software subscription", "Design software subscription",
            "CRM software subscription", "Team collaboration tools",
            "Antivirus subscription", "Backup software subscription",
            "Video editing software", "Graphic design software",
            "Development tools subscription", "Business software subscription"
        ],
        "ecommerce_high_ticket": [
            "High end electronics", "Luxury goods online", "Premium products",
            "High ticket items", "Luxury watches", "Designer handbags",
            "Premium jewelry", "High end furniture", "Luxury cars",
            "Premium appliances", "High end audio equipment",
            "Designer clothing", "Luxury travel", "Premium home goods",
            "High end fashion", "Luxury accessories"
        ],
        "education_professional": [
            "Professional certification programs", "Online business courses",
            "Executive education programs", "Professional development courses",
            "MBA programs online", "Project management certification",
            "Digital marketing courses", "Coding bootcamp online",
            "Professional training programs", "Continuing education online",
            "Career advancement courses", "Industry certification training",
            "Business management courses", "Leadership development programs"
        ]
    }
    
    AD_CATEGORIES = [
        {"id": "saas_enterprise", "name": "Enterprise SaaS", "category": "Business"},
        {"id": "finance_mortgage", "name": "Mortgage", "category": "Finance"},
        {"id": "finance_investing_stocks", "name": "Stock Investing", "category": "Finance"},
        {"id": "finance_insurance_health", "name": "Health Insurance", "category": "Finance"},
        {"id": "finance_insurance_life", "name": "Life Insurance", "category": "Finance"},
        {"id": "finance_crypto_trading", "name": "Crypto Trading", "category": "Finance"},
        {"id": "finance_personal_loans", "name": "Personal Loans", "category": "Finance"},
        {"id": "finance_credit_cards_premium", "name": "Premium Credit Cards", "category": "Finance"},
        {"id": "b2b_software", "name": "B2B Software", "category": "Business"},
        {"id": "legal_services", "name": "Legal Services", "category": "Legal"},
        {"id": "real_estate_investing", "name": "Real Estate Investing", "category": "Real Estate"},
        {"id": "finance_debt_consolidation", "name": "Debt Consolidation", "category": "Finance"},
        {"id": "software_subscription", "name": "Software Subscription", "category": "Business"},
        {"id": "ecommerce_high_ticket", "name": "High Ticket E-commerce", "category": "Retail"},
        {"id": "education_professional", "name": "Professional Education", "category": "Education"},
    ]

    def __init__(
        self,
        api_origin: Optional[str] = None,
        user_agent: Optional[str] = None,
        accept_language: Optional[str] = None,
        timezone: Optional[str] = None,
        locale: Optional[str] = None,
        visitor_id: Optional[str] = None,
        session: Optional[requests.Session] = None,
        proxy_config: Optional[ProxyConfig] = None,
        use_proxy: Optional[bool] = None,
        device_info: Any = None,
    ):
        self.api_origin = (api_origin or self.API_ORIGIN).rstrip("/")
        self.user_agent = user_agent or self._default_ua()
        self.accept_language = accept_language or "en-US,en;q=0.9"
        self.timezone = timezone or "UTC"
        self.locale = locale or "en-US"
        self.visitor_id = visitor_id or self._generate_visitor_id()
        self.session = session or requests.Session()
        self.proxy_config = proxy_config or proxy
        self.last_ad: Optional[Dict[str, Any]] = None
        self.last_impression_sent = False
        self.last_click_url: Optional[str] = None
        self.requests_count = 0
        self.device_info = device_info

        if use_proxy is None:
            use_proxy = self.proxy_config.enabled
        self.proxy_enabled = use_proxy

        if self.proxy_enabled:
            proxies = self.proxy_config.get_proxies_dict()
            if proxies:
                self.session.proxies.update(proxies)
                logger.info(f"Proxy enabled: {self.proxy_config.host}:{self.proxy_config.port}")
            else:
                logger.warning("Proxy enabled but not configured")
                self.proxy_enabled = False

        logger.info(f"RoiifyWebSDK initialized")
        logger.info(f"  API: {self.api_origin}")
        logger.info(f"  Visitor ID: {self.visitor_id}")
        logger.info(f"  Language: {self.locale} | Timezone: {self.timezone}")
        logger.info(f"  Proxy: {'enabled' if self.proxy_enabled else 'disabled'}")
        logger.info(f"  UA: {self.user_agent[:70]}...")

    @staticmethod
    def _default_ua() -> str:
        return (
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.6422.110 Mobile Safari/537.36"
        )

    def _generate_visitor_id(self) -> str:
        random_part = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        ts_part = int(time.time()).to_bytes(5, "big").hex()
        return f"v_{random_part}{ts_part}"

    def _get_headers(self, is_json: bool = True) -> Dict[str, str]:
        chrome_ver = self._extract_chrome_version()
        is_android = "Android" in self.user_agent
        is_ios = "iPhone" in self.user_agent or "iPad" in self.user_agent
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": self.accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": self.api_origin,
            "Referer": self.api_origin + "/",
            "Sec-CH-UA": f'"Chromium";v="{chrome_ver}", "Not=A?Brand";v="24", "Google Chrome";v="{chrome_ver}"',
            "Sec-CH-UA-Mobile": "?1" if (is_android or is_ios) else "?0",
            "Sec-CH-UA-Platform": '"Android"' if is_android else '"iOS"' if is_ios else '"Windows"',
            "Sec-CH-UA-Full-Version": f'"{chrome_ver}.0.0.0"',
            "Sec-CH-Timezone": self.timezone,
            "Sec-CH-Locale": self.locale,
            "Sec-CH-Device-Memory": "4",
            "Sec-CH-Viewport-Width": "375",
            "Sec-CH-Prefers-Color-Scheme": "light",
            "Sec-CH-Arch": '"arm64"' if (is_android or is_ios) else '"x86"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-User": "?1",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "TE": "Trailers",
        }
        if is_json:
            headers["Content-Type"] = "application/json"
        return headers
    
    def _extract_chrome_version(self) -> str:
        import re
        match = re.search(r"Chrome/(\d+)", self.user_agent) or re.search(r"CriOS/(\d+)", self.user_agent)
        if match:
            return match.group(1)
        return str(random.randint(120, 126))

    def request_ad(
        self,
        placement_id: str,
        ad_format: str = "banner",
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.api_origin}/ad/request"
        
        category_weights = [
            4.0,  # saas_enterprise (highest value)
            3.5,  # finance_mortgage
            3.0,  # finance_investing_stocks
            2.8,  # finance_insurance_health (high value)
            2.5,  # finance_insurance_life
            2.2,  # finance_crypto_trading
            1.8,  # finance_personal_loans
            1.5,  # finance_credit_cards_premium
            1.5,  # b2b_software
            1.3,  # legal_services (high value)
            1.2,  # real_estate_investing
            1.0,  # finance_debt_consolidation
            0.8,  # software_subscription
            0.6,  # ecommerce_high_ticket
            0.5,  # education_professional
        ]
        category = random.choices(self.AD_CATEGORIES, weights=category_weights, k=1)[0]
        
        category_id_to_keyword = {
            "saas_enterprise": "saas_enterprise",
            "finance_mortgage": "mortgage",
            "finance_investing_stocks": "investing_stocks",
            "finance_insurance_health": "insurance_health",
            "finance_crypto_trading": "crypto_trading",
            "finance_insurance_life": "insurance_life",
            "finance_personal_loans": "personal_loans",
            "finance_credit_cards_premium": "credit_cards_premium",
            "b2b_software": "b2b_software",
            "legal_services": "legal_services",
            "real_estate_investing": "real_estate_investing",
            "finance_debt_consolidation": "debt_consolidation",
            "software_subscription": "software_subscription",
            "ecommerce_high_ticket": "ecommerce_high_ticket",
            "education_professional": "education_professional",
        }
        keyword_group = category_id_to_keyword.get(category["id"], "personal_loans")
        keywords = self.FINANCIAL_KEYWORDS.get(keyword_group, self.FINANCIAL_KEYWORDS["personal_loans"])
        title_keyword = random.choice(keywords)
        meta_keywords = random.sample(keywords, min(3, len(keywords)))
        
        page_titles = [
            f"What are the best {title_keyword.lower()} in 2026?",
            f"Best {title_keyword.lower()} for beginners",
            f"{title_keyword} review and comparison",
            f"Top {title_keyword.lower()} - complete guide",
            f"{title_keyword} vs other options",
            f"Compare {title_keyword.lower()} online",
            f"How to choose the best {title_keyword.lower()}",
            f"Ultimate guide to {title_keyword.lower()}",
        ]
        
        content_domains = [
            "https://www.financeadvice.com",
            "https://www.investmentguide.com",
            "https://www.creditcardreviews.com",
            "https://www.insurancecompare.com",
            "https://www.personalloansguide.com",
            "https://www.mortgagetips.com",
            "https://www.debtreliefhelp.com",
            "https://www.retirementplanning.org",
        ]
        base_domain = random.choice(content_domains)
        
        page_title = random.choice(page_titles)
        page_url = f"{base_domain}/{keyword_group}/{title_keyword.lower().replace(' ', '-')}"
        
        content_descriptions = {
            "saas_enterprise": [
                "Enterprise SaaS solutions for businesses. Compare top CRM, ERP, and collaboration tools.",
                "Best enterprise software for productivity and workflow management.",
                "Enterprise-grade SaaS platforms for digital transformation.",
                "Comprehensive reviews of enterprise software solutions and services.",
            ],
            "finance_mortgage": [
                "Mortgage rates and refinancing options. Find the best home loan deals.",
                "Guide to mortgage loans, refinancing, and home financing.",
                "Compare mortgage rates from top lenders and banks.",
                "Expert advice on home loans and mortgage refinancing.",
            ],
            "finance_investing_stocks": [
                "Stock market investing strategies and tips for beginners.",
                "Investment analysis software and tools for traders.",
                "Best stock trading platforms and brokerage accounts.",
                "Professional stock market research and investment guidance.",
            ],
            "finance_insurance_health": [
                "Health insurance plans and coverage options for individuals and families.",
                "Compare health insurance quotes from top providers.",
                "Affordable health insurance solutions for every budget.",
                "Complete guide to health insurance and medical coverage.",
            ],
            "finance_crypto_trading": [
                "Cryptocurrency trading platforms and exchange reviews.",
                "Bitcoin and altcoin trading strategies for investors.",
                "Best crypto wallets and trading apps.",
                "Complete cryptocurrency investment guide for beginners.",
            ],
            "finance_insurance_life": [
                "Life insurance quotes and policy comparisons.",
                "Best life insurance companies and coverage options.",
                "Term vs whole life insurance guide.",
                "Protect your family with the right life insurance policy.",
            ],
            "finance_personal_loans": [
                "Personal loan options for all credit types.",
                "Compare personal loans and find the best rates.",
                "Fast cash loans for emergencies.",
                "Personal loan comparison and reviews.",
            ],
            "finance_credit_cards_premium": [
                "Premium credit cards with exclusive benefits.",
                "Best travel rewards credit cards.",
                "Luxury credit cards with high limits.",
                "Compare premium credit card offers and benefits.",
            ],
            "b2b_software": [
                "B2B software solutions for modern businesses.",
                "Best business software tools and platforms.",
                "Enterprise software reviews and comparisons.",
                "Boost productivity with top B2B software solutions.",
            ],
            "legal_services": [
                "Legal services and attorney directory for all practice areas.",
                "Find the best lawyer for your legal needs.",
                "Expert legal advice and attorney referrals.",
                "Compare law firms and legal service providers.",
            ],
            "real_estate_investing": [
                "Real estate investing strategies and property investment guide.",
                "Learn how to invest in rental properties and REITs.",
                "Real estate crowdfunding platforms and opportunities.",
                "Complete guide to real estate investment strategies.",
            ],
            "finance_debt_consolidation": [
                "Debt consolidation loans and services.",
                "How to consolidate credit card debt.",
                "Best debt relief options.",
                "Take control of your finances with debt consolidation.",
            ],
            "software_subscription": [
                "Best SaaS subscription services for businesses.",
                "Productivity software and cloud tools.",
                "Subscription-based software reviews.",
                "Top software subscriptions for professionals.",
            ],
            "ecommerce_high_ticket": [
                "Luxury goods and high-end products online.",
                "Premium electronics and designer fashion.",
                "High ticket item shopping guide.",
                "Exclusive deals on luxury products.",
            ],
            "education_professional": [
                "Professional certification programs and career advancement courses.",
                "Best online business courses and executive education.",
                "Advance your career with professional training programs.",
                "Industry-recognized certifications and online learning.",
            ],
        }
        
        content_tags = {
            "saas_enterprise": ["SaaS", "enterprise", "business", "productivity", "CRM", "ERP", "B2B", "software"],
            "finance_mortgage": ["mortgage", "home loan", "refinance", "real estate", "housing", "lending"],
            "finance_investing_stocks": ["stocks", "investing", "trading", "stock market", "investment", "brokerage"],
            "finance_insurance_health": ["health insurance", "insurance", "medical", "healthcare", "coverage", "wellness"],
            "finance_crypto_trading": ["cryptocurrency", "bitcoin", "crypto", "trading", "blockchain", "exchange"],
            "finance_insurance_life": ["life insurance", "insurance", "coverage", "policy", "protection", "family"],
            "finance_personal_loans": ["personal loan", "loans", "credit", "debt", "borrow", "lending"],
            "finance_credit_cards_premium": ["credit card", "premium", "rewards", "travel", "luxury", "exclusive"],
            "b2b_software": ["B2B", "software", "enterprise", "business", "SaaS", "productivity"],
            "legal_services": ["legal", "lawyer", "attorney", "law firm", "legal services", "consultation"],
            "real_estate_investing": ["real estate", "investing", "property", "rental", "REIT", "investment"],
            "finance_debt_consolidation": ["debt consolidation", "debt", "credit", "finance", "consolidate", "relief"],
            "software_subscription": ["software", "subscription", "SaaS", "cloud", "productivity", "tools"],
            "ecommerce_high_ticket": ["luxury", "premium", "high-end", "designer", "electronics", "shopping"],
            "education_professional": ["education", "professional", "certification", "training", "career", "courses"],
        }
        
        content_description = random.choice(content_descriptions.get(category["id"], content_descriptions["software_subscription"]))
        content_tag_list = content_tags.get(category["id"], content_tags["software_subscription"])
        
        user_interests = [
            "business", "finance", "technology", "investing", "personal finance",
            "entrepreneurship", "stocks", "real estate", "luxury", "travel",
            "marketing", "healthcare", "education", "fitness", "entrepreneur"
        ]
        
        traffic_source = random.choices(
            ["organic", "direct", "referral", "social", "email", "paid_search"],
            weights=[4.0, 3.0, 2.0, 1.5, 1.0, 0.5],
            k=1
        )[0]
        
        session_depth = random.choices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            weights=[1.5, 2.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5],
            k=1
        )[0]
        
        is_returning_visitor = random.random() < 0.65
        
        viewability_score = random.uniform(0.65, 0.95)
        
        payload = {
            "placementId": placement_id,
            "format": ad_format,
            "visitorId": self.visitor_id,
            "locale": self.locale,
            "language": self.accept_language.split(",")[0] if self.accept_language else "en",
            "timezone": self.timezone,
            "sdkVersion": config.SDK_VERSION,
            "category": category["id"],
            "categoryName": category["name"],
            "pageTitle": page_title,
            "pageKeywords": ",".join(meta_keywords),
            "contentTopic": category["category"],
            "pageType": "article",
            "pageUrl": page_url,
            "contentDescription": content_description,
            "contentTags": ",".join(content_tag_list),
            "userInterests": ",".join(random.sample(user_interests, 5)),
            "contentLength": random.randint(800, 3500),
            "contentQuality": round(random.uniform(0.75, 0.98), 2),
            "pageRank": random.randint(3, 10),
            "domainAuthority": random.randint(40, 85),
            "trafficQualityScore": round(random.uniform(0.82, 0.97), 2),
            "userEngagementScore": round(random.uniform(0.7, 0.95), 2),
            "pageViews": random.randint(5000, 100000),
            "avgTimeOnPage": random.randint(45, 180),
            "avgSessionDuration": random.randint(90, 420),
            "bounceRate": round(random.uniform(0.25, 0.55), 2),
            "mobileOptimized": True,
            "sslEnabled": True,
            "pageAge": random.randint(60, 730),
            "trafficSource": traffic_source,
            "sessionDepth": session_depth,
            "isReturningVisitor": is_returning_visitor,
            "viewabilityScore": round(viewability_score, 2),
            "scrollDepth": random.randint(35, 95),
            "pagesPerSession": round(random.uniform(1.5, 4.5), 1),
            "userIntent": random.choice(["informational", "commercial", "navigational"]),
            "userAgeRange": random.choice(["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]),
            "userIncomeLevel": random.choices(
                ["low", "medium", "high", "premium"],
                weights=[1.0, 2.5, 3.5, 2.0],
                k=1
            )[0],
            "deviceTrustScore": round(random.uniform(0.7, 0.95), 2),
        }
        # 添加设备信息
        dev = self.device_info
        if dev:
            hw = getattr(dev, "hardware", None)
            sys_info = getattr(dev, "system", None)
            net = getattr(dev, "network", None)
            browser = getattr(dev, "browser", None)
            # 设备ID
            if hasattr(dev, "device_id"):
                payload["deviceId"] = dev.device_id
                payload["deviceIdType"] = getattr(dev, "device_id_type", "gaid")
            if hw:
                payload["deviceModel"] = hw.model
                payload["deviceBrand"] = hw.brand
                payload["deviceType"] = getattr(hw, "device_type", "mobile")
                if hasattr(hw, "screen_width") and hasattr(hw, "screen_height"):
                    payload["screenWidth"] = hw.screen_width
                    payload["screenHeight"] = hw.screen_height
            if sys_info:
                payload["os"] = sys_info.os_name
                payload["osVersion"] = sys_info.os_version
                payload["country"] = sys_info.country
                if hasattr(sys_info, "app_package_name"):
                    payload["appPackage"] = sys_info.app_package_name or config.DEFAULT_APP_PACKAGE
                if hasattr(sys_info, "app_version"):
                    payload["appVersion"] = sys_info.app_version or "1.0.0"
            if net:
                payload["carrier"] = net.carrier_name
                payload["connectionType"] = net.connection_type
            if browser:
                browser_name = getattr(browser, "browser_name", None)
                browser_version = getattr(browser, "browser_version", None)
                if not browser_name or not browser_version:
                    ua = getattr(browser, "user_agent", "")
                    if "Chrome/" in ua:
                        browser_name = "Chrome"
                        browser_version = ua.split("Chrome/")[1].split(" ")[0].split(".")[0]
                    elif "CriOS/" in ua:
                        browser_name = "CriOS"
                        browser_version = ua.split("CriOS/")[1].split(" ")[0].split(".")[0]
                    else:
                        browser_name = "Chrome"
                        browser_version = "125"
                payload["browserType"] = browser_name
                payload["browserVersion"] = browser_version
                if hasattr(browser, "viewport_width") and hasattr(browser, "viewport_height"):
                    payload["viewportWidth"] = browser.viewport_width
                    payload["viewportHeight"] = browser.viewport_height
                if hasattr(browser, "device_pixel_ratio"):
                    payload["devicePixelRatio"] = browser.device_pixel_ratio

        logger.info(f"Requesting ad: placement={placement_id}, format={ad_format}")
        logger.info(f"  Category: {category['name']} | Topic: {category['category']}")
        logger.info(f"  Page Title: {payload['pageTitle'][:60]}")
        logger.info(f"  Keywords: {', '.join(meta_keywords)[:80]}")

        current_session = self.session

        for attempt in range(3):
            try:
                response = current_session.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=15,
                )

                logger.debug(f"Response status: {response.status_code}")

                if response.status_code == 204:
                    logger.info("No ad available (204 No Content)")
                    self.last_ad = None
                    return None

                if not response.ok:
                    logger.warning(f"Ad request failed: HTTP {response.status_code}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return None

                data = response.json()
                if not data or not data.get("ad"):
                    logger.info("No ad in response")
                    self.last_ad = None
                    return None

                self.last_ad = data
                self.last_impression_sent = False
                self.requests_count += 1

                ad = data.get("ad", {})
                logger.info(f"Ad received: type={ad.get('type', 'banner')}")
                if ad.get("title"):
                    logger.info(f"  Title: {ad['title'][:60]}")
                if ad.get("description"):
                    logger.info(f"  Description: {ad['description'][:60]}")
                logger.info(f"  Click URL: {data.get('clickUrl', '')[:80]}...")
                logger.info(f"  Has impression token: {bool(data.get('impressionToken'))}")

                return data

            except requests.exceptions.Timeout:
                logger.warning(f"Ad request timed out (attempt {attempt+1}), retrying...")
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None

            except requests.exceptions.ConnectionError as e:
                err_str = str(e)
                logger.warning(f"Ad request connection error (attempt {attempt+1}): {err_str[:100]}")
                if "ConnectionResetError" in err_str or "ECONNRESET" in err_str:
                    logger.info(f"  Connection reset, rotating session...")
                    current_session = requests.Session()
                    if self.proxy_enabled:
                        proxies = self.proxy_config.get_proxies_dict(new_session=True)
                        if proxies:
                            current_session.proxies.update(proxies)
                    self.session = current_session
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None

            except Exception as e:
                logger.error(f"Ad request error (attempt {attempt+1}): {e}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None

    def send_impression(self, impression_token: Optional[str] = None, view_duration: float = 0) -> bool:
        token = impression_token or (
            self.last_ad.get("impressionToken") if self.last_ad else None
        )

        if not token:
            logger.warning("No impression token available")
            return False

        if self.last_impression_sent:
            logger.info("Impression already sent")
            return True

        url = f"{self.api_origin}/ad/impression"
        payload = {
            "token": token,
            "visitorId": self.visitor_id,
            "viewDuration": round(view_duration * 1000),
            "adInView": True,
        }
        # 添加设备信息
        dev = self.device_info
        if dev:
            hw = getattr(dev, "hardware", None)
            if hw and hasattr(hw, "screen_width") and hasattr(hw, "screen_height"):
                payload["containerWidth"] = hw.screen_width
                payload["containerHeight"] = hw.screen_height

        logger.info("Sending impression...")

        current_session = self.session

        for attempt in range(3):
            try:
                response = current_session.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=15,
                )

                if response.ok:
                    self.last_impression_sent = True
                    logger.info("✓ Impression reported successfully")
                    return True
                else:
                    logger.warning(f"Impression failed: HTTP {response.status_code}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return False

            except requests.exceptions.Timeout:
                logger.warning(f"Impression timed out (attempt {attempt+1}), retrying...")
                if attempt < 2:
                    time.sleep(2)
                    continue
                return False

            except requests.exceptions.ConnectionError as e:
                err_str = str(e)
                logger.warning(f"Impression connection error (attempt {attempt+1}): {err_str[:100]}")
                if "ConnectionResetError" in err_str or "ECONNRESET" in err_str:
                    logger.info(f"  Connection reset, rotating session...")
                    current_session = requests.Session()
                    if self.proxy_enabled:
                        proxies = self.proxy_config.get_proxies_dict(new_session=True)
                        if proxies:
                            current_session.proxies.update(proxies)
                    self.session = current_session
                if attempt < 2:
                    time.sleep(2)
                    continue
                return False

            except Exception as e:
                logger.error(f"Impression error (attempt {attempt+1}): {e}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                return False

    def get_click_url(self) -> Optional[str]:
        if not self.last_ad or not self.last_ad.get("clickUrl"):
            return None
        final_url = self.last_ad["clickUrl"]
        
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(final_url)
        params = parse_qs(parsed.query)
        if "visitorId" not in params:
            params["visitorId"] = self.visitor_id
        # 添加设备追踪参数
        dev = self.device_info
        if dev:
            if "os" not in params:
                sys_info = getattr(dev, "system", None)
                if sys_info:
                    params["os"] = sys_info.os_name
                    params["osVersion"] = sys_info.os_version
            if "language" not in params:
                params["language"] = self.accept_language.split(",")[0] if self.accept_language else "en"
            if "timezone" not in params:
                params["timezone"] = self.timezone
            if "screenWidth" not in params:
                hw = getattr(dev, "hardware", None)
                if hw:
                    if hasattr(hw, "screen_width"):
                        params["screenWidth"] = str(hw.screen_width)
                    if hasattr(hw, "screen_height"):
                        params["screenHeight"] = str(hw.screen_height)
                    if hasattr(hw, "model"):
                        params["deviceModel"] = hw.model
        new_query = urlencode(params, doseq=True)
        final_url = urlunparse(parsed._replace(query=new_query))
        
        self.last_click_url = final_url
        return final_url

    def send_click(self) -> bool:
        click_url = self.get_click_url()
        if not click_url:
            logger.warning("No click URL available")
            return False
        logger.info(f"Sending click to: {click_url[:80]}...")
        
        headers = self._get_headers(is_json=False)
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        headers["Accept-Language"] = self.accept_language
        headers["Sec-Fetch-Dest"] = "document"
        headers["Sec-Fetch-Mode"] = "navigate"
        headers["Sec-Fetch-Site"] = "cross-site"
        headers["Sec-Fetch-User"] = "?1"
        headers["Upgrade-Insecure-Requests"] = "1"
        headers["Cache-Control"] = "max-age=0"
        headers["Connection"] = "keep-alive"
        headers["DNT"] = "1"
        
        if "Android" in self.user_agent:
            headers["X-Requested-With"] = "com.roiify.app"
        elif "iPhone" in self.user_agent:
            headers["X-Requested-With"] = "com.roiify.ios"
        
        current_session = self.session
        current_click_url = click_url
        
        for attempt in range(3):
            try:
                response = current_session.get(
                    current_click_url,
                    headers=headers,
                    timeout=10,
                    allow_redirects=True,
                )
                
                self.last_click_url = response.url
                
                if response.status_code in (200, 301, 302, 303, 307, 308):
                    logger.info(f"✓ Click sent (attempt {attempt+1}), final URL: {response.url[:80]}...")
                    return True
                elif response.status_code >= 200 and response.status_code < 400:
                    logger.info(f"✓ Click sent (attempt {attempt+1}, status {response.status_code})")
                    return True
                else:
                    logger.warning(f"Click request failed (attempt {attempt+1}): HTTP {response.status_code}")
            
            except requests.exceptions.Timeout:
                logger.warning(f"Click request timed out (attempt {attempt+1})")
            
            except requests.exceptions.ConnectionError as e:
                err_str = str(e)
                logger.warning(f"Click request connection error (attempt {attempt+1}): {err_str[:100]}")
                
                if "ConnectionResetError" in err_str or "ECONNRESET" in err_str:
                    logger.info(f"  Connection reset, rotating session...")
                    current_session = requests.Session()
                    if self.proxy_enabled:
                        proxies = self.proxy_config.get_proxies_dict(new_session=True)
                        if proxies:
                            current_session.proxies.update(proxies)
                    self.session = current_session
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Click request error (attempt {attempt+1}): {str(e)[:100]}")
            
            except Exception as e:
                logger.error(f"Click request unexpected error (attempt {attempt+1}): {str(e)[:100]}")
        
        logger.error(f"Click request failed after 3 attempts")
        return False

    def simulate_click(self, view_duration: float = 3.0) -> Optional[str]:
        import time
        time.sleep(min(view_duration, 5))

        if self.last_ad and self.last_ad.get("impressionToken"):
            self.send_impression()

        return self.get_click_url()

    def verify_inview_and_send_impression(
        self,
        check_interval_ms: int = 250,
        required_time_ms: int = 2000,
        max_checks: int = 120,
        is_in_view: bool = True,
    ) -> bool:
        if not self.last_ad or not self.last_ad.get("impressionToken"):
            return False

        visible_time_ms = 0

        for _ in range(max_checks):
            if self.last_impression_sent:
                break

            if is_in_view:
                visible_time_ms += check_interval_ms
                if visible_time_ms >= required_time_ms:
                    return self.send_impression()
            else:
                visible_time_ms = 0

            time.sleep(check_interval_ms / 1000.0)

        return self.last_impression_sent

    def report_conversion(
        self,
        event_name: str = "register",
        value: float = 0.0,
        currency: str = "USD",
    ) -> bool:
        url = f"{self.api_origin}/ad/conversion"
        payload = {
            "visitorId": self.visitor_id,
            "event": event_name,
            "value": value,
            "currency": currency,
        }
        logger.info(f"Reporting conversion: event={event_name}, visitorId={self.visitor_id}")
        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10,
            )
            if response.ok:
                logger.info(f"✓ Conversion reported successfully")
                return True
            else:
                logger.warning(f"Conversion report failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Conversion report error: {e}")
            return False

    def reset(self, rotate_proxy: bool = False):
        self.last_ad = None
        self.last_impression_sent = False
        self.last_click_url = None
        self.visitor_id = self._generate_visitor_id()
        self.session = requests.Session()

        if self.proxy_enabled:
            proxies = self.proxy_config.get_proxies_dict(new_session=rotate_proxy)
            if proxies:
                self.session.proxies.update(proxies)

        logger.info(f"SDK reset, new visitorId: {self.visitor_id}")

    def rotate_ip(self):
        self.reset(rotate_proxy=True)
        logger.info("IP rotated")
