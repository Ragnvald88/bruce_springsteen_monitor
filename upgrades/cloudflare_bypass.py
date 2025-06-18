"""
CloudFlare Bypass Service Integration
=====================================
Implements FlareSolverr integration to bypass CloudFlare's bot detection
that's causing the 10-minute timeout on FanSale.it
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin
import docker
import time

logger = logging.getLogger(__name__)


@dataclass
class CloudFlareResponse:
    """Response from CloudFlare bypass"""
    url: str
    status: int
    headers: Dict[str, str]
    cookies: Dict[str, str]
    html: str
    solution: Dict[str, Any]


class CloudFlareBypass:
    """
    Manages CloudFlare bypass using FlareSolverr
    Handles the 10-minute detection issue on FanSale.it
    """
    
    def __init__(self, flaresolverr_url: str = "http://localhost:8191"):
        self.flaresolverr_url = flaresolverr_url
        self.session_id = None
        self.max_timeout = 60000  # 60 seconds
        self.docker_client = None
        self.container = None
        
    async def start_flaresolverr(self) -> bool:
        """Start FlareSolverr Docker container if not running"""
        try:
            self.docker_client = docker.from_env()
            
            # Check if container exists
            try:
                self.container = self.docker_client.containers.get('flaresolverr')
                if self.container.status != 'running':
                    self.container.start()
                    logger.info("Started existing FlareSolverr container")
                else:
                    logger.info("FlareSolverr container already running")
            except docker.errors.NotFound:
                # Create and start new container
                logger.info("Creating new FlareSolverr container...")
                self.container = self.docker_client.containers.run(
                    'ghcr.io/flaresolverr/flaresolverr:latest',
                    name='flaresolverr',
                    ports={'8191/tcp': 8191},
                    detach=True,
                    environment={
                        'LOG_LEVEL': 'info',
                        'CAPTCHA_SOLVER': 'none'  # We'll use 2captcha separately
                    }
                )
                logger.info("FlareSolverr container created and started")
            
            # Wait for service to be ready
            await self._wait_for_service()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start FlareSolverr: {e}")
            return False
    
    async def _wait_for_service(self, max_retries: int = 30):
        """Wait for FlareSolverr service to be ready"""
        for i in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.flaresolverr_url}/health") as resp:
                        if resp.status == 200:
                            logger.info("FlareSolverr service is ready")
                            return
            except:
                pass
            
            await asyncio.sleep(1)
        
        raise Exception("FlareSolverr service failed to start")
    
    async def create_session(self) -> str:
        """Create a new FlareSolverr session"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "cmd": "sessions.create",
                    "session": f"fansale_{int(time.time())}"
                }
                
                async with session.post(
                    f"{self.flaresolverr_url}/v1",
                    json=payload
                ) as resp:
                    data = await resp.json()
                    
                    if data.get("status") == "ok":
                        self.session_id = data["session"]
                        logger.info(f"Created CloudFlare session: {self.session_id}")
                        return self.session_id
                    else:
                        raise Exception(f"Failed to create session: {data}")
                        
        except Exception as e:
            logger.error(f"Error creating CloudFlare session: {e}")
            raise
    
    async def solve_challenge(self, url: str, user_agent: Optional[str] = None) -> CloudFlareResponse:
        """
        Solve CloudFlare challenge for a given URL
        This is the key to bypassing the 10-minute timeout
        """
        if not self.session_id:
            await self.create_session()
        
        try:
            payload = {
                "cmd": "request.get",
                "url": url,
                "session": self.session_id,
                "maxTimeout": self.max_timeout
            }
            
            if user_agent:
                payload["userAgent"] = user_agent
            
            logger.info(f"Solving CloudFlare challenge for: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.flaresolverr_url}/v1",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.max_timeout/1000 + 10)
                ) as resp:
                    data = await resp.json()
                    
                    if data.get("status") == "ok":
                        solution = data["solution"]
                        
                        # Extract cookies
                        cookies = {}
                        for cookie in solution.get("cookies", []):
                            cookies[cookie["name"]] = cookie["value"]
                        
                        logger.info(f"Successfully bypassed CloudFlare for {url}")
                        logger.debug(f"Got cookies: {list(cookies.keys())}")
                        
                        return CloudFlareResponse(
                            url=solution["url"],
                            status=solution["status"],
                            headers=solution.get("headers", {}),
                            cookies=cookies,
                            html=solution.get("response", ""),
                            solution=solution
                        )
                    else:
                        error_msg = data.get("message", "Unknown error")
                        raise Exception(f"CloudFlare bypass failed: {error_msg}")
                        
        except asyncio.TimeoutError:
            logger.error("CloudFlare bypass timed out")
            raise
        except Exception as e:
            logger.error(f"Error solving CloudFlare challenge: {e}")
            raise
    
    async def get_tokens_for_browser(self, url: str) -> Dict[str, Any]:
        """
        Get CloudFlare tokens that can be injected into a browser
        This prevents the 10-minute detection
        """
        response = await self.solve_challenge(url)
        
        # Extract critical tokens
        tokens = {
            "cookies": response.cookies,
            "user_agent": response.solution.get("userAgent", ""),
            "headers": response.headers
        }
        
        # Look for specific CloudFlare tokens
        cf_tokens = {}
        for name, value in response.cookies.items():
            if name.startswith('cf_') or name == '__cf_bm' or name == '_cfuvid':
                cf_tokens[name] = value
        
        tokens["cf_tokens"] = cf_tokens
        
        logger.info(f"Extracted CloudFlare tokens: {list(cf_tokens.keys())}")
        return tokens
    
    async def destroy_session(self):
        """Destroy the current session"""
        if self.session_id:
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "cmd": "sessions.destroy",
                        "session": self.session_id
                    }
                    
                    await session.post(f"{self.flaresolverr_url}/v1", json=payload)
                    logger.info(f"Destroyed CloudFlare session: {self.session_id}")
                    self.session_id = None
            except Exception as e:
                logger.error(f"Error destroying session: {e}")
    
    def stop_flaresolverr(self):
        """Stop FlareSolverr container"""
        if self.container:
            try:
                self.container.stop()
                logger.info("Stopped FlareSolverr container")
            except Exception as e:
                logger.error(f"Error stopping FlareSolverr: {e}")


