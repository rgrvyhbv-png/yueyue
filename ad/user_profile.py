import random
from dataclasses import dataclass
from typing import Dict, Optional

INCOME_LEVELS = ["low", "medium", "high"]
CREDIT_SCORES = ["bad", "fair", "good", "excellent"]
INVESTMENT_PREFERENCES = ["conservative", "moderate", "aggressive"]
INSURANCE_NEEDS = ["none", "basic", "comprehensive"]
DEBT_STATUS = ["none", "low", "high"]

@dataclass
class UserProfile:
    income_level: str
    credit_score: str
    investment_preference: str
    insurance_need: str
    debt_status: str
    age_group: str
    occupation: str

    def __repr__(self):
        return (f"UserProfile(income={self.income_level}, "
                f"credit={self.credit_score}, "
                f"investment={self.investment_preference}, "
                f"insurance={self.insurance_need}, "
                f"debt={self.debt_status})")

INCOME_RANGES = {
    "low": {"min": 0, "max": 30000, "label": "Low Income"},
    "medium": {"min": 30000, "max": 80000, "label": "Medium Income"},
    "high": {"min": 80000, "max": 500000, "label": "High Income"}
}

CREDIT_RANGES = {
    "bad": {"min": 300, "max": 579, "label": "Poor"},
    "fair": {"min": 580, "max": 669, "label": "Fair"},
    "good": {"min": 670, "max": 739, "label": "Good"},
    "excellent": {"min": 740, "max": 850, "label": "Excellent"}
}

OCCUPATIONS_BY_INCOME = {
    "low": ["Retail Worker", "Restaurant Server", "Cleaner", "Delivery Driver", "Part-time Worker"],
    "medium": ["Teacher", "Nurse", "Administrator", "Engineer", "Designer", "Sales Representative"],
    "high": ["Doctor", "Lawyer", "Business Executive", "Entrepreneur", "Financial Analyst", "Software Developer"]
}

AGE_GROUPS = {
    "young": {"range": (18, 30), "label": "Young Adult"},
    "middle": {"range": (31, 50), "label": "Middle Age"},
    "senior": {"range": (51, 70), "label": "Senior"}
}

def generate_user_profile() -> UserProfile:
    income_level = random.choices(
        INCOME_LEVELS,
        weights=[0.35, 0.45, 0.20]
    )[0]

    credit_weights = {
        "low": [0.40, 0.35, 0.20, 0.05],
        "medium": [0.15, 0.30, 0.40, 0.15],
        "high": [0.05, 0.10, 0.30, 0.55]
    }
    credit_score = random.choices(
        CREDIT_SCORES,
        weights=credit_weights[income_level]
    )[0]

    investment_weights = {
        "low": [0.60, 0.30, 0.10],
        "medium": [0.25, 0.50, 0.25],
        "high": [0.10, 0.30, 0.60]
    }
    investment_preference = random.choices(
        INVESTMENT_PREFERENCES,
        weights=investment_weights[income_level]
    )[0]

    insurance_weights = {
        "low": [0.40, 0.45, 0.15],
        "medium": [0.20, 0.50, 0.30],
        "high": [0.05, 0.30, 0.65]
    }
    insurance_need = random.choices(
        INSURANCE_NEEDS,
        weights=insurance_weights[income_level]
    )[0]

    debt_weights = {
        "low": [0.50, 0.35, 0.15],
        "medium": [0.25, 0.45, 0.30],
        "high": [0.30, 0.40, 0.30]
    }
    debt_status = random.choices(
        DEBT_STATUS,
        weights=debt_weights[income_level]
    )[0]

    age_group = random.choices(
        list(AGE_GROUPS.keys()),
        weights=[0.30, 0.50, 0.20]
    )[0]

    occupation = random.choice(OCCUPATIONS_BY_INCOME[income_level])

    return UserProfile(
        income_level=income_level,
        credit_score=credit_score,
        investment_preference=investment_preference,
        insurance_need=insurance_need,
        debt_status=debt_status,
        age_group=age_group,
        occupation=occupation
    )

