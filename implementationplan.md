# StealthMaster Bot: Strategic Implementation Plan

## 1\. Objective

This document outlines a three-phase strategic plan to evolve the `StealthMaster` bot into a state-of-the-art automation platform. The primary goal is to address critical integration issues, enhance stealth capabilities against Akamai, and optimize performance and cost-efficiency. The architectural foundation will shift to a centralized orchestration model, leveraging persistent, warmed-up browser sessions as the primary operational standard.

## 2\. Guiding Architectural Principles

  * **Centralized Orchestration:** A single `StealthMasterOrchestrator` class will manage the lifecycle and interaction of all core components (browser pool, proxy manager, behavior engine, etc.).
  * **Persistent Session Lifecycle:** The bot will abandon the "fresh session" model. All operations will be conducted through a pool of persistent, warmed-up user profiles, each with a stable trust score and history.
  * **Context-Aware Behavior:** Human behavior simulation will be context-driven, aligning actions with specific tasks (e.g., searching, checkout) to appear more natural.
  * **Stability Over Rotation:** The proxy strategy will prioritize stable, sticky residential sessions, as IP consistency is a key trust signal for modern bot detection systems.

-----

## 3\. Phased Implementation Plan

### **Phase 1: Core Integration (Target: Week 1)**

*Objective: Establish the new architectural foundation. Integrate the most critical components to achieve a baseline of high undetectability.*

#### **Task 1.1: Refactor `EnhancedBrowserPool` for Persistence**

  * **Objective:** Transform the browser pool from a session factory into a manager of persistent, long-lived browser profiles.
  * **Target Files:**
      * `src/browser/pool.py` (Major Refactor)
      * `src/stealth/browser_warmup.py` (Integration)
      * `src/profiles/persistence.py` (Integration)
  * **Actionable Steps:**
    1.  Modify `EnhancedBrowserPool` to load, manage, and save a finite number of browser profiles from a dedicated directory.
    2.  Integrate the `BrowserWarmupEngine`. When a new profile is created or a cold one is loaded, the pool must trigger the warmup sequence before making the profile available for tasks.
    3.  Implement a `PersistentSession` class (see Architectural Blueprints below) to track the state, trust score, and associated proxy for each profile.
    4.  The `acquire_browser` method should now return a complete, warmed-up `PersistentSession` object.

#### **Task 1.2: Unify Browser Launch via `ultimate_bypass`**

  * **Objective:** Make the advanced `nodriver` and OS-level input methods the standard, not an alternative.
  * **Target Files:**
      * `src/browser/launcher.py` (Refactor)
      * `src/stealth/ultimate_bypass.py` (Integration)
  * **Actionable Steps:**
    1.  Remove the old browser launch logic from `launcher.py`.
    2.  The launcher should now exclusively use the functions and principles from `ultimate_bypass.py` to create new browser instances.
    3.  Ensure the launcher is configured to use the custom Chrome extension for browser control.

#### **Task 1.3: Enforce Sticky Proxy Sessions**

  * **Objective:** Reconfigure the proxy manager to prioritize session stability over rotation.
  * **Target Files:**
      * `src/network/intelligent_proxy_manager.py` (Logic Modification)
      * `src/config.py` (Configuration Update)
  * **Actionable Steps:**
    1.  Modify the `IntelligentProxyRotator`'s selection algorithm. It must check if an active `PersistentSession` already has an assigned proxy and continue using it.
    2.  When a new session requires a proxy, it should select a high-quality residential proxy and "lock" it to that session.
    3.  Rotation should *only* occur on explicit failure (e.g., confirmed IP block, multiple failed health checks).
    4.  Update `config.py` to include a `session_id` field in the `ProxyConfig` and set Italian residential proxies as the default for the Fansale platform configuration.

#### **Task 1.4: Activate Data-Saving Measures**

  * **Objective:** Enable and enforce aggressive data-saving settings by default.
  * **Target Files:**
      * `src/config.py` (Default Value Change)
  * **Actionable Steps:**
    1.  In the `DataLimits` model within `config.py`, set the default value for `resource_blocking` to `True`.
    2.  Ensure that resources like images, media, and fonts are blocked on all page loads.

-----

### **Phase 2: Behavioral & Adaptive Enhancement (Target: Week 2)**

*Objective: Refine the bot's behavior to be indistinguishable from a human's and enable the system to react dynamically to detection events.*

#### **Task 2.1: Implement Goal-Oriented Behavior**

  * **Objective:** Make human behavior simulation context-aware.
  * **Target Files:**
      * `src/stealth/behaviors.py` (Add New Classes)
      * `src/platforms/*.py` (Integration)
  * **Actionable Steps:**
    1.  Create a `BehaviorContext` class (see Architectural Blueprints) in `behaviors.py`.
    2.  Define an enumeration for `TaskType` (e.g., `SEARCHING`, `SELECTING_TICKET`, `CHECKOUT_FORM`).
    3.  In each platform handler (e.g., `fansale.py`), before initiating a behavior, create a `BehaviorContext` instance that defines the current task and the relevant "attention zones" (e.g., coordinates of the search bar, ticket list, or payment form).
    4.  Modify `HumanBehavior` methods to accept this context and direct mouse movements and interactions within the specified zones.

