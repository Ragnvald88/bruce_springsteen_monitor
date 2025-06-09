# stealthmaster/profiles/models.py
"""Profile data models for user and browser profile management."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, EmailStr
import hashlib
import json


class ProfileStatus(str, Enum):
    """Profile status states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"


class ProfileTier(int, Enum):
    """Profile quality tiers based on trust score."""
    PREMIUM = 5      # Highest trust, never blocked
    HIGH = 4         # High trust, rarely blocked
    MEDIUM = 3       # Medium trust, occasional blocks
    STANDARD = 2     # Standard trust, some blocks
    LOW = 1          # Low trust, frequent blocks


class PaymentMethod(BaseModel):
    """Payment method configuration."""
    type: str = Field(..., description="Payment type (card, paypal, etc)")
    provider: Optional[str] = Field(None, description="Payment provider")
    last_four: Optional[str] = Field(None, description="Last 4 digits for display")
    expiry: Optional[str] = Field(None, description="Expiry date MM/YY")
    is_default: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BillingAddress(BaseModel):
    """Billing address information."""
    street_address: str
    city: str
    state_province: str
    postal_code: str
    country: str = Field(default="IT")
    
    @validator('country')
    def validate_country(cls, v):
        """Ensure country code is uppercase."""
        return v.upper()


class UserCredentials(BaseModel):
    """Platform-specific user credentials."""
    platform: str
    username: str
    password: str
    email: Optional[EmailStr] = None
    last_login: Optional[datetime] = None
    session_data: Optional[Dict[str, Any]] = None
    cookies: Optional[List[Dict[str, Any]]] = None
    
    def get_password_hash(self) -> str:
        """Get hashed version of password for storage."""
        return hashlib.sha256(self.password.encode()).hexdigest()


class BrowserFingerprint(BaseModel):
    """Browser fingerprint configuration."""
    fingerprint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_agent: str
    viewport: Dict[str, int]
    screen: Dict[str, int]
    webgl: Dict[str, str]
    canvas: Dict[str, Any]
    audio: Dict[str, Any]
    fonts: List[str]
    navigator: Dict[str, Any]
    timezone: Dict[str, Any]
    plugins: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProfileMetrics(BaseModel):
    """Profile performance metrics."""
    total_attempts: int = 0
    successful_purchases: int = 0
    failed_attempts: int = 0
    blocks_encountered: int = 0
    captchas_solved: int = 0
    average_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    trust_score: float = Field(default=50.0, ge=0.0, le=100.0)
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_purchases / self.total_attempts) * 100
    
    def update_trust_score(self, event: str, impact: float = 1.0) -> None:
        """Update trust score based on events."""
        if event == "success":
            self.trust_score = min(100.0, self.trust_score + (5.0 * impact))
        elif event == "failure":
            self.trust_score = max(0.0, self.trust_score - (3.0 * impact))
        elif event == "block":
            self.trust_score = max(0.0, self.trust_score - (10.0 * impact))
        elif event == "captcha":
            self.trust_score = max(0.0, self.trust_score - (2.0 * impact))


class ProxyBinding(BaseModel):
    """Proxy configuration bound to profile."""
    proxy_id: str
    provider: str
    country: str
    city: Optional[str] = None
    sticky_session: bool = True
    last_rotation: datetime = Field(default_factory=datetime.now)
    performance_score: float = Field(default=50.0)
    
    def should_rotate(self, max_age_hours: int = 24) -> bool:
        """Check if proxy should be rotated."""
        age = datetime.now() - self.last_rotation
        return age.total_seconds() > (max_age_hours * 3600)


class Profile(BaseModel):
    """Complete user profile for ticket purchasing."""
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: str
    
    # Status
    status: ProfileStatus = ProfileStatus.ACTIVE
    tier: ProfileTier = ProfileTier.STANDARD
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # User data
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    billing_address: BillingAddress
    payment_methods: List[PaymentMethod] = Field(default_factory=list)
    
    # Platform credentials
    credentials: List[UserCredentials] = Field(default_factory=list)
    
    # Browser configuration
    fingerprint: Optional[BrowserFingerprint] = None
    proxy_binding: Optional[ProxyBinding] = None
    
    # Performance tracking
    metrics: ProfileMetrics = Field(default_factory=ProfileMetrics)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    custom_data: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('email')
    def normalize_email(cls, v):
        """Normalize email to lowercase."""
        return v.lower()
    
    @validator('phone')
    def validate_phone(cls, v):
        """Basic phone validation."""
        # Remove common separators
        cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not cleaned.replace('+', '').isdigit():
            raise ValueError('Phone must contain only digits')
        return cleaned
    
    def get_credential(self, platform: str) -> Optional[UserCredentials]:
        """Get credentials for specific platform."""
        for cred in self.credentials:
            if cred.platform.lower() == platform.lower():
                return cred
        return None
    
    def add_credential(self, credential: UserCredentials) -> None:
        """Add or update platform credentials."""
        # Remove existing credential for platform
        self.credentials = [c for c in self.credentials if c.platform != credential.platform]
        self.credentials.append(credential)
        self.updated_at = datetime.now()
    
    def get_default_payment(self) -> Optional[PaymentMethod]:
        """Get default payment method."""
        for payment in self.payment_methods:
            if payment.is_default:
                return payment
        return self.payment_methods[0] if self.payment_methods else None
    
    def calculate_tier(self) -> ProfileTier:
        """Calculate profile tier based on trust score."""
        trust = self.metrics.trust_score
        if trust >= 90:
            return ProfileTier.PREMIUM
        elif trust >= 75:
            return ProfileTier.HIGH
        elif trust >= 50:
            return ProfileTier.MEDIUM
        elif trust >= 25:
            return ProfileTier.STANDARD
        else:
            return ProfileTier.LOW
    
    def update_metrics(self, event_type: str, success: bool = True) -> None:
        """Update profile metrics based on events."""
        self.metrics.total_attempts += 1
        
        if event_type == "purchase":
            if success:
                self.metrics.successful_purchases += 1
                self.metrics.last_success = datetime.now()
                self.metrics.update_trust_score("success")
            else:
                self.metrics.failed_attempts += 1
                self.metrics.last_failure = datetime.now()
                self.metrics.update_trust_score("failure")
        elif event_type == "block":
            self.metrics.blocks_encountered += 1
            self.metrics.update_trust_score("block")
        elif event_type == "captcha":
            self.metrics.captchas_solved += 1
            self.metrics.update_trust_score("captcha", 0.5)
        
        # Update tier based on new trust score
        self.tier = self.calculate_tier()
        self.updated_at = datetime.now()
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """Export profile without sensitive data."""
        data = self.dict()
        # Remove sensitive fields
        for cred in data.get('credentials', []):
            cred.pop('password', None)
            cred.pop('session_data', None)
            cred.pop('cookies', None)
        return data
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProfileGroup(BaseModel):
    """Group of profiles for coordinated actions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    profile_ids: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_profile(self, profile_id: str) -> None:
        """Add profile to group."""
        if profile_id not in self.profile_ids:
            self.profile_ids.append(profile_id)
    
    def remove_profile(self, profile_id: str) -> None:
        """Remove profile from group."""
        if profile_id in self.profile_ids:
            self.profile_ids.remove(profile_id)