class CloudFlareIntegration:
    """
    Integration layer for CloudFlare bypass with Playwright/Selenium
    """
    
    def __init__(self):
        self.bypass = CloudFlareBypass()
        self.token_cache = {}
        self.last_token_refresh = {}
        
    async def prepare_browser_with_tokens(self, page: Any, url: str) -> bool:
        """
        Prepare a browser page with CloudFlare tokens
        This is called before navigating to FanSale.it
        """
        try:
            # Get fresh tokens if needed (refresh every 8 minutes)
            cache_key = url.split('?')[0]  # Remove query params
            last_refresh = self.last_token_refresh.get(cache_key, 0)
            
            if time.time() - last_refresh > 480:  # 8 minutes
                logger.info("Refreshing CloudFlare tokens...")
                tokens = await self.bypass.get_tokens_for_browser(url)
                self.token_cache[cache_key] = tokens
                self.last_token_refresh[cache_key] = time.time()
            else:
                tokens = self.token_cache.get(cache_key)
                if not tokens:
                    tokens = await self.bypass.get_tokens_for_browser(url)
                    self.token_cache[cache_key] = tokens
                    self.last_token_refresh[cache_key] = time.time()
            
            # Apply tokens to browser
            if hasattr(page, 'context'):  # Playwright
                context = page.context
                
                # Add cookies
                cookies_list = []
                for name, value in tokens['cookies'].items():
                    cookies_list.append({
                        'name': name,
                        'value': value,
                        'domain': '.fansale.it',
                        'path': '/'
                    })
                
                await context.add_cookies(cookies_list)
                
                # Set user agent if different
                if tokens.get('user_agent'):
                    # This is set at context creation, log for info
                    logger.info(f"CloudFlare UA: {tokens['user_agent'][:50]}...")
                
            else:  # Selenium
                # Add cookies after navigating to domain
                for name, value in tokens['cookies'].items():
                    page.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.fansale.it'
                    })
            
            logger.info("Applied CloudFlare bypass tokens to browser")
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare browser with tokens: {e}")
            return False
    
    async def check_challenge_on_page(self, page: Any) -> bool:
        """Check if current page has CloudFlare challenge"""
        try:
            if hasattr(page, 'content'):  # Playwright
                content = await page.content()
            else:  # Selenium
                content = page.page_source
            
            # Check for CloudFlare challenge indicators
            cf_indicators = [
                'Checking your browser',
                'cf-browser-verification',
                'cf_clearance',
                '__cf_chl_jschl_tk__',
                'cf-challenge-running'
            ]
            
            return any(indicator in content for indicator in cf_indicators)
            
        except Exception as e:
            logger.error(f"Error checking for CloudFlare challenge: {e}")
            return False


# Global instance
cloudflare_bypass = CloudFlareIntegration()