AD_CATEGORY_PRIORITIES = {
    "personal_loans": {
        "income_level": {"low": 0.30, "medium": 0.45, "high": 0.25},
        "credit_score": {"bad": 0.40, "fair": 0.35, "good": 0.15, "excellent": 0.10},
        "debt_status": {"none": 0.20, "low": 0.35, "high": 0.45}
    },
    "credit_cards": {
        "income_level": {"low": 0.20, "medium": 0.45, "high": 0.35},
        "credit_score": {"bad": 0.10, "fair": 0.30, "good": 0.40, "excellent": 0.20},
        "debt_status": {"none": 0.30, "low": 0.40, "high": 0.30}
    },
    "investing": {
        "income_level": {"low": 0.10, "medium": 0.35, "high": 0.55},
        "credit_score": {"bad": 0.10, "fair": 0.20, "good": 0.40, "excellent": 0.30},
        "investment_preference": {"conservative": 0.20, "moderate": 0.40, "aggressive": 0.40}
    },
    "insurance": {
        "income_level": {"low": 0.25, "medium": 0.40, "high": 0.35},
        "credit_score": {"bad": 0.20, "fair": 0.30, "good": 0.30, "excellent": 0.20},
        "insurance_need": {"none": 0.10, "basic": 0.40, "comprehensive": 0.50}
    },
    "debt_consolidation": {
        "income_level": {"low": 0.35, "medium": 0.40, "high": 0.25},
        "credit_score": {"bad": 0.25, "fair": 0.35, "good": 0.25, "excellent": 0.15},
        "debt_status": {"none": 0.05, "low": 0.35, "high": 0.60}
    },
    "mortgage": {
        "income_level": {"low": 0.15, "medium": 0.45, "high": 0.40},
        "credit_score": {"bad": 0.05, "fair": 0.20, "good": 0.45, "excellent": 0.30},
        "debt_status": {"none": 0.40, "low": 0.35, "high": 0.25}
    }
}

def calculate_ad_category_probability(profile: UserProfile, category: str) -> float:
    if category not in AD_CATEGORY_PRIORITIES:
        return 0.1667

    weights = AD_CATEGORY_PRIORITIES[category]
    probability = 1.0

    for attr, attr_weights in weights.items():
        if hasattr(profile, attr):
            value = getattr(profile, attr)
            if value in attr_weights:
                probability *= attr_weights[value]
            else:
                probability *= 0.5

    return probability

def select_ad_category(profile: UserProfile) -> str:
    categories = list(AD_CATEGORY_PRIORITIES.keys())
    probabilities = [calculate_ad_category_probability(profile, cat) for cat in categories]

    total = sum(probabilities)
    if total == 0:
        return random.choice(categories)

    normalized_probs = [p / total for p in probabilities]
    return random.choices(categories, weights=normalized_probs)[0]

