# src/core/profiles/persistence.py
"""Profile persistence handling."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import aiofiles
from cryptography.fernet import Fernet

from .models import BrowserProfile
from src.core.advanced_profile_system import DynamicProfile, ProfileState, MutationStrategy

logger = logging.getLogger(__name__)


class ProfilePersistence:
    """Handle profile saving and loading."""
    
    def __init__(self, filepath: str, enable_encryption: bool = True):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.enable_encryption = enable_encryption
        
        if self.enable_encryption:
            self._encryption_key = self._load_or_generate_key()
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate encryption key."""
        key_file = self.filepath.parent / '.profile_key'
        
        try:
            if key_file.exists():
                return key_file.read_bytes()
            else:
                key = Fernet.generate_key()
                key_file.write_bytes(key)
                return key
        except Exception as e:
            logger.error(f"Error handling encryption key: {e}")
            return Fernet.generate_key()
    
    async def save_profiles(
        self,
        dynamic_profiles: List[DynamicProfile],
        static_profiles: Dict[str, BrowserProfile]
    ):
        """Save profiles to disk."""
        try:
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'version': '2.1',
                'profiles': []
            }
            
            for dynamic_profile in dynamic_profiles:
                static_profile = static_profiles.get(dynamic_profile.id)
                
                profile_data = {
                    'id': dynamic_profile.id,
                    'state': dynamic_profile.state.value,
                    'created_at': dynamic_profile.created_at.isoformat(),
                    'last_active': dynamic_profile.last_active.isoformat(),
                    'fingerprint': dynamic_profile.get_fingerprint_snapshot(),
                    'stats': {
                        'success_count': dynamic_profile.success_count,
                        'failure_count': dynamic_profile.failure_count,
                        'consecutive_failures': dynamic_profile.consecutive_failures
                    }
                }
                
                if static_profile:
                    profile_data['static'] = {
                        'quality': static_profile.quality.name,
                        'platform_sessions': static_profile.platform_sessions,
                        'platform_stats': dict(static_profile.platform_stats),
                        'proxy_session_id': static_profile.proxy_session_id,
                        'proxy_provider': (
                            static_profile.proxy_config.proxy_provider
                            if static_profile.proxy_config else None
                        ),
                        'fingerprint_hash': static_profile.fingerprint_hash
                    }
                
                backup_data['profiles'].append(profile_data)
            
            # Save to disk
            content = json.dumps(backup_data, indent=2)
            
            if self.enable_encryption:
                fernet = Fernet(self._encryption_key)
                content = fernet.encrypt(content.encode()).decode()
            
            async with aiofiles.open(self.filepath, 'w') as f:
                await f.write(content)
            
            logger.info(f"Saved {len(dynamic_profiles)} profiles to disk")
            
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}", exc_info=True)
    
    async def load_profiles(
        self,
        dynamic_profiles: List[DynamicProfile],
        static_profiles: Dict[str, BrowserProfile],
        mutation_strategy: MutationStrategy
    ) -> bool:
        """Load profiles from disk."""
        try:
            if not self.filepath.exists():
                return False
            
            async with aiofiles.open(self.filepath, 'r') as f:
                content = await f.read()
            
            if self.enable_encryption:
                try:
                    fernet = Fernet(self._encryption_key)
                    content = fernet.decrypt(content.encode()).decode()
                except Exception:
                    logger.warning("Failed to decrypt profiles, trying unencrypted")
            
            backup_data = json.loads(content)
            
            logger.info(f"Loading profiles from {backup_data.get('timestamp', 'unknown time')}")
            
            for profile_data in backup_data.get('profiles', []):
                try:
                    # Recreate dynamic profile
                    base_profile = profile_data.get('fingerprint', {})
                    base_profile['device_class'] = base_profile.get('device_class', 'mid_range_desktop')
                    
                    dynamic_profile = DynamicProfile(
                        mutation_strategy=mutation_strategy,
                        base_profile_dict=base_profile,
                        profile_id=profile_data['id']
                    )
                    
                    # Restore state
                    dynamic_profile.state = ProfileState(profile_data['state'])
                    dynamic_profile.created_at = datetime.fromisoformat(profile_data['created_at'])
                    dynamic_profile.last_active = datetime.fromisoformat(profile_data['last_active'])
                    
                    stats = profile_data.get('stats', {})
                    dynamic_profile.success_count = stats.get('success_count', 0)
                    dynamic_profile.failure_count = stats.get('failure_count', 0)
                    dynamic_profile.consecutive_failures = stats.get('consecutive_failures', 0)
                    
                    dynamic_profiles.append(dynamic_profile)
                    
                except Exception as e:
                    logger.error(f"Failed to load profile {profile_data.get('id', 'unknown')}: {e}")
            
            return len(dynamic_profiles) > 0
            
        except Exception as e:
            logger.error(f"Failed to load profiles from disk: {e}", exc_info=True)
            return False