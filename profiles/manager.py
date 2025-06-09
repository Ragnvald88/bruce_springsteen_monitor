# stealthmaster/profiles/manager.py
"""Profile management system with CRUD operations and intelligent selection."""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
import aiofiles
import random
from cryptography.fernet import Fernet

from .models import (
    Profile, ProfileStatus, ProfileTier, ProfileGroup,
    UserCredentials, BrowserFingerprint, ProxyBinding,
    ProfileMetrics, PaymentMethod, BillingAddress
)
from ..stealth.fingerprint import FingerprintGenerator
from ..config import Settings

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages user profiles with encryption and intelligent selection."""
    
    def __init__(self, settings: Settings):
        """Initialize profile manager."""
        self.settings = settings
        self.profiles: Dict[str, Profile] = {}
        self.groups: Dict[str, ProfileGroup] = {}
        self.profile_locks: Dict[str, asyncio.Lock] = {}
        
        # Paths
        self.profiles_dir = settings.data_dir / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Encryption for sensitive data
        self._cipher = self._init_encryption()
        
        # Performance tracking
        self._selection_history: List[Tuple[str, datetime]] = []
        self._profile_usage: Dict[str, int] = defaultdict(int)
        
        # Fingerprint generator
        self.fingerprint_gen = FingerprintGenerator()
        
        # Load profiles on init
        asyncio.create_task(self.load_all_profiles())
    
    def _init_encryption(self) -> Fernet:
        """Initialize encryption for sensitive data."""
        key_file = self.profiles_dir / ".key"
        
        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Restrict access
        
        return Fernet(key)
    
    async def create_profile(
        self,
        name: str,
        email: str,
        phone: str,
        first_name: str,
        last_name: str,
        billing_address: BillingAddress,
        **kwargs
    ) -> Profile:
        """
        Create a new profile.
        
        Args:
            name: Profile identifier name
            email: Email address
            phone: Phone number
            first_name: User's first name
            last_name: User's last name
            billing_address: Billing address
            **kwargs: Additional profile fields
            
        Returns:
            Created profile
        """
        # Create profile
        profile = Profile(
            name=name,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            billing_address=billing_address,
            **kwargs
        )
        
        # Generate initial fingerprint
        profile.fingerprint = BrowserFingerprint(
            **self.fingerprint_gen.generate()
        )
        
        # Store profile
        self.profiles[profile.id] = profile
        self.profile_locks[profile.id] = asyncio.Lock()
        
        # Save to disk
        await self.save_profile(profile)
        
        logger.info(f"Created profile: {profile.name} (ID: {profile.id})")
        return profile
    
    async def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID."""
        if profile_id in self.profiles:
            return self.profiles[profile_id]
        
        # Try loading from disk
        profile = await self.load_profile(profile_id)
        if profile:
            self.profiles[profile_id] = profile
            self.profile_locks[profile_id] = asyncio.Lock()
        
        return profile
    
    async def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Optional[Profile]:
        """
        Update profile fields.
        
        Args:
            profile_id: Profile ID
            updates: Fields to update
            
        Returns:
            Updated profile
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            return None
        
        async with self.profile_locks[profile_id]:
            # Apply updates
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            profile.updated_at = datetime.now()
            
            # Save changes
            await self.save_profile(profile)
        
        return profile
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        if profile_id not in self.profiles:
            return False
        
        # Remove from memory
        del self.profiles[profile_id]
        if profile_id in self.profile_locks:
            del self.profile_locks[profile_id]
        
        # Remove from groups
        for group in self.groups.values():
            group.remove_profile(profile_id)
        
        # Delete file
        profile_file = self.profiles_dir / f"{profile_id}.json"
        if profile_file.exists():
            profile_file.unlink()
        
        logger.info(f"Deleted profile: {profile_id}")
        return True
    
    async def select_profile(
        self,
        platform: str,
        tier_minimum: ProfileTier = ProfileTier.STANDARD,
        tags: Optional[List[str]] = None,
        exclude_ids: Optional[Set[str]] = None
    ) -> Optional[Profile]:
        """
        Select optimal profile for use.
        
        Args:
            platform: Target platform
            tier_minimum: Minimum tier requirement
            tags: Required tags
            exclude_ids: Profile IDs to exclude
            
        Returns:
            Selected profile or None
        """
        exclude_ids = exclude_ids or set()
        candidates = []
        
        for profile in self.profiles.values():
            # Skip excluded profiles
            if profile.id in exclude_ids:
                continue
            
            # Check status
            if profile.status != ProfileStatus.ACTIVE:
                continue
            
            # Check tier
            if profile.tier < tier_minimum:
                continue
            
            # Check platform credentials
            if not profile.get_credential(platform):
                continue
            
            # Check tags
            if tags and not all(tag in profile.tags for tag in tags):
                continue
            
            candidates.append(profile)
        
        if not candidates:
            logger.warning(f"No suitable profiles found for {platform}")
            return None
        
        # Score and sort candidates
        scored = []
        for profile in candidates:
            score = self._calculate_selection_score(profile, platform)
            scored.append((score, profile))
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Select with weighted randomization (top profiles more likely)
        weights = [score for score, _ in scored]
        selected = random.choices(
            [p for _, p in scored],
            weights=weights,
            k=1
        )[0]
        
        # Track selection
        self._selection_history.append((selected.id, datetime.now()))
        self._profile_usage[selected.id] += 1
        
        logger.info(f"Selected profile: {selected.name} for {platform}")
        return selected
    
    def _calculate_selection_score(self, profile: Profile, platform: str) -> float:
        """Calculate profile selection score."""
        score = 0.0
        
        # Base score from tier
        score += profile.tier.value * 20
        
        # Trust score component
        score += profile.metrics.trust_score * 0.5
        
        # Success rate component
        success_rate = profile.metrics.calculate_success_rate()
        score += success_rate * 0.3
        
        # Freshness bonus (less recently used)
        last_used = None
        for pid, timestamp in reversed(self._selection_history):
            if pid == profile.id:
                last_used = timestamp
                break
        
        if last_used:
            hours_ago = (datetime.now() - last_used).total_seconds() / 3600
            score += min(hours_ago * 2, 50)  # Max 50 point bonus
        else:
            score += 50  # Never used bonus
        
        # Credential freshness
        cred = profile.get_credential(platform)
        if cred and cred.last_login:
            days_since_login = (datetime.now() - cred.last_login).days
            if days_since_login < 1:
                score += 20
            elif days_since_login < 7:
                score += 10
        
        # Penalty for recent failures
        if profile.metrics.last_failure:
            hours_since_failure = (datetime.now() - profile.metrics.last_failure).total_seconds() / 3600
            if hours_since_failure < 1:
                score -= 30
            elif hours_since_failure < 6:
                score -= 15
        
        return max(score, 0.0)
    
    async def rotate_fingerprint(self, profile_id: str) -> bool:
        """
        Rotate browser fingerprint for profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Success status
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            return False
        
        async with self.profile_locks[profile_id]:
            # Generate new fingerprint maintaining platform
            old_platform = profile.fingerprint.navigator.get("platform", "Win32") if profile.fingerprint else "Win32"
            platform_map = {"Win32": "windows", "MacIntel": "mac", "Linux x86_64": "linux"}
            platform = platform_map.get(old_platform, "windows")
            
            new_fingerprint = self.fingerprint_gen.generate(platform)
            profile.fingerprint = BrowserFingerprint(**new_fingerprint)
            profile.updated_at = datetime.now()
            
            await self.save_profile(profile)
        
        logger.info(f"Rotated fingerprint for profile: {profile.name}")
        return True
    
    async def bind_proxy(self, profile_id: str, proxy_binding: ProxyBinding) -> bool:
        """
        Bind proxy to profile.
        
        Args:
            profile_id: Profile ID
            proxy_binding: Proxy configuration
            
        Returns:
            Success status
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            return False
        
        async with self.profile_locks[profile_id]:
            profile.proxy_binding = proxy_binding
            profile.updated_at = datetime.now()
            await self.save_profile(profile)
        
        logger.info(f"Bound proxy {proxy_binding.proxy_id} to profile: {profile.name}")
        return True
    
    async def add_credentials(
        self,
        profile_id: str,
        platform: str,
        username: str,
        password: str,
        **kwargs
    ) -> bool:
        """
        Add platform credentials to profile.
        
        Args:
            profile_id: Profile ID
            platform: Platform name
            username: Username
            password: Password
            **kwargs: Additional credential fields
            
        Returns:
            Success status
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            return False
        
        async with self.profile_locks[profile_id]:
            credentials = UserCredentials(
                platform=platform,
                username=username,
                password=password,
                **kwargs
            )
            profile.add_credential(credentials)
            await self.save_profile(profile)
        
        logger.info(f"Added {platform} credentials to profile: {profile.name}")
        return True
    
    async def update_session(
        self,
        profile_id: str,
        platform: str,
        session_data: Dict[str, Any],
        cookies: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update session data for platform.
        
        Args:
            profile_id: Profile ID
            platform: Platform name
            session_data: Session information
            cookies: Browser cookies
            
        Returns:
            Success status
        """
        profile = await self.get_profile(profile_id)
        if not profile:
            return False
        
        cred = profile.get_credential(platform)
        if not cred:
            return False
        
        async with self.profile_locks[profile_id]:
            cred.session_data = session_data
            cred.cookies = cookies
            cred.last_login = datetime.now()
            profile.updated_at = datetime.now()
            await self.save_profile(profile)
        
        return True
    
    async def create_group(self, name: str, description: Optional[str] = None) -> ProfileGroup:
        """Create a profile group."""
        group = ProfileGroup(name=name, description=description)
        self.groups[group.id] = group
        
        # Save group
        await self._save_group(group)
        
        logger.info(f"Created profile group: {name}")
        return group
    
    async def add_to_group(self, group_id: str, profile_ids: List[str]) -> bool:
        """Add profiles to group."""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        for profile_id in profile_ids:
            if profile_id in self.profiles:
                group.add_profile(profile_id)
        
        await self._save_group(group)
        return True
    
    async def get_group_profiles(self, group_id: str) -> List[Profile]:
        """Get all profiles in a group."""
        if group_id not in self.groups:
            return []
        
        group = self.groups[group_id]
        profiles = []
        
        for profile_id in group.profile_ids:
            profile = await self.get_profile(profile_id)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    async def save_profile(self, profile: Profile) -> None:
        """Save profile to disk with encryption."""
        profile_file = self.profiles_dir / f"{profile.id}.json"
        
        # Prepare data
        data = profile.dict()
        
        # Encrypt sensitive fields
        sensitive_fields = ["credentials", "payment_methods"]
        for field in sensitive_fields:
            if field in data and data[field]:
                encrypted = self._cipher.encrypt(
                    json.dumps(data[field]).encode()
                ).decode()
                data[field] = {"_encrypted": encrypted}
        
        # Write to file
        async with aiofiles.open(profile_file, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    async def load_profile(self, profile_id: str) -> Optional[Profile]:
        """Load profile from disk."""
        profile_file = self.profiles_dir / f"{profile_id}.json"
        
        if not profile_file.exists():
            return None
        
        try:
            async with aiofiles.open(profile_file, 'r') as f:
                data = json.loads(await f.read())
            
            # Decrypt sensitive fields
            sensitive_fields = ["credentials", "payment_methods"]
            for field in sensitive_fields:
                if field in data and isinstance(data[field], dict) and "_encrypted" in data[field]:
                    decrypted = self._cipher.decrypt(
                        data[field]["_encrypted"].encode()
                    ).decode()
                    data[field] = json.loads(decrypted)
            
            return Profile(**data)
            
        except Exception as e:
            logger.error(f"Failed to load profile {profile_id}: {e}")
            return None
    
    async def load_all_profiles(self) -> None:
        """Load all profiles from disk."""
        for profile_file in self.profiles_dir.glob("*.json"):
            if profile_file.stem.startswith("."):
                continue
            
            profile_id = profile_file.stem
            profile = await self.load_profile(profile_id)
            
            if profile:
                self.profiles[profile_id] = profile
                self.profile_locks[profile_id] = asyncio.Lock()
        
        logger.info(f"Loaded {len(self.profiles)} profiles")
        
        # Load groups
        groups_file = self.profiles_dir / ".groups.json"
        if groups_file.exists():
            try:
                async with aiofiles.open(groups_file, 'r') as f:
                    groups_data = json.loads(await f.read())
                
                for group_data in groups_data:
                    group = ProfileGroup(**group_data)
                    self.groups[group.id] = group
                
                logger.info(f"Loaded {len(self.groups)} profile groups")
            except Exception as e:
                logger.error(f"Failed to load groups: {e}")
    
    async def _save_group(self, group: ProfileGroup) -> None:
        """Save group data."""
        groups_file = self.profiles_dir / ".groups.json"
        
        # Load existing groups
        groups_data = []
        if groups_file.exists():
            try:
                async with aiofiles.open(groups_file, 'r') as f:
                    groups_data = json.loads(await f.read())
            except Exception:
                pass
        
        # Update or add group
        group_dict = group.dict()
        found = False
        for i, g in enumerate(groups_data):
            if g["id"] == group.id:
                groups_data[i] = group_dict
                found = True
                break
        
        if not found:
            groups_data.append(group_dict)
        
        # Save
        async with aiofiles.open(groups_file, 'w') as f:
            await f.write(json.dumps(groups_data, indent=2))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get profile management statistics."""
        total = len(self.profiles)
        
        if total == 0:
            return {
                "total_profiles": 0,
                "active_profiles": 0,
                "profiles_by_tier": {},
                "average_trust_score": 0.0,
                "average_success_rate": 0.0
            }
        
        # Calculate statistics
        active = sum(1 for p in self.profiles.values() if p.status == ProfileStatus.ACTIVE)
        
        # Group by tier
        by_tier = defaultdict(int)
        trust_scores = []
        success_rates = []
        
        for profile in self.profiles.values():
            by_tier[profile.tier.name] += 1
            trust_scores.append(profile.metrics.trust_score)
            success_rates.append(profile.metrics.calculate_success_rate())
        
        return {
            "total_profiles": total,
            "active_profiles": active,
            "profiles_by_tier": dict(by_tier),
            "average_trust_score": sum(trust_scores) / len(trust_scores),
            "average_success_rate": sum(success_rates) / len(success_rates),
            "total_groups": len(self.groups),
            "recent_selections": self._selection_history[-10:],
            "usage_distribution": dict(self._profile_usage)
        }
    
    async def maintenance_cleanup(self) -> None:
        """Perform maintenance tasks on profiles."""
        logger.info("Starting profile maintenance")
        
        for profile in self.profiles.values():
            # Check proxy rotation need
            if profile.proxy_binding and profile.proxy_binding.should_rotate():
                logger.info(f"Profile {profile.name} needs proxy rotation")
            
            # Check fingerprint age
            if profile.fingerprint:
                age = datetime.now() - profile.fingerprint.created_at
                if age.days > 30:
                    logger.info(f"Profile {profile.name} has old fingerprint ({age.days} days)")
            
            # Update tier based on current metrics
            old_tier = profile.tier
            profile.tier = profile.calculate_tier()
            if old_tier != profile.tier:
                logger.info(f"Profile {profile.name} tier changed: {old_tier.name} -> {profile.tier.name}")
                await self.save_profile(profile)
        
        logger.info("Profile maintenance completed")