#### **Task 2.2: Connect the Adaptive Response Engine**

  * **Objective:** Create a closed-loop system where detection events automatically trigger strategic changes.
  * **Target Files:**
      * `src/detection/adaptive_response.py` (Integration)
      * `src/orchestration/state.py` (Integration)
      * `src/browser/pool.py` (Integration)
  * **Actionable Steps:**
    1.  The `DetectionMonitor` should report failure events (e.g., captcha, block page) to the central `StealthMasterOrchestrator`.
    2.  The orchestrator will then consult the `AdaptiveResponseEngine`.
    3.  The engine will recommend a new strategy (e.g., "retire session and proxy", "switch to a higher-quality fingerprint").
    4.  The orchestrator will execute this strategy via the `EnhancedBrowserPool` and `IntelligentProxyRotator`.

-----

### **Phase 3: Advanced Optimizations (Target: Week 3)**

*Objective: Implement cutting-edge techniques to maximize speed and data efficiency, and harden the bot against browser-level detection.*

#### **Task 3.1: Develop API-Based Monitoring**

  * **Objective:** Drastically reduce data usage and increase monitoring speed by using a target site's internal APIs instead of full page loads.
  * **Target Files:**
      * `src/network/interceptor.py` (Enhance)
      * `src/platforms/*.py` (New Monitoring Mode)
  * **Actionable Steps:**
    1.  Enhance the `interceptor` to not only cache but also log `fetch`/`XHR` requests that return JSON data during manual analysis.
    2.  Create a new `APIMonitor` class that can be configured with specific API endpoints for each platform.
    3.  In `fansale.py`, implement a hybrid monitoring mode: use the `APIMonitor` for high-frequency checks and only trigger a full browser-based check when the API indicates a change.

#### **Task 3.2: Integrate Critical OS-Level Actions**

  * **Objective:** Use OS-level input for the most sensitive actions to make them completely invisible to the browser.
  * **Target Files:**
      * `src/stealth/ultimate_bypass.py` (Create Wrapper)
  * **Actionable Steps:**
    1.  Create a simple, robust wrapper class `OSInput` that abstracts `pyautogui` functions (`click`, `type`, etc.).
    2.  This wrapper must perform coordinate calibration to adjust for different screen resolutions and window sizes.
    3.  In the platform checkout flows, replace critical CDP-based clicks (e.g., "Confirm Purchase") with calls to the `OSInput` wrapper.

-----

## 4\. Architectural Blueprints (Code Skeletons)

```python
# Location: src/orchestration/orchestrator.py (New File)
class StealthMasterOrchestrator:
    """Central orchestration point for all components."""
    def __init__(self, config: RootConfig):
        self.config = config
        self.browser_pool = EnhancedBrowserPool(config.browser_pool_settings)
        self.proxy_manager = IntelligentProxyRotator(config.proxy_settings)
        # ... other components initialized here
        self.state_manager = GlobalStateManager()

    async def run_workflow(self, workflow_name: str):
        # Main logic to acquire resources and execute a task workflow
        pass

# Location: src/browser/session.py (New File or in pool.py)
from enum import Enum
from datetime import datetime

class WarmupState(Enum):
    COLD = "COLD"
    WARMING = "WARMING"
    WARM = "WARM"

class PersistentSession:
    """Manages the lifecycle of a single warmed-up browser session."""
    def __init__(self, profile_id: str, proxy: ProxyConfig):
        self.profile_id: str = profile_id
        self.proxy: ProxyConfig = proxy
        self.browser: 'uc.Chrome' = None # type: ignore
        self.trust_score: float = 0.0
        self.warmup_state: WarmupState = WarmupState.COLD
        self.last_activity: datetime = datetime.now()
        self.is_in_use: bool = False

# Location: src/stealth/behaviors.py (Enhancement)
from enum import Enum
from typing import List, NamedTuple

class Rectangle(NamedTuple):
    x: int
    y: int
    width: int
    height: int

class TaskType(Enum):
    GENERIC_Browse = "GENERIC_Browse"
    SEARCHING = "SEARCHING"
    SELECTING = "SELECTING"
    FORM_FILLING = "FORM_FILLING"
    CHECKOUT = "CHECKOUT"

class BehaviorContext:
    """Provides context for more realistic behavior simulation."""
    task_type: TaskType
    focus_areas: List[Rectangle]  # List of primary interaction zones
    interaction_speed: float = 1.0  # Multiplier (e.g., 0.8 for slower, 1.5 for faster)
```

```
**Rationale:** This markdown file is structured as a comprehensive project plan. It clearly defines the objectives, principles, and a phased, actionable timeline. Each task is broken down with a clear goal, target files, and specific steps. Providing the Python class skeletons gives a concrete architectural blueprint that is ready for implementation, which is ideal for a developer or another AI to understand and execute precisely.

</File>
```