CLICK_MOTIVATIONS_BY_PROFILE = {
    "personal_loans": {
        "low_income": [
            "User needs emergency funds",
            "User has bad credit, looking for small loans",
            "User has unstable income, needs flexible repayment",
            "User wants to start business but has no collateral"
        ],
        "medium_income": [
            "User wants to renovate home",
            "User plans to travel and needs funds",
            "User wants to buy large items",
            "User needs to pay off high-interest credit cards"
        ],
        "high_income": [
            "User needs short-term liquidity",
            "User wants to invest in new projects",
            "User is evaluating loan interest rates",
            "User plans to consolidate debt"
        ],
        "bad_credit": [
            "User has low credit score, rejected by banks",
            "User needs money urgently but banks won't approve",
            "User is looking for no-credit-check loans"
        ],
        "high_debt": [
            "User has heavy debt burden, wants to restructure",
            "User has multiple credit cards to consolidate",
            "User is looking for debt solutions"
        ]
    },
    "credit_cards": {
        "low_income": [
            "User wants to build credit history",
            "User needs emergency credit line",
            "User wants interest-free period benefits"
        ],
        "medium_income": [
            "User wants rewards points and cashback",
            "User travels frequently and needs travel benefits",
            "User wants to increase credit limit"
        ],
        "high_income": [
            "User wants premium card exclusive benefits",
            "User needs business travel services",
            "User values VIP services and airport lounges"
        ],
        "good_credit": [
            "User has good credit, wants high-limit card",
            "User wants to enjoy premium credit card benefits"
        ]
    },
    "investing": {
        "low_income": [
            "User wants to start investing and build wealth",
            "User heard market is good and wants to try",
            "User looking for low-threshold investment channels"
        ],
        "medium_income": [
            "User wants to increase passive income",
            "User is planning retirement savings",
            "User wants to invest in real estate funds"
        ],
        "high_income": [
            "User wants to expand investment portfolio",
            "User looking for professional investment advisor",
            "User wants to invest in private equity",
            "User plans asset allocation optimization"
        ],
        "conservative": [
            "User prefers low-risk investments",
            "User values principal safety"
        ],
        "aggressive": [
            "User pursues high-yield investments",
            "User willing to take higher risks"
        ]
    },
    "insurance": {
        "low_income": [
            "User needs basic coverage",
            "User looking for affordable insurance plans",
            "User just started working, needs health insurance"
        ],
        "medium_income": [
            "User wants to buy insurance for family",
            "User plans to buy car insurance",
            "User is evaluating life insurance plans"
        ],
        "high_income": [
            "User needs comprehensive wealth protection",
            "User wants to buy premium health insurance",
            "User plans estate planning"
        ],
        "comprehensive": [
            "User values comprehensive coverage",
            "User is comparing multiple insurance companies"
        ]
    },
    "debt_consolidation": {
        "low_income": [
            "User has multiple high-interest debts",
            "User wants to reduce monthly payments",
            "User has heavy debt burden and needs help"
        ],
        "medium_income": [
            "User wants to consolidate credit card debt",
            "User plans to lower interest rates",
            "User wants to simplify repayment process"
        ],
        "high_income": [
            "User has business debt that needs restructuring",
            "User wants to optimize debt structure",
            "User plans debt refinancing"
        ],
        "high_debt": [
            "User has too much debt to consolidate",
            "User wants to get rid of high-interest debt"
        ]
    },
    "mortgage": {
        "low_income": [
            "User wants to buy first home",
            "User looking for low-down-payment options"
        ],
        "medium_income": [
            "User wants to upgrade to bigger house",
            "User plans to refinance at lower rates",
            "User wants to invest in real estate"
        ],
        "high_income": [
            "User wants to buy luxury property",
            "User plans to invest in real estate",
            "User wants to optimize mortgage"
        ],
        "good_credit": [
            "User has good credit for favorable rates",
            "User preparing to apply for large mortgage"
        ]
    }
}

