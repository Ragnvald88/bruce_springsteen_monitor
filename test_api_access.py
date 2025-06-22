import os
import time
from pathlib import Path
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# Load environment
load_dotenv()

def test_api_methods():
    """Test different methods to access the FanSale API"""
    
    print("🧪 FanSale API Access Tester\n")
    
    # Setup browser
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    profile_dir = Path("browser_profiles") / "fansale_test"
    options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
    
    driver = uc.Chrome(options=options)
    
    try:
        # Navigate to login
        print("1️⃣ Please login manually...")
        driver.get("https://www.fansale.it/fansale/login.htm")
        input("Press Enter after logging in...")
        
        # Navigate to target page
        print("\n2️⃣ Navigating to ticket page...")
        target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        driver.get(target_url)
        time.sleep(2)
        
        # Test different API access methods
        print("\n3️⃣ Testing API access methods...\n")
        
        # Method 1: Fetch with all headers
        print("Testing Method 1: Fetch with full headers...")
        result1 = driver.execute_script("""
            async function testFetch() {
                try {
                    const response = await fetch('https://www.fansale.it/json/offers/17844388', {
                        method: 'GET',
                        credentials: 'include',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Referer': window.location.href,
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'same-origin'
                        }
                    });
                    
                    return {
                        success: true,
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries())
                    };
                } catch (error) {
                    return {success: false, error: error.message};
                }
            }
            
            return await testFetch();
        """)
        print(f"Result: {result1}\n")
        
        # Method 2: XMLHttpRequest
        print("Testing Method 2: XMLHttpRequest...")
        result2 = driver.execute_script("""
            function testXHR() {
                return new Promise((resolve) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('GET', 'https://www.fansale.it/json/offers/17844388', true);
                    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                    xhr.withCredentials = true;
                    
                    xhr.onload = function() {
                        resolve({
                            success: true,
                            status: xhr.status,
                            statusText: xhr.statusText,
                            responseHeaders: xhr.getAllResponseHeaders()
                        });
                    };
                    
                    xhr.onerror = function() {
                        resolve({success: false, error: 'Network error'});
                    };
                    
                    xhr.send();
                });
            }
            
            return testXHR();
        """)
        print(f"Result: {result2}\n")
        
        # Method 3: Look for existing API calls
        print("Testing Method 3: Intercepting existing API calls...")
        driver.execute_script("""
            // Override fetch to log calls
            const originalFetch = window.fetch;
            window.fetchCalls = [];
            
            window.fetch = function(...args) {
                window.fetchCalls.push({url: args[0], options: args[1]});
                return originalFetch.apply(this, args);
            };
            
            // Override XMLHttpRequest
            const originalXHROpen = XMLHttpRequest.prototype.open;
            window.xhrCalls = [];
            
            XMLHttpRequest.prototype.open = function(method, url, ...args) {
                window.xhrCalls.push({method, url});
                return originalXHROpen.apply(this, [method, url, ...args]);
            };
            
            console.log('API interception enabled');
        """)
        
        print("Refresh the page and wait for any API calls...")
        driver.refresh()
        time.sleep(5)
        
        # Check intercepted calls
        api_calls = driver.execute_script("""
            return {
                fetchCalls: window.fetchCalls || [],
                xhrCalls: window.xhrCalls || []
            };
        """)
        
        print(f"\nIntercepted API calls:")
        print(f"Fetch calls: {len(api_calls['fetchCalls'])}")
        for call in api_calls['fetchCalls'][:3]:
            print(f"  - {call['url']}")
        
        print(f"\nXHR calls: {len(api_calls['xhrCalls'])}")
        for call in api_calls['xhrCalls'][:3]:
            print(f"  - {call['method']} {call['url']}")
        
        # Extract any tokens
        print("\n4️⃣ Looking for authentication tokens...")
        tokens = driver.execute_script("""
            return {
                cookies: document.cookie,
                meta_csrf: document.querySelector('meta[name="csrf-token"]')?.content,
                input_token: document.querySelector('input[name*="token"]')?.value,
                localStorage: Object.keys(localStorage).reduce((obj, key) => {
                    obj[key] = localStorage.getItem(key);
                    return obj;
                }, {}),
                sessionStorage: Object.keys(sessionStorage).reduce((obj, key) => {
                    obj[key] = sessionStorage.getItem(key);
                    return obj;
                }, {})
            };
        """)
        
        print(f"Cookies: {bool(tokens['cookies'])}")
        print(f"CSRF Token (meta): {bool(tokens['meta_csrf'])}")
        print(f"CSRF Token (input): {bool(tokens['input_token'])}")
        print(f"LocalStorage items: {len(tokens['localStorage'])}")
        print(f"SessionStorage items: {len(tokens['sessionStorage'])}")
        
        print("\n✅ Test complete! Check the results above.")
        input("\nPress Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_api_methods()
