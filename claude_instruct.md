# Project Directive: Fansale High-Performance Ticket Bot v3.0 (Analysis-Driven)

## 1. Your Persona & Mission

**Your Persona:** You are a senior-level automation engineer. Your expertise is in writing Python code that is not only functional but also exceptionally fast, memory-efficient, and resilient. You think in terms of selectors, state management, and robust error handling. You write clean, commented code and prioritize simplicity and performance over complex, unnecessary abstractions.

**Your Mission:** To re-engineer this project into a specialized, high-performance bot for the Fansale.it platform. The singular goal is to monitor a specific event page and execute a successful ticket reservation the instant an offer appears. Every line of code you write must serve this mission directly.

## 2. Project Analysis & Strategic Vision

My analysis of the existing codebase reveals the following:

* **Strengths:**
    * **Excellent Foundation in Stealth:** The project correctly uses `nodriver` and has a dedicated `src/stealth` module. This focus on anti-detection is a core asset we must preserve and leverage.
    * **Modular Structure:** The code is broken into components (`platforms`, `utils`, `network`), which is a good architectural starting point.

* **Weaknesses (Our Primary Targets for Improvement):**
    * **Over-Complexity & Fragmentation:** The main issue is a scattered and confusing structure. Logic is split between a root-level `stealthmaster.py`, `src/main.py`, and `src/platforms/fansale.py`. There are multiple, conflicting entry points (`run.sh` vs. `run_stealth.sh`), making it difficult to understand the execution flow.
    * **Lack of a Central Orchestrator:** There is no single class that manages the bot's state (like the browser instance) and lifecycle. This leads to redundant code and makes the system hard to reason about.
    * **Configuration Sprawl:** Configuration is handled by both `config.yaml` and `.env` files, which is unnecessary.

**Our Strategic Vision:** We will refactor the project around a single, powerful `FansaleBot` class located in `src/platforms/fansale.py`. This class will orchestrate the entire process. `src/main.py` will become the sole, unambiguous entry point to the application. We will absorb all useful logic from scattered scripts like `stealthmaster.py` and the various `analyze_*.py` files into this central class and then discard the originals to drastically simplify the project.

## 3. The Unbreakable Rules of Engagement

1.  **Technology Lock-In:** This project uses `nodriver`. All browser interaction **must** be implemented using `nodriver` and its asynchronous (`async`/`await`) capabilities.
2.  **Simplify and Consolidate:** Aggressively refactor scattered logic into the central `FansaleBot` class. If a file or function does not serve the new, streamlined architecture, it must be removed.
3.  **Preserve the `src` Structure:** Do **not** change the existing filenames *within* the `src` subdirectories unless explicitly told to. However, redundant files in the root directory will be eliminated.
4.  **Configuration from `.env` Only:** The `.env` file is the single source of truth. All `yaml`-based configuration must be removed.
5.  **Performance is Paramount:** Optimize for speed and minimal data usage by blocking non-essential network resources.

---

## 4. The Execution Blueprint: A Step-by-Step Tactical Plan

### **Task 1: Foundational Refactoring & Consolidation**

**Objective:** To unify the project's scattered logic into a clean, single-entry-point application.

* **Step 1.1: Standardize Dependencies**: In `requirements.txt`, ensure `nodriver`, `python-dotenv`, and `asyncio` are present. Remove `PyYAML`.
* **Step 1.2: Unify Configuration (`src/config.py`)**:
    * Rewrite the `AppConfig` class to load all variables *only* from the `.env` file using `os.getenv()`. Remove all YAML logic.
* **Step 1.3: Define the Sole Entry Point (`src/main.py`)**:
    * This file becomes the master launcher.
    * Its only purpose is to import `asyncio`, import the (not-yet-implemented) `FansaleBot`, create an instance, and run it within a `try/except` block for clean shutdown.
        ```python
        # src/main.py
        import asyncio
        from src.platforms.fansale import FansaleBot
        import logging

        if __name__ == "__main__":
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            bot = FansaleBot()
            try:
                asyncio.run(bot.run())
            except KeyboardInterrupt:
                logging.info("Bot shutting down manually.")
            except Exception as e:
                logging.critical(f"A critical error forced shutdown: {e}", exc_info=True)
        ```
* **Step 1.4: Decommission Redundant Scripts**:
    * Delete the root-level scripts: `stealthmaster.py`, `stealthmaster_backup.py`, `analyze_fansale_advanced.py`, `analyze_fansale_javascript.py`, and `capture_tickets.py`. We are committing to the new, clean structure.

