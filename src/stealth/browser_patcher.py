"""
Browser-level patches applied before launch to prevent detection.
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BrowserPatcher:
    """
    Applies patches to browser executable and resources to prevent detection.
    Similar approach to undetected-chromedriver but for Playwright.
    """
    
    def __init__(self):
        """Initialize browser patcher"""
        self._patches_applied = False
        self._patched_browser_path: Optional[Path] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        
    def patch_browser(self, original_browser_path: str) -> str:
        """
        Create patched browser instance
        
        Args:
            original_browser_path: Path to original browser executable
            
        Returns:
            Path to patched browser
        """
        if self._patches_applied:
            return str(self._patched_browser_path)
        
        logger.info("Creating patched browser instance...")
        
        # Create temporary directory for patched browser
        self._temp_dir = tempfile.TemporaryDirectory(prefix='stealth_browser_')
        temp_path = Path(self._temp_dir.name)
        
        # Copy browser to temp location
        browser_name = Path(original_browser_path).name
        self._patched_browser_path = temp_path / browser_name
        shutil.copy2(original_browser_path, self._patched_browser_path)
        
        # Make executable
        os.chmod(self._patched_browser_path, 0o755)
        
        # Apply binary patches
        self._apply_binary_patches()
        
        # Apply resource patches
        self._apply_resource_patches(original_browser_path)
        
        self._patches_applied = True
        logger.info(f"Browser patched successfully: {self._patched_browser_path}")
        
        return str(self._patched_browser_path)
    
    def _apply_binary_patches(self):
        """Apply binary-level patches to browser executable"""
        # Read binary
        with open(self._patched_browser_path, 'rb') as f:
            binary_data = f.read()
        
        # Patches to apply (hex patterns)
        patches = [
            # Remove "HeadlessChrome" string
            (b'HeadlessChrome', b'Chrome\x00\x00\x00\x00\x00\x00\x00\x00'),
            
            # Modify CDP domain strings to prevent detection
            (b'Runtime.enable', b'Rumtime.enable'),  # Intentional typo
            (b'cdp.Runtime', b'cdq.Runtime'),
            
            # Remove webdriver-related strings
            (b'webdriver', b'navigator'),
            (b'$cdc_', b'$wdc_'),
            (b'$chrome_asyncScriptInfo', b'$chrome_asyncScriptLnfo'),
        ]
        
        # Apply patches
        for search, replace in patches:
            if len(search) != len(replace):
                logger.warning(f"Patch size mismatch: {search} -> {replace}")
                continue
            binary_data = binary_data.replace(search, replace)
        
        # Write patched binary
        with open(self._patched_browser_path, 'wb') as f:
            f.write(binary_data)
    
    def _apply_resource_patches(self, original_browser_path: str):
        """Apply patches to browser resources"""
        original_dir = Path(original_browser_path).parent
        patched_dir = self._patched_browser_path.parent
        
        # Copy required resources
        resources_to_copy = [
            'chrome_100_percent.pak',
            'chrome_200_percent.pak',
            'resources.pak',
            'v8_context_snapshot.bin',
            'icudtl.dat',
        ]
        
        for resource in resources_to_copy:
            src = original_dir / resource
            if src.exists():
                shutil.copy2(src, patched_dir / resource)
        
        # Copy locales
        locales_src = original_dir / 'locales'
        if locales_src.exists():
            shutil.copytree(locales_src, patched_dir / 'locales', dirs_exist_ok=True)
        
        # Create modified preferences
        self._create_stealth_preferences(patched_dir)
    
    def _create_stealth_preferences(self, browser_dir: Path):
        """Create stealth browser preferences"""
        prefs = {
            "webkit": {
                "webprefs": {
                    "webdriver_enable": False,
                    "automation_controlled": False,
                    "dom_automation_controller_enable": False,
                    "enable_automation": False
                }
            },
            "browser": {
                "enable_automation": False,
                "automation_controlled": False
            },
            "profile": {
                "exit_type": "Normal",
                "exited_cleanly": True
            }
        }
        
        # Write preferences
        prefs_file = browser_dir / 'Default' / 'Preferences'
        prefs_file.parent.mkdir(exist_ok=True)
        
        import json
        with open(prefs_file, 'w') as f:
            json.dump(prefs, f, indent=2)
    
    def cleanup(self):
        """Cleanup patched browser"""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
        self._patches_applied = False
        self._patched_browser_path = None