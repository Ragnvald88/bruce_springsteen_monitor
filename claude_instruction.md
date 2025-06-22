<master_prompt>

<persona>
You are an expert-level Senior Software Engineer specializing in Python, automation, and building resilient, high-performance web bots. Your task is to refactor and radically enhance a Python Selenium project called "StealthMaster". You are meticulous, security-conscious, and you write clean, efficient, and well-documented code.
</persona>

<project_context>
The user has a Python project for a ticketing bot. The goal is to monitor a specific page on Fansale.it and automatically reserve tickets as soon as they become available.

The project is currently in a messy state:
1.  There is a simple, monolithic script called `stealthmaster.py`.
2.  There is also a highly complex, over-engineered framework in a `src/` directory.
3.  The user feels overwhelmed and wants to combine the power of the `src` framework with the simplicity of a single-script approach.

Our mission is to create a new, vastly improved `stealthmaster.py` from scratch, incorporating the best ideas from the `src` directory and adding many new features that are essential for a modern, effective bot. We will then delete all the old, redundant files.

**Key Files for Your Analysis:**
- `stealthmaster.py`: The user's original simple script.
- `config.yaml`: The user's configuration file.
- `src/stealth/nodriver_core.py`: Contains advanced logic for creating a stealthy browser driver.
- `src/utils/proxy_auth_extension.py`: Contains the critical logic for creating a proxy authentication extension.
- `src/network/session.py`: Contains logic for session persistence (saving/loading cookies).
- `.env` file: Contains credentials for Fansale, proxies, 2Captcha, and notifications.
</project_context>

<core_principles>
1.  **Simplicity & Maintainability:** The final project must be easy to understand. The core logic will reside in a single `stealthmaster.py` file, supported by a few new files for clarity where necessary (e.g., `notifications.py`).
2.  **Robustness & Resilience:** The bot must handle errors gracefully. It needs to recover from network issues, site layout changes, and login failures without crashing.
3.  **Efficiency (Speed & Data):** The bot must be fast. Every millisecond counts. It must also be mindful of data usage, especially when using metered proxies. This means aggressively blocking unnecessary network requests.
4.  **Stealth:** The bot must be as undetectable as possible, using advanced techniques to mimic a human user.
5.  **Do Not Change `stealthmaster.py` Filename:** The main script must always be `stealthmaster.py`.
</core_principles>

<final_architecture>
The final project structure should be clean and simple:
/
|-- stealthmaster.py  # The main bot script
|-- notifications.py  # A new file for handling notifications
|-- captcha_solver.py # A new file for 2Captcha logic
|-- config.yaml       # User configuration
|-- .env              # User secrets
|-- requirements.txt  # A new file listing all dependencies
|-- README.md         # A new, comprehensive README file
|-- logs/             # Directory for log files
|-- session/          # Directory to store session cookies
</final_architecture>

<instructions>

### **Phase 1: Foundation and Project Setup**

**Goal:** Lay a clean, professional foundation for the new bot.

* **Step 1.1: Create `requirements.txt`**
    Based on your analysis of the project and the features we will be adding (Selenium, undetected-chromedriver, PyYAML, python-dotenv, requests, 2captcha-python, python-telegram-bot), create a `requirements.txt` file.

* **Step 1.2: Create the Main Script `stealthmaster.py`**
    Create a new `stealthmaster.py` file. Gut all old content. Set up the basic structure with necessary imports, logging configuration (logging to both console and a file in `logs/`), and a main `StealthMaster` class. The logger should be highly detailed.

* **Step 1.3: Implement Configuration and State Management**
    In `stealthmaster.py`, implement a `load_config` function that safely loads and validates `config.yaml`. Inside the `StealthMaster` class, create a Python `Enum` for state management. The bot can be in states like `INITIALIZING`, `LOGGING_IN`, `MONITORING`, `RESERVING`, `BLOCKED`, `SOLVING_CAPTCHA`.

### **Phase 2: Advanced Driver, Stealth, and Efficiency**

**Goal:** Build the core of the bot's stealth and performance capabilities.

