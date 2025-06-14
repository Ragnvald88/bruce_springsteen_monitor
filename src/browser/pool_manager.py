    
    async def get_browser_for_monitoring(self, platform: str, requires_auth: bool = False) -> BrowserInstance:
        """
        Get appropriate browser for monitoring
        Uses headful for auth, headless for monitoring
        """
        
        if requires_auth or self.credential_browser_platform == platform:
            # Use headful browser for authentication
            logger.info(f"Using headful browser for {platform} (auth required)")
            return self.headful_browser
        
        # Use headless browser for regular monitoring if enabled
        if self.settings.app_settings.headless_mode and platform in self.headless_pool:
            # Use headless browser for regular monitoring
            if not self.headless_pool[platform]:
                # Create new headless browser if needed
                browser_id = await self.launcher.launch_browser(headless=True)
                browser = BrowserInstance(
                    id=browser_id,
                    platform=platform,
                    headless=True,
                    created_at=datetime.now(),
                    last_used=datetime.now()
                )
                self.headless_pool[platform] = [browser]
            
            # Get least loaded browser
            browser = self._get_least_loaded_browser(self.headless_pool[platform])
            browser.last_used = datetime.now()
            return browser
        else:
            # Use headful browser if headless mode is disabled
            return self.headful_browser
    
    def _get_least_loaded_browser(self, browsers: List[BrowserInstance]) -> BrowserInstance:
        """Get browser with least active pages"""
        return min(browsers, key=lambda b: (b.page_count, b.request_count))
    
    async def route_to_headful_on_detection(self, platform: str, url: str):
        """
        Route to headful browser when tickets detected
        Provides visual feedback for manual intervention
        """
        
        console.print(f"[yellow]🎯 Routing {platform} to main browser for ticket purchase![/yellow]")
        
        # Switch to headful browser
        if self.headful_browser:
            context_id = await self.launcher.create_context(self.headful_browser.id)
            page = await self.launcher.new_page(context_id)
            
            # Navigate to ticket page
            await page.goto(url)
            
            # Bring window to front (platform-specific)
            await self._bring_browser_to_front(page)
            
            # Visual notification
            try:
                await page.evaluate("""
                    (() => {
                        // Add visual indicator
                        const banner = document.createElement('div');
                        banner.style.cssText = `
                            position: fixed;
                            top: 0;
                            left: 0;
                            right: 0;
                            background: linear-gradient(90deg, #4CAF50, #45a049);
                            color: white;
                            padding: 15px;
                            text-align: center;
                            font-size: 18px;
                            z-index: 999999;
                            animation: pulse 1s infinite;
                        `;
                        banner.textContent = '🎫 TICKETS DETECTED! Ready for purchase.';
                        document.body.appendChild(banner);
                        
                        // Add CSS animation
                        const style = document.createElement('style');
                        style.textContent = `
                            @keyframes pulse {
                                0% { opacity: 1; }
                                50% { opacity: 0.7; }
                                100% { opacity: 1; }
                            }
                        `;
                        document.head.appendChild(style);
                        
                        // Auto-remove after 10 seconds
                        setTimeout(() => banner.remove(), 10000);
                    })();
                """)
            except Exception as e:
                logger.error(f"Failed to add visual indicator: {e}")
            
            return page
    
    async def _bring_browser_to_front(self, page: Any):
        """Bring browser window to front (platform-specific)"""
        try:
            # Try to bring window to front using CDP
            await page.evaluate("window.focus()")
            
            # Additional platform-specific logic can be added here
            # For example, using AppleScript on macOS or Windows APIs
            
        except Exception as e:
            logger.debug(f"Could not bring window to front: {e}")
    
    async def health_check(self):
        """Check health of all browsers in pool"""
        unhealthy_browsers = []
        
        # Check headful browser
        if self.headful_browser:
            try:
                # Simple health check - try to create a new context
                test_context = await self.launcher.create_context(self.headful_browser.id)
                await self.launcher.close_context(test_context)
            except Exception as e:
                logger.error(f"Headful browser health check failed: {e}")
                unhealthy_browsers.append(('main', self.headful_browser))
        
        # Check headless browsers
        for platform, browsers in self.headless_pool.items():
            for browser in browsers:
                if browser.health_check_fails > 3:
                    unhealthy_browsers.append((platform, browser))
        
        # Replace unhealthy browsers
        for platform, browser in unhealthy_browsers:
            await self._replace_browser(platform, browser)
    
    async def _replace_browser(self, platform: str, old_browser: BrowserInstance):
        """Replace an unhealthy browser"""
        logger.warning(f"Replacing unhealthy browser for {platform}")
        
        try:
            # Close old browser
            await self.launcher.close_browser(old_browser.id)
        except:
            pass
        
        # Create new browser
        new_browser_id = await self.launcher.launch_browser(headless=old_browser.headless)
        new_browser = BrowserInstance(
            id=new_browser_id,
            platform=platform,
            headless=old_browser.headless,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        # Replace in appropriate pool
        if platform == "main":
            self.headful_browser = new_browser
        else:
            self.headless_pool[platform] = [b for b in self.headless_pool.get(platform, []) if b != old_browser]
            self.headless_pool[platform].append(new_browser)
    
    async def cleanup(self):
        """Clean up all browsers"""
        logger.info("Cleaning up browser pool")
        
        # Close headful browser
        if self.headful_browser:
            try:
                await self.launcher.close_browser(self.headful_browser.id)
            except Exception as e:
                logger.error(f"Error closing headful browser: {e}")
        
        # Close all headless browsers
        for platform, browsers in self.headless_pool.items():
            for browser in browsers:
                try:
                    await self.launcher.close_browser(browser.id)
                except Exception as e:
                    logger.error(f"Error closing browser for {platform}: {e}")
        
        self.headless_pool.clear()
        self.headful_browser = None
        self.initialized = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        total_browsers = 1 if self.headful_browser else 0  # headful
        total_browsers += sum(len(browsers) for browsers in self.headless_pool.values())
        
        return {
            'total_browsers': total_browsers,
            'headful_active': self.headful_browser is not None,
            'headless_per_platform': {
                platform: len(browsers) 
                for platform, browsers in self.headless_pool.items()
            },
            'total_requests': sum(
                browser.request_count 
                for browsers in self.headless_pool.values() 
                for browser in browsers
            )
        }
