"""Create Chrome extension for proxy authentication."""
import zipfile
import os
import tempfile
from pathlib import Path


def create_proxy_auth_extension(username: str, password: str, host: str, port: str) -> str:
    """
    Create a Chrome extension that handles proxy authentication.
    
    Returns:
        Path to the created extension zip file
    """
    # Create a temporary directory for the extension
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # manifest.json
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Extension",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        
        # Write manifest.json
        manifest_path = temp_path / "manifest.json"
        import json
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # background.js
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{host}",
                    port: parseInt({port})
                }},
                bypassList: ["localhost"]
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{username}",
                    password: "{password}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """
        
        # Write background.js
        background_path = temp_path / "background.js"
        with open(background_path, 'w') as f:
            f.write(background_js)
        
        # Create zip file
        extension_path = Path(tempfile.gettempdir()) / f"proxy_auth_{os.getpid()}.zip"
        with zipfile.ZipFile(extension_path, 'w') as zf:
            zf.write(manifest_path, "manifest.json")
            zf.write(background_path, "background.js")
        
        return str(extension_path)