# stealthmaster/constants.py
"""Global constants for StealthMaster."""

from enum import Enum, auto


class BrowserState(str, Enum):
    """Browser lifecycle states."""
    IDLE = "idle"
    STARTING = "starting"
    READY = "ready"
    NAVIGATING = "navigating"
    MONITORING = "monitoring"
    STRIKING = "striking"
    BLOCKED = "blocked"
    ERROR = "error"
    CLOSING = "closing"
    CLOSED = "closed"


class DetectionType(str, Enum):
    """Types of bot detection encountered."""
    NONE = "none"
    CAPTCHA = "captcha"
    CLOUDFLARE = "cloudflare"
    RECAPTCHA = "recaptcha"
    HCAPTCHA = "hcaptcha"
    DISTIL = "distil"
    PERIMETER_X = "perimeter_x"
    SHAPE_SECURITY = "shape_security"
    DATADOME = "datadome"
    QUEUE_IT = "queue_it"
    BROWSER_CHECK = "browser_check"
    RATE_LIMIT = "rate_limit"
    IP_BLOCK = "ip_block"
    FINGERPRINT = "fingerprint"
    BEHAVIOR_ANOMALY = "behavior_anomaly"
    UNKNOWN = "unknown"


class PurchaseStatus(str, Enum):
    """Ticket purchase status."""
    SEARCHING = "searching"
    FOUND = "found"
    SELECTING = "selecting"
    IN_CART = "in_cart"
    CHECKOUT = "checkout"
    PAYMENT = "payment"
    CONFIRMING = "confirming"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    OUT_OF_STOCK = "out_of_stock"


class ProfileStatus(str, Enum):
    """Profile health status."""
    FRESH = "fresh"
    ACTIVE = "active"
    WARMING = "warming"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"
    COOLDOWN = "cooldown"
    RETIRED = "retired"


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NetworkStatus(str, Enum):
    """Network connection status."""
    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


# Timing constants (in milliseconds)
class TimingConstants:
    """Timing-related constants."""
    MIN_HUMAN_REACTION = 150  # Minimum human reaction time
    MAX_HUMAN_REACTION = 400  # Maximum human reaction time
    MIN_TYPING_DELAY = 50  # Minimum delay between keystrokes
    MAX_TYPING_DELAY = 200  # Maximum delay between keystrokes
    MIN_MOUSE_MOVE = 5  # Minimum mouse movement duration
    MAX_MOUSE_MOVE = 50  # Maximum mouse movement duration
    PAGE_LOAD_TIMEOUT = 30000  # Page load timeout
    ELEMENT_WAIT_TIMEOUT = 10000  # Element wait timeout
    NETWORK_IDLE_TIMEOUT = 5000  # Network idle timeout


# Detection patterns
DETECTION_PATTERNS = {
    "cloudflare": [
        "Checking your browser",
        "Please wait",
        "DDoS protection by Cloudflare",
        "cf-browser-verification",
    ],
    "recaptcha": [
        "g-recaptcha",
        "grecaptcha",
        "recaptcha/api",
        "I'm not a robot",
    ],
    "hcaptcha": [
        "h-captcha",
        "hcaptcha.com",
        "hcaptcha-response",
    ],
    "queue_it": [
        "queue-it",
        "queueit",
        "You are now in line",
        "waiting room",
    ],
    "rate_limit": [
        "rate limit",
        "too many requests",
        "429",
        "slow down",
    ],
}


# Platform-specific selectors
PLATFORM_SELECTORS = {
    "fansale": {
        "login_email": 'input[name="email"]',
        "login_password": 'input[name="password"]',
        "login_button": 'button[type="submit"]',
        "ticket_card": ".ticket-card",
        "buy_button": ".buy-button",
        "cart_button": ".cart-button",
    },
    "ticketmaster": {
        "login_email": "#email",
        "login_password": "#password",
        "login_button": "#sign-in",
        "ticket_section": ".event-offer",
        "buy_button": ".buy-button",
        "checkout_button": "#checkout-button",
    },
    "vivaticket": {
        "login_email": 'input[type="email"]',
        "login_password": 'input[type="password"]',
        "login_button": ".login-submit",
        "ticket_row": ".ticket-row",
        "add_to_cart": ".add-to-cart",
        "proceed_button": ".proceed-checkout",
    },
}


# HTTP headers for stealth
STEALTH_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


# User agent strings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


# ADDED: Common selectors for various UI elements
COMMON_SELECTORS = {
    "accept_cookies": [
        'button:has-text("Accept all")',
        'button:has-text("Accept All")',
        'button:has-text("Accetta tutti")',
        'button:has-text("Accetta")',
        '#onetrust-accept-btn-handler',
        '.cookie-consent-accept',
        '[data-testid="cookie-accept"]',
        'button[id*="accept"][id*="cookie"]',
        'button[class*="accept"][class*="cookie"]'
    ]
}