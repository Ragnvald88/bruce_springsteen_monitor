"""Configuration validation utilities."""

import logging
from typing import List, Tuple
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration settings on startup."""
    
    def __init__(self, settings):
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate configuration settings.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validate targets
        self._validate_targets()
        
        # Validate authentication
        self._validate_authentication()
        
        # Validate proxy settings
        self._validate_proxy_settings()
        
        # Validate browser settings
        self._validate_browser_settings()
        
        # Validate captcha settings
        self._validate_captcha_settings()
        
        # Check Chrome installation
        self._validate_chrome_installation()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
        
    def _validate_targets(self):
        """Validate monitoring targets."""
        if not self.settings.targets:
            self.errors.append("No monitoring targets configured")
            return
            
        enabled_count = sum(1 for t in self.settings.targets if t.enabled)
        if enabled_count == 0:
            self.errors.append("No monitoring targets are enabled")
            
        for i, target in enumerate(self.settings.targets):
            if target.enabled:
                # Check URL
                if not target.url:
                    self.errors.append(f"Target {i}: Missing URL")
                    
                # Check price limits
                if target.max_price_per_ticket <= 0:
                    self.warnings.append(f"Target {i}: No price limit set")
                    
                # Check ticket quantity
                if target.max_ticket_quantity < target.min_ticket_quantity:
                    self.errors.append(f"Target {i}: max_ticket_quantity < min_ticket_quantity")
                    
    def _validate_authentication(self):
        """Validate authentication credentials."""
        if not self.settings.authentication.enabled:
            self.warnings.append("Authentication is disabled - manual login will be required")
            return
            
        platforms = self.settings.authentication.platforms
        
        # Check if credentials are placeholder values
        for platform, creds in platforms.items():
            if creds.username and creds.username.startswith("${"):
                self.errors.append(f"{platform}: Username not configured (still using placeholder)")
            elif creds.username and "@example.com" in creds.username:
                self.warnings.append(f"{platform}: Username appears to be a placeholder")
                
            if creds.password and creds.password.startswith("${"):
                self.errors.append(f"{platform}: Password not configured (still using placeholder)")
            elif creds.password == "your_password":
                self.warnings.append(f"{platform}: Password appears to be a placeholder")
                
    def _validate_proxy_settings(self):
        """Validate proxy configuration."""
        if not self.settings.proxy_settings.enabled:
            self.warnings.append("Proxies disabled - higher risk of IP blocks")
            return
            
        if not self.settings.proxy_settings.primary_pool:
            self.errors.append("Proxy enabled but no proxies configured")
            return
            
        for i, proxy in enumerate(self.settings.proxy_settings.primary_pool):
            # Check for placeholder values
            if proxy.host.startswith("${") or "example.com" in proxy.host:
                self.errors.append(f"Proxy {i}: Invalid host configuration")
                
            if proxy.username.startswith("${"):
                self.errors.append(f"Proxy {i}: Username not configured")
                
            if proxy.password.startswith("${"):
                self.errors.append(f"Proxy {i}: Password not configured")
                
    def _validate_browser_settings(self):
        """Validate browser configuration."""
        if self.settings.browser_options.headless:
            self.warnings.append("Running in headless mode - some sites may detect this")
            
    def _validate_captcha_settings(self):
        """Validate CAPTCHA service configuration."""
        if self.settings.captcha_settings.enabled:
            if not self.settings.captcha_settings.api_key:
                self.errors.append("CAPTCHA service enabled but no API key configured")
            elif self.settings.captcha_settings.api_key.startswith("${"):
                self.errors.append("CAPTCHA API key not configured (using placeholder)")
                
    def _validate_chrome_installation(self):
        """Check if Chrome is installed."""
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        ]
        
        chrome_found = False
        chrome_env = os.getenv('CHROME_PATH')
        
        if chrome_env and os.path.exists(chrome_env):
            chrome_found = True
        else:
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_found = True
                    break
                    
        if not chrome_found:
            self.errors.append("Chrome/Chromium not found - please install Chrome")
            
    def print_validation_results(self):
        """Print validation results to console."""
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        
        if self.errors:
            console.print("\n[red]❌ Configuration Errors:[/red]")
            for error in self.errors:
                console.print(f"  • {error}")
                
        if self.warnings:
            console.print("\n[yellow]⚠️  Configuration Warnings:[/yellow]")
            for warning in self.warnings:
                console.print(f"  • {warning}")
                
        if not self.errors and not self.warnings:
            console.print("[green]✅ Configuration valid![/green]")
            
        return len(self.errors) == 0