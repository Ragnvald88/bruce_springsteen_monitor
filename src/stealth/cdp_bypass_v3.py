"""
Modern CDP Bypass Implementation - Intercepts and modifies Chrome DevTools Protocol
to prevent detection at the protocol level.
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Optional, Set, Callable
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class CDPMessage:
    """Represents a CDP message"""
    id: Optional[int]
    method: Optional[str]
    params: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    
    @classmethod
    def from_json(cls, data: str) -> 'CDPMessage':
        """Parse CDP message from JSON"""
        parsed = json.loads(data)
        return cls(
            id=parsed.get('id'),
            method=parsed.get('method'),
            params=parsed.get('params', {}),
            result=parsed.get('result'),
            error=parsed.get('error')
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        data = {}
        if self.id is not None:
            data['id'] = self.id
        if self.method:
            data['method'] = self.method
        if self.params:
            data['params'] = self.params
        if self.result is not None:
            data['result'] = self.result
        if self.error:
            data['error'] = self.error
        return json.dumps(data)


class CDPInterceptor:
    """
    Intercepts and modifies CDP messages to prevent detection.
    Acts as a proxy between Playwright and Chrome.
    """
    
    def __init__(self):
        """Initialize CDP interceptor"""
        self._browser_ws: Optional[websockets.WebSocketClientProtocol] = None
        self._client_ws: Optional[websockets.WebSocketServerProtocol] = None
        self._intercepted_methods: Set[str] = set()
        self._message_handlers: Dict[str, Callable] = {}
        self._runtime_enabled = False
        self._console_api_enabled = False
        
        # Methods that expose automation
        self._blocked_methods = {
            'Runtime.enable',  # Causes CDP detection
            'Runtime.addBinding',  # Exposes bindings
            'Page.addScriptToEvaluateOnNewDocument',  # Can be detected
        }
        
        # Methods to modify
        self._setup_handlers()
        
        logger.info("CDP Interceptor initialized")
    
    def _setup_handlers(self):
        """Setup message modification handlers"""
        # Runtime domain handlers
        self._message_handlers['Runtime.evaluate'] = self._handle_runtime_evaluate
        self._message_handlers['Runtime.callFunctionOn'] = self._handle_runtime_call
        self._message_handlers['Page.createIsolatedWorld'] = self._handle_create_world
        self._message_handlers['Target.createTarget'] = self._handle_create_target
        
    async def start_proxy(self, browser_ws_url: str, listen_port: int = 9223):
        """
        Start CDP proxy server
        
        Args:
            browser_ws_url: Original browser WebSocket URL
            listen_port: Port to listen on for client connections
        """
        # Connect to real browser
        self._browser_ws = await websockets.connect(browser_ws_url)
        
        # Start proxy server
        async def handle_client(websocket, path):
            self._client_ws = websocket
            await self._proxy_messages()
        
        server = await websockets.serve(handle_client, 'localhost', listen_port)
        
        # Replace browser WS URL
        proxy_url = f"ws://localhost:{listen_port}"
        logger.info(f"CDP proxy started: {browser_ws_url} -> {proxy_url}")
        
        return proxy_url, server
    
    async def _proxy_messages(self):
        """Proxy messages between client and browser"""
        try:
            # Handle messages in both directions
            await asyncio.gather(
                self._handle_client_to_browser(),
                self._handle_browser_to_client(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Proxy error: {e}")
        finally:
            await self._cleanup()
    
    async def _handle_client_to_browser(self):
        """Handle messages from client (Playwright) to browser"""
        async for message in self._client_ws:
            try:
                cdp_msg = CDPMessage.from_json(message)
                
                # Check if method should be blocked
                if cdp_msg.method in self._blocked_methods:
                    logger.debug(f"Blocking method: {cdp_msg.method}")
                    # Send fake success response
                    if cdp_msg.id:
                        fake_response = CDPMessage(
                            id=cdp_msg.id,
                            result={},
                            method=None,
                            params=None,
                            error=None
                        )
                        await self._client_ws.send(fake_response.to_json())
                    continue
                
                # Apply modifications
                modified_msg = await self._modify_outgoing(cdp_msg)
                
                # Forward to browser
                await self._browser_ws.send(modified_msg.to_json())
                
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
    
    async def _handle_browser_to_client(self):
        """Handle messages from browser to client"""
        async for message in self._browser_ws:
            try:
                cdp_msg = CDPMessage.from_json(message)
                
                # Apply modifications
                modified_msg = await self._modify_incoming(cdp_msg)
                
                # Forward to client
                await self._client_ws.send(modified_msg.to_json())
                
            except Exception as e:
                logger.error(f"Error handling browser message: {e}")
    
    async def _modify_outgoing(self, msg: CDPMessage) -> CDPMessage:
        """Modify outgoing messages to browser"""
        if not msg.method:
            return msg
        
        # Handle specific methods
        if msg.method in self._message_handlers:
            return await self._message_handlers[msg.method](msg)
        
        # Default modifications
        if msg.method == 'Page.navigate':
            # Add stealth headers
            if not msg.params.get('headers'):
                msg.params['headers'] = {}
            msg.params['headers'].update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            })
        
        return msg
    
    async def _modify_incoming(self, msg: CDPMessage) -> CDPMessage:
        """Modify incoming messages from browser"""
        # Remove CDP artifacts from console
        if msg.method == 'Runtime.consoleAPICalled':
            if msg.params and 'args' in msg.params:
                # Filter out CDP-related console messages
                args = msg.params['args']
                if any('CDP' in str(arg.get('value', '')) for arg in args):
                    # Don't forward CDP-related console messages
                    return None
        
        return msg
    
    async def _handle_runtime_evaluate(self, msg: CDPMessage) -> CDPMessage:
        """Handle Runtime.evaluate to inject stealth code"""
        if msg.params and 'expression' in msg.params:
            expression = msg.params['expression']
            
            # Inject stealth code before user expression
            stealth_injection = """
            // Stealth injection
            (() => {
                // Remove webdriver completely
                delete Object.getPrototypeOf(navigator).webdriver;
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: false
                });
                
                // Fix chrome.runtime
                if (!window.chrome) window.chrome = {};
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {
                        connect: () => { throw new Error('Extension context invalidated.'); },
                        sendMessage: () => { throw new Error('Extension context invalidated.'); },
                        id: undefined,
                        onMessage: { addListener: () => {} }
                    };
                }
                
                // Remove CDP artifacts
                const cdpProps = Object.getOwnPropertyNames(window).filter(n => n.includes('cdc'));
                cdpProps.forEach(prop => delete window[prop]);
            })();
            """
            
            # Prepend stealth code
            msg.params['expression'] = stealth_injection + '\n' + expression
        
        return msg
    
    async def _handle_runtime_call(self, msg: CDPMessage) -> CDPMessage:
        """Handle Runtime.callFunctionOn"""
        # Similar to evaluate, inject stealth code
        return msg
    
    async def _handle_create_world(self, msg: CDPMessage) -> CDPMessage:
        """Handle isolated world creation"""
        # Ensure our stealth code runs in isolated worlds too
        if msg.params and not msg.params.get('worldName', '').startswith('__stealth'):
            # Create our own isolated world first
            stealth_world = CDPMessage(
                id=None,  # Will be assigned by system
                method='Page.createIsolatedWorld',
                params={
                    'frameId': msg.params.get('frameId'),
                    'worldName': '__stealth_world',
                    'grantUniveralAccess': True
                },
                result=None,
                error=None
            )
            await self._browser_ws.send(stealth_world.to_json())
        
        return msg
    
    async def _handle_create_target(self, msg: CDPMessage) -> CDPMessage:
        """Handle new target creation"""
        # Add stealth parameters to new targets
        if msg.params:
            if not msg.params.get('browserContextId'):
                # Add our stealth context
                msg.params['browserContextId'] = '__stealth_context'
        
        return msg
    
    async def _cleanup(self):
        """Cleanup connections"""
        if self._browser_ws:
            await self._browser_ws.close()
        if self._client_ws:
            await self._client_ws.close()