# src/profiles/manager.py - Simplified but Powerful Version
"""
StealthMaster AI Profile Manager v2.0
Simplified for immediate use while maintaining core functionality
"""

import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

from .models import BrowserProfile, ProfileQuality, Platform
from .utils import generate_random_profile

logger = logging.getLogger(__name__)


class ProfileManager:
    """Simplified but effective profile manager for StealthMaster AI"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.profiles: Dict[str, BrowserProfile] = {}
        self.profile_stats: Dict[str, Dict] = {}
        
        # Storage location
        self.storage_path = Path("data/profiles/profiles.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing profiles or create new ones
        self._load_or_create_profiles()
        
        logger.info(f"ProfileManager initialized with {len(self.profiles)} profiles")
    
    def _load_or_create_profiles(self) -> None:
        """Load existing profiles or create new ones"""
        if self.storage_path.exists():
            try:
                self._load_profiles()
                logger.info(f"Loaded {len(self.profiles)} existing profiles")
            except Exception as e:
                logger.error(f"Failed to load profiles: {e}")
                self._create_initial_profiles()
        else:
            self._create_initial_profiles()
    
    def _create_initial_profiles(self) -> None:
        """Create initial set of profiles"""
        num_profiles = self.config.get('num_target_profiles', 15)
        
        logger.info(f"Creating {num_profiles} initial profiles...")
        
        for i in range(num_profiles):
            # Create profile with quality distribution
            if i < 3:
                quality = ProfileQuality.PREMIUM
            elif i < 8:
                quality = ProfileQuality.HIGH
            elif i < 12:
                quality = ProfileQuality.MEDIUM
            else:
                quality = ProfileQuality.LOW
            
            profile = self._create_profile(quality)
            self.profiles[profile.profile_id] = profile
        
        self._save_profiles()
    
    def _create_profile(self, quality: ProfileQuality) -> BrowserProfile:
        """Create a single profile with specified quality"""
        # Use your existing profile generation
        profile_data = generate_random_profile()
        
        # Enhance based on quality
        if quality == ProfileQuality.PREMIUM:
            profile_data['user_agent'] = self._get_premium_user_agent()
            profile_data['viewport_width'] = random.choice([1920, 2560])
            profile_data['viewport_height'] = random.choice([1080, 1440])
        
        profile = BrowserProfile(**profile_data)
        profile.quality = quality
        
        # Initialize platform stats
        for platform in ['fansale', 'ticketmaster', 'vivaticket']:
            profile.platform_stats[platform] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'last_success': None,
                'last_failure': None,
                'success_rate': 0.0
            }
        
        return profile
    
    def _get_premium_user_agent(self) -> str:
        """Get a premium user agent string"""
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        return random.choice(agents)
    
    async def get_healthy_profiles(
        self, 
        platform: str = None,
        min_quality_tier: int = 1,
        limit: int = None
    ) -> List[BrowserProfile]:
        """Get healthy profiles for use"""
        healthy = []
        
        for profile in self.profiles.values():
            # Check quality tier
            if profile.quality.tier < min_quality_tier:
                continue
            
            # Check if not compromised
            if hasattr(profile, 'state') and profile.state == 'compromised':
                continue
            
            # Check platform performance if specified
            if platform:
                stats = profile.platform_stats.get(platform, {})
                if stats.get('failures', 0) > stats.get('successes', 0) * 2:
                    continue  # Too many failures
            
            healthy.append(profile)
        
        # Sort by success rate
        if platform:
            healthy.sort(
                key=lambda p: p.platform_stats.get(platform, {}).get('success_rate', 0),
                reverse=True
            )
        
        if limit:
            healthy = healthy[:limit]
        
        return healthy
    
    async def record_feedback(
        self,
        profile_id: str,
        event: str,
        platform: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Record usage feedback for a profile"""
        if profile_id not in self.profiles:
            logger.warning(f"Unknown profile: {profile_id}")
            return
        
        profile = self.profiles[profile_id]
        stats = profile.platform_stats.setdefault(platform, {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'success_rate': 0.0
        })
        
        # Update stats
        stats['attempts'] += 1
        
        if event == 'success' or 'success' in event.lower():
            stats['successes'] += 1
            stats['last_success'] = datetime.now().isoformat()
        else:
            stats['failures'] += 1
            stats['last_failure'] = datetime.now().isoformat()
        
        # Calculate success rate
        if stats['attempts'] > 0:
            stats['success_rate'] = stats['successes'] / stats['attempts']
        
        # Save periodically
        if stats['attempts'] % 10 == 0:
            self._save_profiles()
        
        logger.info(f"Profile {profile_id} on {platform}: {event} "
                   f"(success rate: {stats['success_rate']:.1%})")
    
    def get_profile(self, profile_id: str) -> Optional[BrowserProfile]:
        """Get specific profile by ID"""
        return self.profiles.get(profile_id)
    
    def rotate_profiles(self) -> None:
        """Rotate profiles - retire poor performers, create new ones"""
        # Find worst performers
        worst_profiles = []
        
        for profile_id, profile in self.profiles.items():
            total_attempts = sum(
                stats.get('attempts', 0) 
                for stats in profile.platform_stats.values()
            )
            
            if total_attempts > 50:  # Enough data
                total_success = sum(
                    stats.get('successes', 0)
                    for stats in profile.platform_stats.values()
                )
                
                success_rate = total_success / total_attempts
                if success_rate < 0.1:  # Less than 10% success
                    worst_profiles.append((profile_id, success_rate))
        
        # Replace worst 20%
        worst_profiles.sort(key=lambda x: x[1])
        to_replace = worst_profiles[:max(1, len(worst_profiles) // 5)]
        
        for profile_id, _ in to_replace:
            logger.info(f"Retiring poor performer: {profile_id}")
            del self.profiles[profile_id]
            
            # Create replacement
            new_profile = self._create_profile(ProfileQuality.MEDIUM)
            self.profiles[new_profile.profile_id] = new_profile
            logger.info(f"Created replacement: {new_profile.profile_id}")
        
        if to_replace:
            self._save_profiles()
    
    def _save_profiles(self) -> None:
        """Save profiles to disk"""
        try:
            data = {
                'profiles': {
                    pid: self._profile_to_dict(profile)
                    for pid, profile in self.profiles.items()
                },
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    def _load_profiles(self) -> None:
        """Load profiles from disk"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for pid, profile_data in data.get('profiles', {}).items():
                profile = self._dict_to_profile(profile_data)
                self.profiles[pid] = profile
                
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            raise
    
    def _profile_to_dict(self, profile: BrowserProfile) -> Dict:
        """Convert profile to dictionary for storage"""
        data = asdict(profile)
        # Convert enums to strings
        if 'quality' in data and hasattr(profile.quality, 'name'):
            data['quality'] = profile.quality.name
        if 'data_optimization_level' in data and hasattr(data['data_optimization_level'], 'name'):
            data['data_optimization_level'] = data['data_optimization_level'].name
        # Convert datetime objects to ISO format strings
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        if 'last_used' in data and data['last_used'] and isinstance(data['last_used'], datetime):
            data['last_used'] = data['last_used'].isoformat()
        # Convert sets to lists for JSON serialization
        if 'block_resources' in data and isinstance(data['block_resources'], set):
            data['block_resources'] = list(data['block_resources'])
        # Convert Path objects to strings
        if 'persistent_context_dir' in data and data['persistent_context_dir']:
            from pathlib import Path
            if isinstance(data['persistent_context_dir'], Path):
                data['persistent_context_dir'] = str(data['persistent_context_dir'])
        # Remove internal fields
        data.pop('_context_encryption_key', None)
        return data
    
    def _dict_to_profile(self, data: Dict) -> BrowserProfile:
        """Convert dictionary to profile"""
        # Import here to avoid circular import
        from .consilidated_models import DataOptimizationLevel
        
        # Convert quality string back to enum
        if 'quality' in data and isinstance(data['quality'], str):
            data['quality'] = ProfileQuality[data['quality']]
        
        # Convert data_optimization_level string back to enum
        if 'data_optimization_level' in data and isinstance(data['data_optimization_level'], str):
            data['data_optimization_level'] = DataOptimizationLevel[data['data_optimization_level']]
        
        # Convert datetime strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_used' in data and isinstance(data['last_used'], str):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        
        # Convert list back to set
        if 'block_resources' in data and isinstance(data['block_resources'], list):
            data['block_resources'] = set(data['block_resources'])
        
        # Convert string back to Path
        if 'persistent_context_dir' in data and isinstance(data['persistent_context_dir'], str):
            from pathlib import Path
            data['persistent_context_dir'] = Path(data['persistent_context_dir'])
        
        return BrowserProfile(**data)
    
    async def initialize(self) -> None:
        """Initialize manager (for compatibility)"""
        logger.info("ProfileManager initialized")
        # Rotate out poor performers on startup
        self.rotate_profiles()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        total_profiles = len(self.profiles)
        
        quality_distribution = {}
        for profile in self.profiles.values():
            quality = profile.quality.name
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        platform_stats = {}
        for platform in ['fansale', 'ticketmaster', 'vivaticket']:
            total_attempts = sum(
                p.platform_stats.get(platform, {}).get('attempts', 0)
                for p in self.profiles.values()
            )
            total_successes = sum(
                p.platform_stats.get(platform, {}).get('successes', 0)
                for p in self.profiles.values()
            )
            
            platform_stats[platform] = {
                'attempts': total_attempts,
                'successes': total_successes,
                'success_rate': total_successes / total_attempts if total_attempts > 0 else 0
            }
        
        return {
            'total_profiles': total_profiles,
            'quality_distribution': quality_distribution,
            'platform_performance': platform_stats
        }