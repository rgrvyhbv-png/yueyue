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
        ],
        "healthcare_medical": [
            "Healthcare services providers", "Medical clinics and hospitals",
            "Private healthcare facilities", "Medical specialist services",
            "Healthcare consulting", "Medical treatment centers",
            "Specialized medical services", "Healthcare management",
            "Medical tourism", "VIP healthcare services",
            "Premium medical care", "Healthcare professionals",
            "Medical diagnosis services", "Healthcare technology"
        ],
        "automotive_luxury": [
            "Luxury car brands", "Premium automobile dealers",
            "High-end luxury vehicles", "Luxury car leasing",
            "Exotic cars for sale", "Luxury sports cars",
            "Premium SUVs", "Luxury electric vehicles",
            "Exclusive car dealerships", "Luxury car maintenance",
            "High-performance cars", "Luxury automotive accessories",
            "VIP car services", "Luxury car customization"
        ],
        "real_estate_luxury": [
            "Luxury real estate properties", "High-end luxury homes",
            "Luxury villas for sale", "Exclusive real estate listings",
            "Premium properties", "Luxury penthouses",
            "Luxury beachfront properties", "High-end residential",
            "Luxury commercial real estate", "Exclusive property listings",
            "Luxury real estate investments", "VIP property viewings",
            "Luxury waterfront homes", "Premium real estate services"
        ],
        "wealth_management": [
            "Wealth management services", "Private wealth advisors",
            "Asset management services", "Investment portfolio management",
            "Wealth planning services", "Private banking services",
            "Financial wealth management", "High net worth advisory",
            "Wealth preservation strategies", "Family office services",
            "Investment management for wealthy", "Premium financial advisory",
            "Wealth accumulation strategies", "Asset protection services"
        ],
        "business_franchise": [
            "Business franchise opportunities", "Franchise business for sale",
            "Top franchise opportunities", "Franchise investment",
            "Best franchises to buy", "Franchise business models",
            "Franchise consulting services", "Franchise startup",
            "Popular franchise opportunities", "Franchise brand opportunities",
            "Franchise business expansion", "Franchise development",
            "Franchise marketing services", "Franchise support services"
        ],
        "private_banking": [
            "Private banking services", "VIP banking services",
            "Exclusive banking services", "Premium banking solutions",
            "Private wealth management", "High net worth banking",
            "Luxury banking services", "Personalized banking",
            "Private client services", "Exclusive financial services",
            "Premium investment services", "VIP financial planning",
            "Private banking accounts", "High-end banking solutions"
        ],
        "insurance_annuities": [
            "Annuity insurance products", "Retirement annuities",
            "Fixed annuity plans", "Variable annuities",
            "Indexed annuities", "Annuity retirement planning",
            "Annuity investment options", "Annuity quotes",
            "Best annuity providers", "Annuity income strategies",
            "Annuity vs 401k", "Annuity benefits",
            "Annuity for retirement", "Annuity payout options"
        ],
        "ecommerce_luxury": [
            "Luxury goods online", "Premium designer brands",
            "Luxury fashion online", "High-end luxury products",
            "Exclusive luxury items", "Luxury jewelry online",
            "Premium watches online", "Designer handbags online",
            "Luxury accessories", "Exclusive luxury collections",
            "VIP luxury shopping", "Premium luxury brands",
            "Luxury home goods", "High-end luxury gifts"
        ],
        "travel_luxury": [
            "Luxury travel destinations", "Premium travel experiences",
            "Luxury vacation packages", "VIP travel services",
            "Exclusive travel deals", "Luxury cruise vacations",
            "Premium hotel bookings", "Luxury resort vacations",
            "VIP travel planning", "Exclusive travel experiences",
            "Luxury business travel", "Premium travel concierge",
            "Luxury adventure travel", "High-end travel packages"
        ],
        "hedge_funds": [
            "Hedge fund investments", "Alternative investments",
            "Private equity funds", "Hedge fund strategies",
            "Investment hedge funds", "Hedge fund managers",
            "Institutional investments", "Private investment funds",
            "Hedge fund performance", "Alternative asset management",
            "Fund of funds", "Private wealth investing",
            "Hedge fund research", "Alternative investment strategies"
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
        # 新增高价值广告类别
        {"id": "healthcare_medical", "name": "Healthcare Services", "category": "Healthcare"},
        {"id": "automotive_luxury", "name": "Luxury Cars", "category": "Automotive"},
        {"id": "real_estate_luxury", "name": "Luxury Real Estate", "category": "Real Estate"},
        {"id": "finance_wealth_management", "name": "Wealth Management", "category": "Finance"},
        {"id": "business_franchise", "name": "Business Franchise", "category": "Business"},
        {"id": "finance_private_banking", "name": "Private Banking", "category": "Finance"},
        {"id": "insurance_annuities", "name": "Annuities", "category": "Finance"},
        {"id": "ecommerce_luxury", "name": "Luxury Goods", "category": "Retail"},
        {"id": "travel_luxury", "name": "Luxury Travel", "category": "Travel"},
        {"id": "finance_hedge_funds", "name": "Hedge Funds", "category": "Finance"},
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
            5.0,  # saas_enterprise (highest value)
            4.5,  # finance_mortgage
            4.0,  # finance_investing_stocks
            3.8,  # finance_insurance_health (high value)
            3.5,  # finance_insurance_life
            3.2,  # finance_crypto_trading
            2.8,  # finance_personal_loans
            2.5,  # finance_credit_cards_premium
            2.5,  # b2b_software
            3.0,  # legal_services (high value)
            2.8,  # real_estate_investing
            2.0,  # finance_debt_consolidation
            1.5,  # software_subscription
            1.2,  # ecommerce_high_ticket
            1.0,  # education_professional
            # 新增高价值类别权重
            4.2,  # healthcare_medical
            4.8,  # automotive_luxury
            4.5,  # real_estate_luxury
            4.0,  # finance_wealth_management
            3.5,  # business_franchise
            4.5,  # finance_private_banking
            3.8,  # insurance_annuities
            3.5,  # ecommerce_luxury
            3.2,  # travel_luxury
            4.0,  # finance_hedge_funds
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
            # 新增类别映射
            "healthcare_medical": "healthcare_medical",
            "automotive_luxury": "automotive_luxury",
            "real_estate_luxury": "real_estate_luxury",
            "finance_wealth_management": "wealth_management",
            "business_franchise": "business_franchise",
            "finance_private_banking": "private_banking",
            "insurance_annuities": "insurance_annuities",
            "ecommerce_luxury": "ecommerce_luxury",
            "travel_luxury": "travel_luxury",
            "finance_hedge_funds": "hedge_funds",
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
            # 金融类
            "https://www.financeadvice.com",
            "https://www.investmentguide.com",
            "https://www.creditcardreviews.com",
            "https://www.insurancecompare.com",
            "https://www.personalloansguide.com",
            "https://www.mortgagetips.com",
            "https://www.debtreliefhelp.com",
            "https://www.retirementplanning.org",
            # 新增高价值域名
            "https://www.privatebanking.com",
            "https://www.wealthmanagementadvisor.com",
            "https://www.hedgefundinvesting.com",
            "https://www.luxurycarreviews.com",
            "https://www.highendcars.com",
            "https://www.luxuryrealestate.com",
            "https://www.premiumproperties.com",
            "https://www.healthcareguide.com",
            "https://www.medicalservices.com",
            "https://www.franchiseopportunities.com",
            "https://www.businessfranchise.com",
            "https://www.annuityguide.com",
            "https://www.luxurygoods.com",
            "https://www.premiumfashion.com",
            "https://www.luxurytravel.com",
            "https://www.exclusivetravel.com",
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
            "healthcare_medical": [
                "Comprehensive healthcare services and medical treatment options.",
                "Best medical clinics and healthcare providers for every need.",
                "Premium healthcare services and medical specialist consultations.",
                "Healthcare management and medical service comparisons.",
            ],
            "automotive_luxury": [
                "Luxury car brands and premium automobile reviews.",
                "Best luxury vehicles and high-end car models.",
                "Exclusive luxury car dealerships and leasing options.",
                "High-performance cars and luxury automotive accessories.",
            ],
            "real_estate_luxury": [
                "Luxury real estate properties and exclusive homes for sale.",
                "Premium properties and luxury residential listings.",
                "Luxury villas and high-end real estate investments.",
                "Exclusive property viewings and luxury real estate services.",
            ],
            "finance_wealth_management": [
                "Wealth management services for high net worth individuals.",
                "Professional asset management and investment portfolio strategies.",
                "Private wealth advisors and financial planning services.",
                "Wealth preservation and accumulation strategies.",
            ],
            "business_franchise": [
                "Top business franchise opportunities and investment options.",
                "Best franchises to buy and franchise business models.",
                "Franchise consulting services and startup support.",
                "Popular franchise opportunities and brand expansion.",
            ],
            "finance_private_banking": [
                "Private banking services and exclusive financial solutions.",
                "VIP banking services for high net worth clients.",
                "Premium banking solutions and personalized financial services.",
                "Exclusive investment services and private client banking.",
            ],
            "insurance_annuities": [
                "Annuity insurance products and retirement planning.",
                "Best annuity providers and payout options.",
                "Fixed and variable annuities for secure retirement income.",
                "Annuity investment strategies and retirement benefits.",
            ],
            "ecommerce_luxury": [
                "Luxury goods and premium designer brands online.",
                "Exclusive luxury items and high-end fashion products.",
                "VIP luxury shopping experience and premium collections.",
                "Luxury jewelry, watches, and designer accessories.",
            ],
            "travel_luxury": [
                "Luxury travel destinations and premium vacation packages.",
                "VIP travel services and exclusive travel experiences.",
                "Luxury cruises and premium hotel bookings.",
                "High-end travel planning and luxury resort vacations.",
            ],
            "finance_hedge_funds": [
                "Hedge fund investments and alternative investment strategies.",
                "Private equity funds and institutional investment options.",
                "Professional hedge fund managers and fund performance.",
                "Alternative asset management and private wealth investing.",
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
            # 新增类别标签
            "healthcare_medical": ["healthcare", "medical", "health", "doctor", "hospital", "treatment", "services", "clinic"],
            "automotive_luxury": ["luxury", "cars", "automobile", "premium", "high-end", "vehicles", "sports cars", "exclusive"],
            "real_estate_luxury": ["luxury", "real estate", "property", "premium", "exclusive", "villa", "penthouse", "homes"],
            "finance_wealth_management": ["wealth", "management", "investment", "finance", "asset", "portfolio", "private", "high net worth"],
            "business_franchise": ["franchise", "business", "opportunity", "investment", "startup", "brand", "expansion", "consulting"],
            "finance_private_banking": ["private", "banking", "finance", "exclusive", "VIP", "premium", "wealth", "investment"],
            "insurance_annuities": ["annuity", "insurance", "retirement", "investment", "payout", "income", "financial", "planning"],
            "ecommerce_luxury": ["luxury", "fashion", "designer", "premium", "jewelry", "watches", "exclusive", "shopping"],
            "travel_luxury": ["luxury", "travel", "vacation", "premium", "exclusive", "cruise", "resort", "VIP"],
            "finance_hedge_funds": ["hedge funds", "investment", "private equity", "alternative", "fund", "portfolio", "institutional", "wealth"],
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
        
        # 真实用户分布 - 不是所有都是高质量
        is_returning_visitor = random.random() < 0.55
        
        # 可查看性分数 - 符合真实分布
        viewability_score = random.choices(
            [round(random.uniform(0.4, 0.6), 2), round(random.uniform(0.6, 0.8), 2), round(random.uniform(0.8, 1.0), 2)],
            weights=[3, 5, 2],
            k=1
        )[0]
        
        # 内容质量 - 不是所有都是最高
        content_quality = random.choices(
            [round(random.uniform(0.4, 0.6), 2), round(random.uniform(0.6, 0.8), 2), round(random.uniform(0.8, 1.0), 2)],
            weights=[2, 5, 3],
            k=1
        )[0]
        
        # 域名权重 - 有些是新站
        domain_authority = random.choices(
            [random.randint(30, 50), random.randint(50, 70), random.randint(70, 100)],
            weights=[3, 5, 2],
            k=1
        )[0]
        
        # 流量质量 - 有好有差
        traffic_quality = random.choices(
            [round(random.uniform(0.4, 0.6), 2), round(random.uniform(0.6, 0.8), 2), round(random.uniform(0.8, 1.0), 2)],
            weights=[2, 6, 2],
            k=1
        )[0]
        
        # 用户参与度 - 符合真实分布
        engagement_score = random.choices(
            [round(random.uniform(0.3, 0.5), 2), round(random.uniform(0.5, 0.75), 2), round(random.uniform(0.75, 1.0), 2)],
            weights=[3, 5, 2],
            k=1
        )[0]
        
        # 跳出率 - 真实数据
        bounce_rate = random.choices(
            [round(random.uniform(0.6, 0.85), 2), round(random.uniform(0.4, 0.6), 2), round(random.uniform(0.15, 0.4), 2)],
            weights=[2, 5, 3],
            k=1
        )[0]
        
        # 设备可信度 - 不是100%
        device_trust = random.choices(
            [round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 0.85), 2), round(random.uniform(0.85, 1.0), 2)],
            weights=[2, 5, 3],
            k=1
        )[0]
        
        # 权威分数
        authority_score = random.choices(
            [round(random.uniform(0.3, 0.5), 2), round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 1.0), 2)],
            weights=[3, 5, 2],
            k=1
        )[0]
        
        # 核心Web指标
        core_web_vitals = random.choices(
            [round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 0.9), 2), round(random.uniform(0.9, 1.0), 2)],
            weights=[2, 6, 2],
            k=1
        )[0]
        
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
            "userInterests": ",".join(random.sample(user_interests, random.randint(3, 6))),
            # 真实分布的内容质量指标
            "contentLength": random.choices(
                [random.randint(500, 1500), random.randint(1500, 3000), random.randint(3000, 8000)],
                weights=[2, 5, 3],
                k=1
            )[0],
            "contentQuality": content_quality,
            "pageRank": random.choices(
                [random.randint(1, 4), random.randint(5, 7), random.randint(8, 10)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "domainAuthority": domain_authority,
            "trafficQualityScore": traffic_quality,
            "userEngagementScore": engagement_score,
            "pageViews": random.choices(
                [random.randint(1000, 10000), random.randint(10000, 100000), random.randint(100000, 1000000)],
                weights=[2, 6, 2],
                k=1
            )[0],
            "avgTimeOnPage": random.choices(
                [random.randint(10, 30), random.randint(30, 90), random.randint(90, 300)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "avgSessionDuration": random.choices(
                [random.randint(30, 120), random.randint(120, 360), random.randint(360, 900)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "bounceRate": bounce_rate,
            "mobileOptimized": random.random() < 0.95,
            "sslEnabled": random.random() < 0.98,
            "pageAge": random.choices(
                [random.randint(30, 180), random.randint(180, 365), random.randint(365, 2000)],
                weights=[3, 4, 3],
                k=1
            )[0],
            "trafficSource": traffic_source,
            "sessionDepth": session_depth,
            "isReturningVisitor": is_returning_visitor,
            "viewabilityScore": viewability_score,
            "scrollDepth": random.choices(
                [random.randint(20, 50), random.randint(50, 75), random.randint(75, 100)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "pagesPerSession": round(random.choices(
                [round(random.uniform(1.0, 2.5), 1), round(random.uniform(2.5, 4.0), 1), round(random.uniform(4.0, 8.0), 1)],
                weights=[3, 5, 2],
                k=1
            )[0], 1),
            "userIntent": random.choices(
                ["informational", "commercial", "navigational", "transactional"],
                weights=[3.0, 4.5, 1.5, 0.5],
                k=1
            )[0],
            "userAgeRange": random.choices(
                ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
                weights=[1.5, 3.0, 3.5, 2.0, 1.0, 0.5],
                k=1
            )[0],
            "userIncomeLevel": random.choices(
                ["low", "medium", "high", "premium"],
                weights=[1.5, 3.5, 3.5, 1.5],
                k=1
            )[0],
            "deviceTrustScore": device_trust,
            # 会话追踪参数 - 更真实
            "adRequestCount": self.requests_count + 1,
            "visitorLifetime": random.choices(
                [random.randint(1, 30), random.randint(30, 180), random.randint(180, 730)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "totalSessions": random.choices(
                [random.randint(1, 5), random.randint(5, 20), random.randint(20, 100)],
                weights=[4, 4, 2],
                k=1
            )[0],
            "avgClicksPerSession": round(random.choices(
                [round(random.uniform(0.1, 0.5), 1), round(random.uniform(0.5, 1.5), 1), round(random.uniform(1.5, 4.0), 1)],
                weights=[4, 4, 2],
                k=1
            )[0], 1),
            "conversionRate": round(random.choices(
                [round(random.uniform(0.001, 0.01), 4), round(random.uniform(0.01, 0.05), 4), round(random.uniform(0.05, 0.15), 4)],
                weights=[4, 4, 2],
                k=1
            )[0], 4),
            "trafficDiversityScore": round(random.choices(
                [round(random.uniform(0.3, 0.5), 2), round(random.uniform(0.5, 0.75), 2), round(random.uniform(0.75, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "contentRelevanceScore": round(random.choices(
                [round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 0.9), 2), round(random.uniform(0.9, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "userTrustScore": round(random.choices(
                [round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 0.9), 2), round(random.uniform(0.9, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "brandSafetyScore": round(random.choices(
                [round(random.uniform(0.6, 0.8), 2), round(random.uniform(0.8, 0.95), 2), round(random.uniform(0.95, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "engagementRate": round(random.choices(
                [round(random.uniform(0.01, 0.05), 4), round(random.uniform(0.05, 0.15), 4), round(random.uniform(0.15, 0.35), 4)],
                weights=[4, 4, 2],
                k=1
            )[0], 4),
            "socialShareCount": random.choices(
                [random.randint(0, 50), random.randint(50, 500), random.randint(500, 10000)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "commentCount": random.choices(
                [random.randint(0, 20), random.randint(20, 150), random.randint(150, 1000)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "backlinkCount": random.choices(
                [random.randint(5, 50), random.randint(50, 200), random.randint(200, 5000)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "organicTrafficPercent": round(random.choices(
                [round(random.uniform(0.2, 0.5), 2), round(random.uniform(0.5, 0.75), 2), round(random.uniform(0.75, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "isBotTraffic": False,
            "trafficGeoDiversity": round(random.choices(
                [round(random.uniform(0.3, 0.5), 2), round(random.uniform(0.5, 0.75), 2), round(random.uniform(0.75, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            # 页面性能指标 - 更真实
            "pageLoadTime": round(random.choices(
                [round(random.uniform(2.0, 5.0), 2), round(random.uniform(1.0, 2.0), 2), round(random.uniform(0.3, 1.0), 2)],
                weights=[2, 5, 3],
                k=1
            )[0], 2),
            "firstContentfulPaint": round(random.choices(
                [round(random.uniform(2.0, 4.0), 2), round(random.uniform(1.0, 2.0), 2), round(random.uniform(0.3, 1.0), 2)],
                weights=[2, 5, 3],
                k=1
            )[0], 2),
            "cumulativeLayoutShift": round(random.choices(
                [round(random.uniform(0.1, 0.3), 2), round(random.uniform(0.05, 0.1), 2), round(random.uniform(0.0, 0.05), 2)],
                weights=[2, 5, 3],
                k=1
            )[0], 2),
            "coreWebVitalsScore": core_web_vitals,
            # 内容新鲜度
            "contentFreshness": random.choices(
                [random.randint(30, 180), random.randint(7, 30), random.randint(1, 7)],
                weights=[2, 5, 3],
                k=1
            )[0],
            "authorityScore": authority_score,
            "topicRelevance": round(random.choices(
                [round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 0.9), 2), round(random.uniform(0.9, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "seasonalityFactor": round(random.uniform(0.7, 1.3), 2),
            # 新增真实用户行为信号
            "timeOnPage": random.choices(
                [random.randint(5, 30), random.randint(30, 120), random.randint(120, 600)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "interactionDepth": random.choices(
                [round(random.uniform(0.1, 0.3), 2), round(random.uniform(0.3, 0.6), 2), round(random.uniform(0.6, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "hasInteracted": random.random() < 0.7,
            "interactionTypes": random.sample(["scroll", "click", "hover", "form", "video"], random.randint(1, 3)),
            "viewportStability": round(random.choices(
                [round(random.uniform(0.5, 0.7), 2), round(random.uniform(0.7, 0.9), 2), round(random.uniform(0.9, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0], 2),
            "adViewDuration": round(random.uniform(1.0, 15.0), 1),
            "inViewPercentage": random.choices(
                [round(random.uniform(0.3, 0.5), 2), round(random.uniform(0.5, 0.8), 2), round(random.uniform(0.8, 1.0), 2)],
                weights=[3, 5, 2],
                k=1
            )[0],
            "viewportPosition": random.choices(
                ["above_fold", "below_fold", "footer"],
                weights=[5, 3, 2],
                k=1
            )[0],
            "tabFocusTime": round(random.uniform(1.0, 30.0), 1),
            "userActivity": random.choices(
                ["active", "idle", "background"],
                weights=[6, 3, 1],
                k=1
            )[0],
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
        
        # 计算真实的展示参数
        view_duration_ms = round(view_duration * 1000)

        # 可见性百分比 - 确保大部分展示是可见的（>70%）
        in_view_pct = round(random.uniform(0.7, 1.0), 2) if view_duration > 0 else round(random.uniform(0.6, 0.9), 2)

        # 视口位置 - 大部分广告在首屏或上半部分
        viewport_pos = random.choices(
            ["above_fold", "upper_mid", "lower_mid", "below_fold"],
            weights=[5, 3, 1.5, 0.5],
            k=1
        )[0]

        # 用户是否在看 - 提高到95%
        user_active = random.random() < 0.95

        # 可查看性分数 - 确保高于0.7
        viewability = round(min(max(view_duration / 5.0, 0.7), 1.0), 2)

        # 视口稳定性
        viewport_stable = round(random.uniform(0.8, 1.0), 2)

        # 首次可见时间 - 越快越好
        first_visible_time = round(random.uniform(0.1, 1.5), 2)

        # 用户与广告的距离 - 大部分为0（广告在视口内）
        ad_distance = random.choices(
            [0, round(random.uniform(0, 20), 1), round(random.uniform(20, 50), 1)],
            weights=[7, 2, 1],
            k=1
        )[0]
        
        payload = {
            "token": token,
            "visitorId": self.visitor_id,
            "viewDuration": view_duration_ms,
            "adInView": in_view_pct > 0.5,
            "inViewPercentage": in_view_pct,
            "viewportPosition": viewport_pos,
            "userIsViewing": user_active,
            "viewabilityScore": viewability,
            "viewportStability": viewport_stable,
            "firstVisibleTime": round(first_visible_time * 1000),
            "adDistanceFromViewport": ad_distance,
            "viewportScrollDepth": round(random.uniform(20, 90), 1),
            "tabActive": random.random() < 0.97,
            "windowFocused": random.random() < 0.95,
            "userInteraction": random.choices(
                ["none", "scroll", "hover", "click"],
                weights=[2, 5, 2, 1],
                k=1
            )[0],
            "interactionCount": random.randint(1, 15),
            "scrollEvents": random.randint(1, 8),
            "mouseMovements": random.randint(0, 25),
            "touchEvents": random.randint(1, 10),
            "pageRefreshed": False,
            "adBlockEnabled": False,
            "javascriptEnabled": True,
            "cookiesEnabled": True,
            "localStorageEnabled": True,
            "sessionStorageEnabled": True,
            "hasWebGL": True,
            "hasCanvas": True,
            "hasAudioContext": True,
            "pixelRatio": round(random.choice([2, 3]), 1),
            "colorDepth": random.choice([24, 32]),
            "screenOrientation": random.choice(["portrait", "landscape"]),
            "touchSupport": True,
            "maxTouchPoints": random.choice([5, 10]),
            "devicePixelRatio": round(random.choice([2.0, 3.0]), 1),
        }
        
        # 添加设备信息
        dev = self.device_info
        if dev:
            hw = getattr(dev, "hardware", None)
            if hw and hasattr(hw, "screen_width") and hasattr(hw, "screen_height"):
                payload["containerWidth"] = hw.screen_width
                payload["containerHeight"] = hw.screen_height
            if hw and hasattr(hw, "device_pixel_ratio"):
                payload["devicePixelRatio"] = hw.device_pixel_ratio
        
        # 添加会话追踪
        if self.last_ad:
            ad_data = self.last_ad.get("ad", {})
            payload["adId"] = ad_data.get("id", "")
            payload["adType"] = ad_data.get("type", "banner")
            payload["adFormat"] = ad_data.get("format", "banner")
            payload["adCategory"] = ad_data.get("category", "")
            payload["creativeId"] = ad_data.get("creativeId", "")
            payload["campaignId"] = ad_data.get("campaignId", "")
        
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