NO_CLICK_REASONS_BY_PROFILE = {
    "personal_loans": {
        "low_income": [
            "User worried about repayment ability",
            "User doesn't want to increase debt burden",
            "User doesn't trust online loans"
        ],
        "medium_income": [
            "User already has enough funds",
            "User thinks interest rate is too high",
            "User is comparing other options"
        ],
        "high_income": [
            "User doesn't need loans",
            "User has better financing channels",
            "User not interested in ad content"
        ],
        "good_credit": [
            "User has good credit, can borrow directly from bank",
            "User doesn't need high-interest small loans"
        ],
        "no_debt": [
            "User has no debt, doesn't need loans",
            "User prefers cash payments"
        ]
    },
    "credit_cards": {
        "low_income": [
            "User already has enough credit cards",
            "User worried about overspending",
            "User has been rejected multiple times"
        ],
        "medium_income": [
            "User satisfied with current credit cards",
            "User doesn't want to increase credit burden",
            "User thinks offers are not attractive enough"
        ],
        "high_income": [
            "User already has premium credit cards",
            "User doesn't need more cards",
            "User not interested in ad benefits"
        ],
        "bad_credit": [
            "User knows credit doesn't meet requirements",
            "User doesn't want to be rejected again"
        ]
    },
    "investing": {
        "low_income": [
            "User has no extra funds to invest",
            "User worried about investment risks",
            "User doesn't understand investments"
        ],
        "medium_income": [
            "User is waiting for better market timing",
            "User prefers stable savings",
            "User doesn't have time to manage investments"
        ],
        "high_income": [
            "User has exclusive investment advisor",
            "User not interested in ad products",
            "User already has well-diversified portfolio"
        ],
        "conservative": [
            "User doesn't like risky investments",
            "User prefers bank wealth management products"
        ]
    },
    "insurance": {
        "low_income": [
            "User thinks insurance is too expensive",
            "User doesn't think they need insurance",
            "User hasn't realized the importance of insurance"
        ],
        "medium_income": [
            "User already has enough insurance",
            "User satisfied with current insurance",
            "User thinks claims process is too complicated"
        ],
        "high_income": [
            "User has exclusive insurance advisor",
            "User not satisfied with ad insurance plans",
            "User already has comprehensive coverage"
        ],
        "none": [
            "User has no insurance needs",
            "User thinks they're too young for insurance"
        ]
    },
    "debt_consolidation": {
        "low_income": [
            "User doesn't understand what debt consolidation is",
            "User worried about high fees",
            "User doesn't trust the service"
        ],
        "medium_income": [
            "User thinks they can manage debt themselves",
            "User satisfied with current debt situation",
            "User worried about credit impact"
        ],
        "high_income": [
            "User can handle it themselves",
            "User doesn't need debt consolidation service",
            "User thinks service isn't worth the cost"
        ],
        "no_debt": [
            "User has no debt to consolidate",
            "User doesn't need this service"
        ]
    },
    "mortgage": {
        "low_income": [
            "User thinks house prices are too high",
            "User thinks they don't meet loan requirements",
            "User has no immediate plans to buy"
        ],
        "medium_income": [
            "User waiting for better timing",
            "User not satisfied with current rates",
            "User still hesitating about buying"
        ],
        "high_income": [
            "User already owns multiple properties",
            "User prefers cash purchases",
            "User not interested in ad listings"
        ],
        "bad_credit": [
            "User knows credit doesn't meet mortgage requirements",
            "User doesn't want to waste time applying"
        ]
    }
}

def get_click_motivation(profile: UserProfile, category: str) -> str:
    motivations = []
    
    if category in CLICK_MOTIVATIONS_BY_PROFILE:
        profile_motivations = CLICK_MOTIVATIONS_BY_PROFILE[category]
        
        if f"{profile.income_level}_income" in profile_motivations:
            motivations.extend(profile_motivations[f"{profile.income_level}_income"])
        
        if profile.credit_score in profile_motivations:
            motivations.extend(profile_motivations[profile.credit_score])
        
        if profile.debt_status in profile_motivations:
            motivations.extend(profile_motivations[profile.debt_status])
        
        if profile.investment_preference in profile_motivations:
            motivations.extend(profile_motivations[profile.investment_preference])
        
        if profile.insurance_need in profile_motivations:
            motivations.extend(profile_motivations[profile.insurance_need])
    
    if not motivations:
        default_motivations = [
            "Ad content is very appealing",
            "User happens to need this product",
            "Great discount offers",
            "High brand recognition",
            "Recommended by friends",
            "Ad copy is very persuasive"
        ]
        motivations = default_motivations
    
    return random.choice(motivations)

def get_no_click_reason(profile: UserProfile, category: str) -> str:
    reasons = []
    
    if category in NO_CLICK_REASONS_BY_PROFILE:
        profile_reasons = NO_CLICK_REASONS_BY_PROFILE[category]
        
        if f"{profile.income_level}_income" in profile_reasons:
            reasons.extend(profile_reasons[f"{profile.income_level}_income"])
        
        if profile.credit_score in profile_reasons:
            reasons.extend(profile_reasons[profile.credit_score])
        
        if profile.debt_status in profile_reasons:
            reasons.extend(profile_reasons[profile.debt_status])
        
        if profile.investment_preference in profile_reasons:
            reasons.extend(profile_reasons[profile.investment_preference])
        
        if profile.insurance_need in profile_reasons:
            reasons.extend(profile_reasons[profile.insurance_need])
    
    if not reasons:
        default_reasons = [
            "User is busy with other things",
            "Not interested in ad content",
            "User already has similar products",
            "User didn't see the ad",
            "User thinks price is too high"
        ]
        reasons = default_reasons
    
    return random.choice(reasons)