* **Step 1.5: Structure the Central Orchestrator (`src/platforms/fansale.py`)**:
    * Clear the existing file content. This is a fresh start.
    * Create the `FansaleBot` class with method stubs. This structure will be the new heart of the application.
        ```python
        # src/platforms/fansale.py
        import nodriver as uc
        import asyncio
        import random
        import logging
        from src.config import AppConfig

        class FansaleBot:
            def __init__(self):
                self.config = AppConfig()
                self.page = None
                self.browser = None
                self.target_url = "[https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388](https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388)"
                self.login_url = "[https://www.fansale.it/fansale/login.htm](https://www.fansale.it/fansale/login.htm)"

            async def run(self): pass
            async def _setup_browser(self): pass
            async def _handle_login(self): pass
            async def _monitor_loop(self): pass
            async def _attempt_purchase(self, ticket_offer_element): pass
            async def _shutdown(self): pass
        ```

### **Task 2: Core Bot Logic Implementation**

**Objective:** To implement the bot's functionality within the new, clean `FansaleBot` structure.

* **Step 2.1: Implement `_setup_browser`**:
    * Initialize `nodriver`. Look at the logic in the old `stealthmaster.py` for inspiration on proxy setup, but implement it here.
        ```python
        # Example proxy setup within _setup_browser
        proxy_server = f"http://{self.config.iproxy_username}:{self.config.iproxy_password}@{self.config.iproxy_hostname}:{self.config.iproxy_port}"
        self.browser = await uc.start(browser_args=[f'--proxy-server={proxy_server}'])
        self.page = await self.browser.get(self.login_url)
        ```
    * **Crucial:** Implement resource blocking to maximize speed and minimize data usage.
    * Log "INFO: Browser setup complete. Resource blocking enabled."

* **Step 2.2: Implement `_handle_login` (Hyper-Detailed)**:
    1.  Log "INFO: Navigating to login page." and navigate to `self.login_url`.
    2.  **Cookie Banner:** Find and click `text='ACCETTA TUTTI I COOKIE'`. Use a `timeout` and handle cases where it might not appear.
    3.  **Credentials:** Find fields by `[data-qa="loginEmail"]` and `[data-qa="loginPassword"]`. Fill them.
    4.  **Submit:** Click the button with `[data-qa="loginSubmit"]`.
    5.  **Verification:** Wait for navigation. A robust check is to look for an element that confirms login, such as `[data-qa="user-logout"]`. If not found after a 15-second timeout, log a critical failure and return `False`. Otherwise, log success and return `True`.

* **Step 2.3: Implement `_monitor_loop` (The Heart of the Bot)**:
    1.  Log "INFO: Starting ticket monitoring loop."
    2.  In a `while True:` loop:
    3.  Navigate to `self.target_url`.
    4.  **Primary Check (No Tickets):** Check for `text='Sfortunatamente non sono state trovate offerte adeguate'`. If found, log this and continue the loop after a randomized delay (`asyncio.sleep(random.uniform(1.5, 2.5))`).
    5.  **Secondary Check (Tickets Found!):** If the "no offers" text is *not* found (it will time out), immediately search for `div[data-qa="ticketToBuy"]`.
    6.  If a ticket offer is found, log "SUCCESS: TICKET OFFER DETECTED!" and immediately call `await self._attempt_purchase(ticket_offer)`. Then `break` the loop.

* **Step 2.4: Implement `_attempt_purchase` (The Final Action)**:
    1.  Within the received `ticket_offer_element`, find and click the details link using the stable class `a.js-Button-inOfferEntryList`.
    2.  After the page navigates, wait for and click the final reservation button. Use the selector `[data-qa="buyNowButton"]`.
    3.  Log "SUCCESS: FINAL RESERVATION BUTTON CLICKED!"

* **Step 2.5: Implement `run` and `_shutdown`**:
    * The `run` method orchestrates the entire lifecycle: call `_setup_browser`, then `_handle_login`, then `_monitor_loop`, and finally `_shutdown` in a `finally` block to ensure the browser always closes.
    * The `_shutdown` method should simply call `await self.browser.close()`.

### **Task 3: Performance & Reliability Benchmarking**

**Objective:** To create a standalone `benchmark.py` script to quantitatively measure the bot's performance.

* **Detailed Steps:**
    1.  Create `benchmark.py`.
    2.  Implement `test_login_speed`.
    3.  Implement `test_detection_speed` (using a local HTML file for reliability).
    4.  Implement `test_end_to_end_purchase_speed` (using a local HTML file).
    5.  The script **must** perform real measurements and write the results to `benchmark_results.md`. **Do not invent results.**
