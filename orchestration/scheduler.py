# stealthmaster/orchestration/scheduler.py
"""Task scheduling for automated ticket purchasing."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

from config import Target as TargetEvent

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledTask:
    """Represents a scheduled task."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        coroutine: Callable,
        scheduled_time: datetime,
        priority: TaskPriority = TaskPriority.NORMAL,
        event: Optional[TargetEvent] = None,
        retry_count: int = 0,
        max_retries: int = 3,
    ):
        """Initialize scheduled task."""
        self.task_id = task_id
        self.name = name
        self.coroutine = coroutine
        self.scheduled_time = scheduled_time
        self.priority = priority
        self.event = event
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1


class TaskScheduler:
    """Manages scheduled tasks for ticket purchasing."""
    
    def __init__(self):
        """Initialize task scheduler."""
        self._tasks: Dict[str, ScheduledTask] = {}
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self._task_counter = 0
    
    async def start(self) -> None:
        """Start the task scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler started")
    
    async def stop(self) -> None:
        """Stop the task scheduler."""
        self._running = False
        
        # Cancel scheduler task
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        for task_id, task in list(self._running_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("Task scheduler stopped")
    
    def schedule_task(
        self,
        name: str,
        coroutine: Callable,
        scheduled_time: datetime,
        priority: TaskPriority = TaskPriority.NORMAL,
        event: Optional[TargetEvent] = None,
    ) -> str:
        """
        Schedule a new task.
        
        Args:
            name: Task name
            coroutine: Async function to execute
            scheduled_time: When to execute
            priority: Task priority
            event: Associated event
            
        Returns:
            Task ID
        """
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{name.replace(' ', '_')}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            coroutine=coroutine,
            scheduled_time=scheduled_time,
            priority=priority,
            event=event,
        )
        
        self._tasks[task_id] = task
        
        # Add to queue
        # Priority queue uses negative priority for correct ordering
        priority_value = -task.priority.value
        self._task_queue.put_nowait((scheduled_time, priority_value, task_id))
        
        logger.info(
            f"Scheduled task '{name}' for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return task_id
    
    def schedule_event_monitoring(
        self,
        event: TargetEvent,
        check_interval: timedelta = timedelta(minutes=5),
    ) -> str:
        """
        Schedule monitoring for an event.
        
        Args:
            event: Event to monitor
            check_interval: How often to check
            
        Returns:
            Task ID
        """
        # Schedule first check
        first_check = datetime.now() + timedelta(seconds=10)
        
        async def monitor_event():
            """Monitor event availability."""
            logger.info(f"Checking event: {event.event_name}")
            # This would be implemented with actual monitoring logic
            # For now, reschedule next check
            
            if datetime.now() < event.event_date:
                # Reschedule
                next_check = datetime.now() + check_interval
                self.schedule_task(
                    name=f"monitor_{event.event_name}",
                    coroutine=monitor_event,
                    scheduled_time=next_check,
                    priority=TaskPriority.HIGH,
                    event=event,
                )
        
        return self.schedule_task(
            name=f"monitor_{event.event_name}",
            coroutine=monitor_event,
            scheduled_time=first_check,
            priority=TaskPriority.HIGH,
            event=event,
        )
    
    def schedule_purchase_attempt(
        self,
        event: TargetEvent,
        attempt_time: datetime,
        priority: TaskPriority = TaskPriority.CRITICAL,
    ) -> str:
        """
        Schedule a purchase attempt.
        
        Args:
            event: Event to purchase tickets for
            attempt_time: When to attempt purchase
            priority: Task priority
            
        Returns:
            Task ID
        """
        async def purchase_tickets():
            """Attempt to purchase tickets."""
            logger.info(f"Starting purchase attempt for {event.event_name}")
            # This would trigger the actual purchase workflow
            # Placeholder for now
            await asyncio.sleep(1)
            return {"success": True, "tickets": 2}
        
        return self.schedule_task(
            name=f"purchase_{event.event_name}",
            coroutine=purchase_tickets,
            scheduled_time=attempt_time,
            priority=priority,
            event=event,
        )
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Wait for next task
                if self._task_queue.empty():
                    await asyncio.sleep(1)
                    continue
                
                # Peek at next task
                scheduled_time, priority, task_id = await self._task_queue.get()
                
                # Check if it's time
                now = datetime.now()
                if scheduled_time > now:
                    # Not yet, put it back
                    await self._task_queue.put((scheduled_time, priority, task_id))
                    
                    # Wait until task time or 1 second
                    wait_time = min((scheduled_time - now).total_seconds(), 1.0)
                    await asyncio.sleep(wait_time)
                    continue
                
                # Time to execute
                task = self._tasks.get(task_id)
                if not task:
                    logger.warning(f"Task {task_id} not found")
                    continue
                
                # Check if already running
                if task_id in self._running_tasks:
                    logger.warning(f"Task {task_id} already running")
                    continue
                
                # Execute task
                logger.info(f"Executing task: {task.name}")
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                # Create asyncio task
                asyncio_task = asyncio.create_task(
                    self._execute_task(task)
                )
                self._running_tasks[task_id] = asyncio_task
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        try:
            # Run the task
            result = await task.coroutine()
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            logger.info(f"Task {task.name} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")
            
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            
            # Check if can retry
            if task.can_retry:
                task.increment_retry()
                retry_delay = timedelta(seconds=30 * task.retry_count)
                retry_time = datetime.now() + retry_delay
                
                logger.info(
                    f"Retrying task {task.name} (attempt {task.retry_count + 1})"
                )
                
                # Reschedule
                self.schedule_task(
                    name=task.name,
                    coroutine=task.coroutine,
                    scheduled_time=retry_time,
                    priority=task.priority,
                    event=task.event,
                )
        
        finally:
            # Remove from running tasks
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task to cancel
            
        Returns:
            Success status
        """
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        
        # Cancel if running
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        logger.info(f"Cancelled task: {task.name}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information
        """
        if task_id not in self._tasks:
            return None
        
        task = self._tasks[task_id]
        
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "scheduled_time": task.scheduled_time.isoformat(),
            "priority": task.priority.name,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "retry_count": task.retry_count,
            "result": task.result,
            "error": task.error,
        }
    
    def get_scheduled_tasks(
        self,
        status: Optional[TaskStatus] = None,
        event: Optional[TargetEvent] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get list of scheduled tasks.
        
        Args:
            status: Filter by status
            event: Filter by event
            
        Returns:
            List of task information
        """
        tasks = []
        
        for task in self._tasks.values():
            # Apply filters
            if status and task.status != status:
                continue
            
            if event and task.event != event:
                continue
            
            tasks.append({
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status.value,
                "scheduled_time": task.scheduled_time.isoformat(),
                "priority": task.priority.name,
                "event": task.event.event_name if task.event else None,
            })
        
        # Sort by scheduled time
        tasks.sort(key=lambda x: x["scheduled_time"])
        
        return tasks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total_tasks = len(self._tasks)
        
        # Count by status
        status_counts = {}
        for task in self._tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "running_tasks": len(self._running_tasks),
            "status_counts": status_counts,
            "scheduler_running": self._running,
        }
