#!/usr/bin/env python3
"""
Capture ticket HTML structure from Fansale
This will help us understand the exact structure
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

def capture_ticket_html():
    """Capture the HTML structure of tickets on Fansale"""
    
    email = os.getenv('FANSALE_EMAIL')
    password = os.getenv('FANSALE_PASSWORD')
    
    if not email or not password:
        print("ERROR: Missing FANSALE_EMAIL or FANSALE_PASSWORD in .env file!")
        return
    
    print("Starting ticket HTML capture...")
    
    # Create driver
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options)
    
    try:
        # Go directly to Bruce page
        bruce_url = "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"
        print(f"\nGoing to: {bruce_url}")
        driver.get(bruce_url)
        time.sleep(5)
        
        # Accept cookies if present
        try:
            cookie_btns = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Accetta')] | //button[contains(text(), 'Accept')] | //button[contains(@id, 'accept')]")
            for btn in cookie_btns:
                if btn.is_displayed():
                    btn.click()
                    print("Accepted cookies")
                    time.sleep(2)
                    break
        except:
            pass
        
        # Check if we need to login
        needs_login = False
        try:
            accedi_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Accedi')]")
            needs_login = len([a for a in accedi_links if a.is_displayed()]) > 0
        except:
            pass
        
        if needs_login:
            print("\nNeed to login first...")
            # Click Accedi
            for link in accedi_links:
                if link.is_displayed():
                    link.click()
                    break
            
            time.sleep(5)
            
            # Switch to iframe if present
            try:
                iframe = driver.find_element(By.CSS_SELECTOR, "iframe[src*='ticketone.it']")
                driver.switch_to.frame(iframe)
                print("Switched to login iframe")
            except:
                print("No iframe found")
            
            # Fill login
            try:
                username = driver.find_element(By.ID, "username")
                username.send_keys(email)
                
                password_field = driver.find_element(By.ID, "password")
                password_field.send_keys(password)
                
                login_btn = driver.find_element(By.ID, "loginCustomerButton")
                login_btn.click()
                print("Submitted login")
                
                # Switch back
                driver.switch_to.default_content()
                time.sleep(10)
                
                # Go back to Bruce page
                driver.get(bruce_url)
                time.sleep(5)
            except Exception as e:
                print(f"Login error: {e}")
        
        # Now capture ticket HTML
        print("\n" + "="*60)
        print("CAPTURING TICKET STRUCTURE")
        print("="*60)
        
        # Save full page HTML
        page_html = driver.page_source
        with open("fansale_tickets_page.html", "w", encoding="utf-8") as f:
            f.write(page_html)
        print("Saved full page HTML to: fansale_tickets_page.html")
        
        # Find elements with Euro symbol
        print("\nElements containing €:")
        euro_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
        print(f"Found {len(euro_elements)} elements with €")
        
        # Save first 10 euro elements
        with open("ticket_elements.txt", "w", encoding="utf-8") as f:
            for i, elem in enumerate(euro_elements[:10]):
                try:
                    # Get element HTML
                    outer_html = driver.execute_script("return arguments[0].outerHTML;", elem)
                    parent_html = driver.execute_script("return arguments[0].parentElement.outerHTML;", elem)
                    
                    f.write(f"\n{'='*60}\n")
                    f.write(f"ELEMENT {i+1}\n")
                    f.write(f"{'='*60}\n")
                    f.write(f"Text: {elem.text}\n")
                    f.write(f"Tag: {elem.tag_name}\n")
                    f.write(f"Class: {elem.get_attribute('class')}\n")
                    f.write(f"\nElement HTML:\n{outer_html}\n")
                    f.write(f"\nParent HTML:\n{parent_html[:500]}...\n")
                    
                    print(f"\nElement {i+1}:")
                    print(f"  Text: {elem.text[:100]}")
                    print(f"  Tag: {elem.tag_name}")
                    print(f"  Class: {elem.get_attribute('class')}")
                except:
                    pass
        
        print(f"\nSaved ticket elements to: ticket_elements.txt")
        
        # Look for common ticket patterns
        print("\nSearching for ticket containers...")
        ticket_selectors = [
            ".offer-item",
            ".ticket-item",
            "[class*='offer']",
            "[class*='ticket']",
            "[class*='listing']",
            ".listing-item",
            "[data-testid*='ticket']"
        ]
        
        for selector in ticket_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\nFound {len(elements)} elements with selector: {selector}")
                    # Save first element
                    if elements[0].is_displayed():
                        html = driver.execute_script("return arguments[0].outerHTML;", elements[0])
                        print(f"First element HTML preview: {html[:200]}...")
            except:
                pass
        
        # JavaScript analysis
        ticket_info = driver.execute_script("""
            // Find all clickable elements with prices
            const results = {
                clickableWithPrice: [],
                buttons: [],
                links: []
            };
            
            // Find clickable elements with €
            const allElements = document.querySelectorAll('*');
            for (const elem of allElements) {
                const text = elem.textContent || '';
                if (text.includes('€') && text.length < 500) {
                    const isClickable = elem.tagName === 'BUTTON' || 
                                      elem.tagName === 'A' || 
                                      elem.onclick || 
                                      elem.style.cursor === 'pointer' ||
                                      elem.classList.contains('clickable');
                    
                    if (isClickable) {
                        results.clickableWithPrice.push({
                            tag: elem.tagName,
                            class: elem.className,
                            text: text.substring(0, 100)
                        });
                    }
                }
            }
            
            // Find all buttons
            document.querySelectorAll('button').forEach(btn => {
                const text = btn.textContent || '';
                if (text.toLowerCase().includes('add') || 
                    text.toLowerCase().includes('cart') ||
                    text.toLowerCase().includes('aggiungi') ||
                    text.toLowerCase().includes('carrello')) {
                    results.buttons.push({
                        text: text,
                        class: btn.className,
                        id: btn.id
                    });
                }
            });
            
            // Find relevant links
            document.querySelectorAll('a').forEach(link => {
                const href = link.href || '';
                const text = link.textContent || '';
                if (href.includes('cart') || href.includes('add') || 
                    text.includes('€') || text.toLowerCase().includes('aggiungi')) {
                    results.links.push({
                        href: href,
                        text: text.substring(0, 100),
                        class: link.className
                    });
                }
            });
            
            return results;
        """)
        
        print("\nJavaScript Analysis:")
        print(f"Clickable elements with prices: {len(ticket_info['clickableWithPrice'])}")
        print(f"Add to cart buttons: {len(ticket_info['buttons'])}")
        print(f"Relevant links: {len(ticket_info['links'])}")
        
        # Save JavaScript analysis
        import json
        with open("ticket_analysis.json", "w", encoding="utf-8") as f:
            json.dump(ticket_info, f, indent=2, ensure_ascii=False)
        print("\nSaved analysis to: ticket_analysis.json")
        
        print("\n" + "="*60)
        print("CAPTURE COMPLETE")
        print("="*60)
        print("\nFiles created:")
        print("1. fansale_tickets_page.html - Full page HTML")
        print("2. ticket_elements.txt - Elements containing €")
        print("3. ticket_analysis.json - JavaScript analysis of clickable elements")
        print("\nAnalyze these files to understand the ticket structure!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    capture_ticket_html()