LANDING_PAGE_BEHAVIORS_BY_PROFILE = {
    "deep": {
        "high_income": [
            "User carefully reads product terms and conditions",
            "User checks interest rate details and repayment plans",
            "User calculates monthly payments and total interest",
            "User reads customer reviews and recommendations",
            "User checks company credentials and licensing information",
            "User contacts customer service for details",
            "User uses online calculator"
        ],
        "medium_income": [
            "User browses product features and benefits",
            "User checks interest rates and fees",
            "User reads frequently asked questions",
            "User checks application process instructions",
            "User compares different plans"
        ],
        "low_income": [
            "User checks application requirements and required documents",
            "User reads simple instructions",
            "User looks for contact information",
            "User checks for hidden fees"
        ],
        "good_credit": [
            "User checks preferential interest rate details",
            "User evaluates application success rate",
            "User prepares application documents"
        ],
        "bad_credit": [
            "User confirms if low credit score applicants are accepted",
            "User checks for alternative options",
            "User understands application requirements"
        ]
    },
    "medium": {
        "high_income": [
            "User browses main product information",
            "User checks interest rate overview",
            "User understands basic application requirements"
        ],
        "medium_income": [
            "User quickly browses page content",
            "User checks product features",
            "User understands application process"
        ],
        "low_income": [
            "User checks basic information",
            "User understands application requirements",
            "User checks contact information"
        ]
    },
    "light": {
        "all": [
            "User quickly scrolls through",
            "User checks page title",
            "User gets rough understanding of product"
        ]
    }
}

def get_landing_page_behaviors(profile: UserProfile, interaction_depth: str) -> list:
    behaviors = []
    
    if interaction_depth in LANDING_PAGE_BEHAVIORS_BY_PROFILE:
        depth_behaviors = LANDING_PAGE_BEHAVIORS_BY_PROFILE[interaction_depth]
        
        if f"{profile.income_level}_income" in depth_behaviors:
            behaviors.extend(depth_behaviors[f"{profile.income_level}_income"])
        
        elif "all" in depth_behaviors:
            behaviors.extend(depth_behaviors["all"])
        
        if profile.credit_score in depth_behaviors:
            behaviors.extend(depth_behaviors[profile.credit_score])
    
    if not behaviors:
        default_behaviors = {
            "deep": [
                "User carefully reads product details",
                "User checks reviews and feedback",
                "User understands application process"
            ],
            "medium": [
                "User browses product features",
                "User checks main information"
            ],
            "light": [
                "User quickly browses page"
            ]
        }
        behaviors = default_behaviors.get(interaction_depth, ["User browses page"])
    
    num_behaviors = random.randint(1, min(3, len(behaviors)))
    return random.sample(behaviors, num_behaviors)

def calculate_click_probability(profile: UserProfile, category: str) -> float:
    base_prob = 0.02

    income_modifiers = {"low": 1.0, "medium": 1.1, "high": 0.9}
    credit_modifiers = {"bad": 1.2, "fair": 1.0, "good": 0.9, "excellent": 0.8}
    debt_modifiers = {"none": 0.7, "low": 1.0, "high": 1.3}
    
    modifier = (income_modifiers.get(profile.income_level, 1.0) *
                credit_modifiers.get(profile.credit_score, 1.0) *
                debt_modifiers.get(profile.debt_status, 1.0))
    
    if category == "personal_loans" and profile.debt_status == "high":
        modifier *= 1.2
    elif category == "investing" and profile.income_level == "high":
        modifier *= 1.15
    elif category == "mortgage" and profile.credit_score == "good":
        modifier *= 1.1
    
    probability = base_prob * modifier
    return min(0.03, max(0.01, probability))