* **Step 2.1: Implement Advanced Driver Creation**
    In `stealthmaster.py`, implement the `create_driver` method. This is critical.
    -   It must use `undetected_chromedriver`.
    -   **Proxy Logic:** Port the logic from `src/utils/proxy_auth_extension.py` to create the dynamic proxy authentication extension. This is non-negotiable.
    -   **Resource Blocking:** Implement logic to block unnecessary resources. Use the `driver.set_blocked_urls` feature of `uc` to block images, fonts, tracking scripts, and CSS files to maximize speed and minimize data usage.
    -   **Stealth Options:** Add all necessary Chrome options and execute CDP scripts to hide `navigator.webdriver` and other bot tells.

* **Step 2.2: Implement Session Persistence**
    Create a method `save_session()` that saves the current browser cookies to a file in the `session/` directory. Create a corresponding `load_session()` method that loads cookies from the file and adds them to the driver. This will help maintain login status between runs and after crashes. The `create_driver` method should call `load_session()` if a session file exists.

### **Phase 3: Bot Workflow and Logic**

**Goal:** Implement the primary functions of the bot for interacting with Fansale.

* **Step 3.1: Implement a Robust Login Flow**
    Create a `login()` method. It must be highly resilient.
    -   It must correctly handle the `ticketone.it` iframe on the Fansale login page.
    -   It should have clear waits (`WebDriverWait`) for each element.
    -   After a successful login, it should call `save_session()` to persist the new login cookies.
    -   It must have robust error handling to detect if the login failed (e.g., wrong password).

* **Step 3.2: Implement the Core Monitoring Loop**
    In the `run()` method, create the main state-driven loop.
    -   The loop will continuously check the bot's current state.
    -   If on the target page, it should call `find_and_reserve_tickets()`.
    -   It must periodically check if the bot is still logged in using an `is_logged_in()` method. If not, it should change the state to `LOGGING_IN`.
    -   It must check if the bot has been blocked or redirected, and handle these cases gracefully.

* **Step 3.3: Implement Ticket Reservation Logic**
    Create the `find_and_reserve_tickets()` method.
    -   It must use a fast and specific CSS selector (`.offer-item:not(.offer-item-sold)`) to find available tickets.
    -   If a ticket is found, it should immediately change state to `RESERVING`.
    -   It will then click the ticket, navigate to the details page, and click the "add to cart" button (`Aggiungi al carrello`).
    -   Upon success, it should trigger a notification.

### **Phase 4: Enhancements and Resilience**

**Goal:** Add advanced features that make the bot truly powerful.

* **Step 4.1: Create `notifications.py`**
    Create a new file, `notifications.py`. Inside, create a `Notifier` class.
    -   Implement a `send_telegram_message()` method that reads the bot token and chat ID from the `.env` file and sends a message.
    -   Add placeholder methods for other services like Pushover if you wish.
    -   In `stealthmaster.py`, import this class and call it upon successful ticket reservation or critical errors.

* **Step 4.2: Create `captcha_solver.py`**
    Create a new file, `captcha_solver.py`. Create a `CaptchaSolver` class.
    -   It must read the `2CAPTCHA_API_KEY` from the `.env` file.
    -   Implement a method `solve_recaptcha()` that can be called when a CAPTCHA is detected on the page. It will find the site key and page URL and submit them to the 2Captcha service.
    -   In `stealthmaster.py`, add logic to detect a CAPTCHA. If found, change state to `SOLVING_CAPTCHA` and call this new module.

* **Step 4.3: Implement Adaptive Delays**
    In the main loop of `stealthmaster.py`, enhance the `time.sleep()` logic. Instead of a fixed delay, use an adaptive delay. If checks are failing or errors occur, the delay should increase. If everything is running smoothly, it can remain short.

### **Phase 5: Documentation and Final Cleanup**

**Goal:** Finalize the project and make it easy for the user to understand and run.

* **Step 5.1: Create a `README.md` File**
    Generate a comprehensive `README.md` file for the project. It should include:
    -   A brief description of the project.
    -   Instructions on how to set up the `.env` file.
    -   How to install dependencies using `pip install -r requirements.txt`.
    -   How to run the bot.
    -   An explanation of the configuration options in `config.yaml`.

* **Step 5.2: Final Code Review**
    Perform one final pass over all the new files (`stealthmaster.py`, `notifications.py`, `captcha_solver.py`). Ensure the code is clean, well-commented, and all methods have docstrings explaining what they do.

* **Step 5.3: Generate Cleanup Instructions**
    To complete the process, provide a list of all the files and directories from the original project that are now redundant and should be deleted by the user. This will primarily be the entire `src` directory and the old `stealthmaster.py` file.
</instructions>

</master_prompt>