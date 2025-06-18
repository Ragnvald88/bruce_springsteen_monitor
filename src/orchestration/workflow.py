# stealthmaster/orchestration/workflow.py
"""Purchase workflow orchestration."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from ..browser.pool import EnhancedBrowserPool
from ..config import Target, Platform
from ..profiles.models import Profile as UserProfile
from ..constants import PurchaseStatus
from ..detection.monitor import DetectionMonitor, MonitoringLevel
from ..detection.recovery import RecoveryStrategy
from ..network.rate_limiter import IntelligentRateLimiter as RateLimiter
from .state import StateManager, StateType
from ..platforms.base import BasePlatformHandler
# COMMENTED OUT: Using purchase handlers instead
# from ..platforms import (
#     FansaleHandler,
#     TicketmasterHandler,
#     VivaticketHandler,
# )

logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    """Workflow execution steps."""
    
    INITIALIZE = "initialize"
    LOGIN = "login"
    SEARCH_TICKETS = "search_tickets"
    SELECT_TICKETS = "select_tickets"
    CHECKOUT = "checkout"
    CONFIRM = "confirm"
    COMPLETE = "complete"


class PurchaseWorkflow:
    """Orchestrates the ticket purchase workflow."""
    
    def __init__(
        self,
        browser_pool: EnhancedBrowserPool,
        state_manager: StateManager,
        detection_monitor: DetectionMonitor,
        rate_limiter: RateLimiter,
    ):
        """Initialize workflow with speed optimizations.
        
        Args:
            browser_pool: Browser pool for instances
            state_manager: State management
            detection_monitor: Detection monitoring
            rate_limiter: Rate limiting
        """
        self.browser_pool = browser_pool
        self.state_manager = state_manager
        self.detection_monitor = detection_monitor
        self.rate_limiter = rate_limiter
        self.recovery_strategy = RecoveryStrategy()
        
        # Platform handlers
        self._platform_handlers = {
            Platform.FANSALE: FansaleHandler(),
            Platform.TICKETMASTER: TicketmasterHandler(),
            Platform.VIVATICKET: VivaticketHandler(),
        }
        
        # Active workflows
        self._active_workflows: Dict[str, asyncio.Task] = {}
    
    async def start_purchase(
        self,
        event: Target,
        profile: UserProfile,
        workflow_id: Optional[str] = None
    ) -> str:
        """
        Start a purchase workflow.
        
        Args:
            event: Target event
            profile: User profile
            workflow_id: Optional workflow ID
            
        Returns:
            Workflow ID
        """
        if not workflow_id:
            workflow_id = f"workflow_{event.platform.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Check if already running
        if workflow_id in self._active_workflows:
            logger.warning(f"Workflow {workflow_id} already running")
            return workflow_id
        
        # Initialize workflow state
        self.state_manager.set_workflow_state(
            workflow_id,
            PurchaseStatus.PENDING,
            event=event.dict(),
            profile={"email": profile.email, "name": f"{profile.first_name} {profile.last_name}"}
        )
        
        # Start workflow task
        task = asyncio.create_task(
            self._execute_workflow(workflow_id, event, profile)
        )
        self._active_workflows[workflow_id] = task
        
        logger.info(f"Started purchase workflow: {workflow_id}")
        return workflow_id
    
    async def stop_workflow(self, workflow_id: str) -> bool:
        """
        Stop a running workflow.
        
        Args:
            workflow_id: Workflow to stop
            
        Returns:
            Success status
        """
        if workflow_id not in self._active_workflows:
            return False
        
        task = self._active_workflows[workflow_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self._active_workflows[workflow_id]
        
        # Update state
        self.state_manager.set_workflow_state(
            workflow_id,
            PurchaseStatus.FAILED,
            error="Workflow cancelled by user"
        )
        
        logger.info(f"Stopped workflow: {workflow_id}")
        return True
    
    async def _execute_workflow(
        self,
        workflow_id: str,
        event: Target,
        profile: UserProfile
    ) -> None:
        """Execute the purchase workflow."""
        browser_instance = None
        context = None
        page = None
        
        try:
            # Update status
            self.state_manager.set_workflow_state(
                workflow_id,
                PurchaseStatus.SEARCHING
            )
            
            # Get platform handler
            handler = self._platform_handlers.get(event.platform)
            if not handler:
                raise ValueError(f"Unsupported platform: {event.platform}")
            
            # Acquire browser
            logger.info(f"Acquiring browser for {event.platform.value}")
            browser_instance, context = await self.browser_pool.acquire(
                prefer_proxy=True
            )
            
            # Create page
            page = await context.new_page()
            
            # Start detection monitoring
            await self.detection_monitor.start_monitoring(
                page,
                MonitoringLevel.HIGH
            )
            
            # Execute workflow steps
            result = await self._execute_steps(
                workflow_id,
                page,
                handler,
                event,
                profile
            )
            
            if result["success"]:
                self.state_manager.set_workflow_state(
                    workflow_id,
                    PurchaseStatus.COMPLETED,
                    result=result
                )
                logger.info(f"Workflow {workflow_id} completed successfully!")
            else:
                self.state_manager.set_workflow_state(
                    workflow_id,
                    PurchaseStatus.FAILED,
                    error=result.get("error", "Unknown error")
                )
                
        except Exception as e:
            logger.error(f"Workflow {workflow_id} error: {e}")
            self.state_manager.set_workflow_state(
                workflow_id,
                PurchaseStatus.FAILED,
                error=str(e)
            )
            
        finally:
            # Cleanup
            if page:
                await self.detection_monitor.stop_monitoring(page)
                await page.close()
            
            if browser_instance and context:
                await self.browser_pool.release(
                    browser_instance,
                    context,
                    success=self.state_manager.get(
                        f"workflow_{workflow_id}_status",
                        StateType.WORKFLOW
                    ) == PurchaseStatus.COMPLETED.value
                )
            
            # Remove from active
            self._active_workflows.pop(workflow_id, None)
    
    async def _execute_steps(
        self,
        workflow_id: str,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Execute workflow steps."""
        steps = [
            (WorkflowStep.INITIALIZE, self._step_initialize),
            (WorkflowStep.LOGIN, self._step_login),
            (WorkflowStep.SEARCH_TICKETS, self._step_search),
            (WorkflowStep.SELECT_TICKETS, self._step_select),
            (WorkflowStep.CHECKOUT, self._step_checkout),
            (WorkflowStep.CONFIRM, self._step_confirm),
        ]
        
        for step, step_func in steps:
            # Update progress
            self.state_manager.set(
                f"workflow_{workflow_id}_progress",
                {"current_step": step.value, "timestamp": datetime.now().isoformat()},
                StateType.WORKFLOW
            )
            
            # Check for detection before each step
            detection = await self.detection_monitor.force_check(page)
            if detection["detected"]:
                logger.warning(f"Detection before {step.value}: {detection['type']}")
                
                # Attempt recovery
                recovered = await self.recovery_strategy.attempt_recovery(
                    page,
                    detection["type"],
                    detection
                )
                
                if not recovered:
                    return {
                        "success": False,
                        "error": f"Detected and could not recover: {detection['type']}"
                    }
            
            # Execute step
            logger.info(f"Executing step: {step.value}")
            result = await step_func(page, handler, event, profile)
            
            if not result["success"]:
                return result
            
            # Rate limiting between steps
            await self.rate_limiter.wait_if_needed(page.url)
        
        return {"success": True, "message": "Workflow completed"}
    
    async def _step_initialize(
        self,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Initialize platform."""
        try:
            success = await handler.initialize(page)
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": f"Initialization failed: {e}"}
    
    async def _step_login(
        self,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Login to platform."""
        try:
            # Check if login required
            platform_config = {
                Platform.FANSALE: True,
                Platform.TICKETMASTER: True,
                Platform.VIVATICKET: False,
            }
            
            if not platform_config.get(event.platform, True):
                logger.info(f"Login not required for {event.platform.value}")
                return {"success": True}
            
            success = await handler.login(page, profile)
            return {"success": success}
            
        except Exception as e:
            return {"success": False, "error": f"Login failed: {e}"}
    
    async def _step_search(
        self,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Search for tickets."""
        try:
            self.state_manager.set_workflow_state(
                self._get_workflow_id(),
                PurchaseStatus.SEARCHING
            )
            
            tickets = await handler.search_tickets(page, event)
            
            if not tickets:
                return {"success": False, "error": "No tickets found"}
            
            # Store found tickets
            self.state_manager.set(
                f"workflow_{self._get_workflow_id()}_tickets",
                tickets,
                StateType.WORKFLOW
            )
            
            logger.info(f"Found {len(tickets)} tickets")
            return {"success": True, "tickets": tickets}
            
        except Exception as e:
            return {"success": False, "error": f"Search failed: {e}"}
    
    async def _step_select(
        self,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Select tickets."""
        try:
            # Get found tickets
            tickets = self.state_manager.get(
                f"workflow_{self._get_workflow_id()}_tickets",
                StateType.WORKFLOW,
                []
            )
            
            if not tickets:
                return {"success": False, "error": "No tickets to select"}
            
            self.state_manager.set_workflow_state(
                self._get_workflow_id(),
                PurchaseStatus.FOUND
            )
            
            success = await handler.select_tickets(
                page,
                tickets,
                event.ticket_quantity
            )
            
            if success:
                self.state_manager.set_workflow_state(
                    self._get_workflow_id(),
                    PurchaseStatus.RESERVED
                )
            
            return {"success": success}
            
        except Exception as e:
            return {"success": False, "error": f"Selection failed: {e}"}
    
    async def _step_checkout(
        self,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Complete checkout."""
        try:
            self.state_manager.set_workflow_state(
                self._get_workflow_id(),
                PurchaseStatus.PURCHASING
            )
            
            result = await handler.complete_purchase(page, profile)
            
            return {
                "success": result.get("success", False),
                "confirmation": result.get("confirmation_number"),
                "error": result.get("error")
            }
            
        except Exception as e:
            return {"success": False, "error": f"Checkout failed: {e}"}
    
    async def _step_confirm(
        self,
        page: Any,
        handler: BasePlatformHandler,
        event: Target,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Confirm purchase."""
        # This step would handle confirmation emails, etc.
        # For now, just return success
        return {"success": True}
    
    def _get_workflow_id(self) -> str:
        """Get current workflow ID (hack for now)."""
        # In a real implementation, this would be passed through
        # For now, return the first active workflow
        if self._active_workflows:
            return list(self._active_workflows.keys())[0]
        return "unknown"
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow status information
        """
        return self.state_manager.get_workflow_state(workflow_id)
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get list of active workflows."""
        workflows = []
        
        for workflow_id in self._active_workflows:
            status = self.get_workflow_status(workflow_id)
            workflows.append({
                "workflow_id": workflow_id,
                "status": status.get("status"),
                "started_at": status.get("started_at"),
                "event": status.get("event", {}).get("event_name"),
            })
        
        return workflows