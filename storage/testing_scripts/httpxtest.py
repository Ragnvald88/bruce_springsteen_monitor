# test_httpx_mounts.py
import httpx
import asyncio
import logging
import os
import sys
from pathlib import Path # For .env loading

# Import AsyncHTTPProxy from httpcore, which httpx uses
from httpcore import AsyncHTTPProxy, ProxyError # Added ProxyError for more specific exception handling

# Setup basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("test_httpx_mounts")

def direct_print(msg):
    print(f"DIRECT_PRINT: {msg}", file=sys.stderr, flush=True)

async def main():
    direct_print("Minimal test script (using mounts) started.")
    logger.info("Minimal test script logger (using mounts) started.")

    try:
        logger.info(f"httpx library version: {httpx.__version__}")
        direct_print(f"httpx library version: {httpx.__version__}")
    except Exception as e:
        direct_print(f"Failed to get httpx version or import httpx: {e}")
        logger.error(f"Failed to get httpx version or import httpx: {e}", exc_info=True)
        return

    # --- Get proxy details (same as before) ---
    try:
        from dotenv import load_dotenv
        # Look for .env in the script's directory or parent (project root)
        script_dir = Path(__file__).resolve().parent
        dotenv_paths = [script_dir / '.env', script_dir.parent / '.env']
        loaded_dotenv = False
        for p in dotenv_paths:
            if p.exists():
                if load_dotenv(dotenv_path=p, override=True):
                    direct_print(f"Loaded .env file from: {p}")
                    loaded_dotenv = True
                    break
        if not loaded_dotenv:
            direct_print("No .env file found in script or parent directory. Relying on pre-set environment variables.")
    except ImportError:
        direct_print("python-dotenv is not installed. Relying on pre-set environment variables.")

    host_str = os.environ.get('IPROYAL_HOSTNAME', '')
    port_str = os.environ.get('IPROYAL_PORT', '')
    username_str = os.environ.get('IPROYAL_USERNAME', '')
    password_str = os.environ.get('IPROYAL_PASSWORD', '')
    proxy_type_scheme = "http" # Proxy scheme, e.g., http or https for the proxy server itself

    if not host_str or not port_str:
        logger.warning("IPROYAL_HOSTNAME or IPROYAL_PORT not found. Test will use a dummy proxy URL.")
        direct_print("IPROYAL_HOSTNAME or IPROYAL_PORT not found. Using dummy proxy URL.")
        # For AsyncHTTPProxy, we need scheme, host, port separately. Auth is a tuple.
        proxy_url_bytes = b"http://example.com:1234" # httpcore expects bytes for URL
        proxy_auth_tuple = ('dummyuser', 'dummypass')
    else:
        proxy_auth_tuple = (username_str.encode('utf-8'), password_str.encode('utf-8')) if username_str and password_str else None
        # httpcore.AsyncHTTPProxy expects the proxy_url as bytes
        proxy_url_bytes = f"{proxy_type_scheme}://{host_str}:{port_str}".encode('utf-8')

    logger.info(f"Proxy details for transport: URL (bytes)='{proxy_url_bytes}', Auth provided: {bool(proxy_auth_tuple)}")
    direct_print(f"Proxy details for transport: URL (bytes)='{proxy_url_bytes}', Auth provided: {bool(proxy_auth_tuple)}")
    # --- End proxy detail section ---

    proxy_transport = None
    try:
        proxy_transport = AsyncHTTPProxy(
            proxy_url=proxy_url_bytes,
            proxy_auth=proxy_auth_tuple,
            # You might need other httpcore.AsyncHTTPProxy args like `ssl_context` if proxy uses HTTPS
            # or `proxy_mode` for forward vs tunnel if dealing with HTTPS targets explicitly.
            # Default mode usually handles HTTPS targets via HTTP CONNECT tunnel.
        )
        mounts_dict = {"all://": proxy_transport}
        logger.info(f"Attempting to create httpx.AsyncClient with mounts: {mounts_dict}")
        direct_print(f"Attempting to create httpx.AsyncClient with mounts: {mounts_dict}")
    except Exception as e_transport:
        logger.error(f"TEST FAILED - Error creating AsyncHTTPProxy transport: {e_transport}", exc_info=True)
        direct_print(f"TEST FAILED - Error creating AsyncHTTPProxy transport: {e_transport}")
        return

    client = None
    try:
        client = httpx.AsyncClient(
            mounts=mounts_dict,
            timeout=30 # Increased timeout for proxy requests
        )
        logger.info("SUCCESS: httpx.AsyncClient created successfully with 'mounts' argument.")
        direct_print("SUCCESS: httpx.AsyncClient created successfully with 'mounts' argument.")

        logger.info("Attempting to make a GET request to https://httpbin.org/ip via proxy (using mounts)...")
        direct_print("Attempting to make a GET request to https://httpbin.org/ip via proxy (using mounts)...")
        async with client: # Use client as a context manager for requests
            response = await client.get("https://httpbin.org/ip")
            logger.info(f"Response status: {response.status_code}")
            direct_print(f"Response status: {response.status_code}")
            logger.info(f"Response content (your IP via proxy): {response.json()}")
            direct_print(f"Response content (your IP via proxy): {response.json()}")

    except ProxyError as pe: # More specific error for proxy issues with httpcore
        logger.error(f"TEST FAILED - ProxyError with mounts: {pe}", exc_info=True)
        direct_print(f"TEST FAILED - ProxyError with mounts: {pe}")
    except httpx.HTTPStatusError as hse:
        logger.error(f"TEST FAILED - HTTPStatusError with mounts (status: {hse.response.status_code}): {hse}", exc_info=True)
        direct_print(f"TEST FAILED - HTTPStatusError with mounts (status: {hse.response.status_code}): {hse}")
    except httpx.RequestError as re: # General httpx request errors (timeout, connection error etc.)
        logger.error(f"TEST FAILED - httpx.RequestError with mounts: {re}", exc_info=True)
        direct_print(f"TEST FAILED - httpx.RequestError with mounts: {re}")
    except TypeError as te: 
        logger.error(f"TEST FAILED - Unexpected TypeError with mounts: {te}", exc_info=True)
        direct_print(f"TEST FAILED - Unexpected TypeError with mounts: {te}")
    except Exception as e:
        logger.error(f"TEST FAILED - Other error with mounts: {e}", exc_info=True)
        direct_print(f"TEST FAILED - Other error with mounts: {e}")
    # No finally block to close client as it's handled by 'async with client:'

if __name__ == "__main__":
    direct_print("Script __main__ (mounts test) entered.")
    asyncio.run(main())
    direct_print("Script __main__ (mounts test) finished.")