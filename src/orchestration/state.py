# stealthmaster/orchestration/state.py
"""State management for ticket purchasing workflows."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from ..constants import PurchaseStatus

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of state data."""
    
    WORKFLOW = "workflow"
    SESSION = "session"
    PROFILE = "profile"
    EVENT = "event"
    SYSTEM = "system"


class StateManager:
    """Manages application state across sessions."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize state manager.
        
        Args:
            data_dir: Directory for state storage
        """
        self.data_dir = data_dir
        self.state_dir = data_dir / "state"
        self.state_dir.mkdir(exist_ok=True)
        
        # In-memory state cache
        self._state_cache: Dict[str, Dict[str, Any]] = {}
        
        # State change callbacks
        self._callbacks: Dict[str, List[Any]] = {}
        
        # Load existing state
        self._load_state()
    
    def get(
        self,
        key: str,
        state_type: StateType = StateType.WORKFLOW,
        default: Any = None
    ) -> Any:
        """
        Get state value.
        
        Args:
            key: State key
            state_type: Type of state
            default: Default value if not found
            
        Returns:
            State value or default
        """
        type_key = state_type.value
        
        if type_key in self._state_cache:
            return self._state_cache[type_key].get(key, default)
        
        return default
    
    def set(
        self,
        key: str,
        value: Any,
        state_type: StateType = StateType.WORKFLOW,
        persist: bool = True
    ) -> None:
        """
        Set state value.
        
        Args:
            key: State key
            value: State value
            state_type: Type of state
            persist: Whether to persist to disk
        """
        type_key = state_type.value
        
        # Ensure type exists
        if type_key not in self._state_cache:
            self._state_cache[type_key] = {}
        
        # Store value
        old_value = self._state_cache[type_key].get(key)
        self._state_cache[type_key][key] = value
        
        # Persist if requested
        if persist:
            self._save_state(type_key)
        
        # Notify callbacks
        self._notify_change(type_key, key, old_value, value)
    
    def update(
        self,
        updates: Dict[str, Any],
        state_type: StateType = StateType.WORKFLOW,
        persist: bool = True
    ) -> None:
        """
        Update multiple state values.
        
        Args:
            updates: Dictionary of updates
            state_type: Type of state
            persist: Whether to persist to disk
        """
        for key, value in updates.items():
            self.set(key, value, state_type, persist=False)
        
        if persist:
            self._save_state(state_type.value)
    
    def delete(
        self,
        key: str,
        state_type: StateType = StateType.WORKFLOW
    ) -> bool:
        """
        Delete state value.
        
        Args:
            key: State key
            state_type: Type of state
            
        Returns:
            Whether key existed
        """
        type_key = state_type.value
        
        if type_key in self._state_cache and key in self._state_cache[type_key]:
            old_value = self._state_cache[type_key][key]
            del self._state_cache[type_key][key]
            
            self._save_state(type_key)
            self._notify_change(type_key, key, old_value, None)
            
            return True
        
        return False
    
    def get_workflow_state(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get complete workflow state.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow state data
        """
        workflow_key = f"workflow_{workflow_id}"
        
        return {
            "workflow_id": workflow_id,
            "status": self.get(f"{workflow_key}_status", StateType.WORKFLOW),
            "started_at": self.get(f"{workflow_key}_started", StateType.WORKFLOW),
            "updated_at": self.get(f"{workflow_key}_updated", StateType.WORKFLOW),
            "event": self.get(f"{workflow_key}_event", StateType.WORKFLOW),
            "profile": self.get(f"{workflow_key}_profile", StateType.WORKFLOW),
            "progress": self.get(f"{workflow_key}_progress", StateType.WORKFLOW, {}),
            "result": self.get(f"{workflow_key}_result", StateType.WORKFLOW),
            "error": self.get(f"{workflow_key}_error", StateType.WORKFLOW),
        }
    
    def set_workflow_state(
        self,
        workflow_id: str,
        status: PurchaseStatus,
        **kwargs
    ) -> None:
        """
        Set workflow state.
        
        Args:
            workflow_id: Workflow identifier
            status: Workflow status
            **kwargs: Additional state data
        """
        workflow_key = f"workflow_{workflow_id}"
        
        updates = {
            f"{workflow_key}_status": status.value,
            f"{workflow_key}_updated": datetime.now().isoformat(),
        }
        
        # Add optional fields
        for key, value in kwargs.items():
            updates[f"{workflow_key}_{key}"] = value
        
        # Set started time if starting
        if status == PurchaseStatus.SEARCHING and f"{workflow_key}_started" not in self._state_cache.get(StateType.WORKFLOW.value, {}):
            updates[f"{workflow_key}_started"] = datetime.now().isoformat()
        
        self.update(updates, StateType.WORKFLOW)
    
    def add_callback(
        self,
        state_type: StateType,
        callback: Any,
        key_filter: Optional[str] = None
    ) -> None:
        """
        Add state change callback.
        
        Args:
            state_type: Type of state to monitor
            callback: Callback function
            key_filter: Optional key pattern to filter
        """
        callback_key = f"{state_type.value}:{key_filter or '*'}"
        
        if callback_key not in self._callbacks:
            self._callbacks[callback_key] = []
        
        self._callbacks[callback_key].append(callback)
    
    def remove_callback(
        self,
        state_type: StateType,
        callback: Any,
        key_filter: Optional[str] = None
    ) -> None:
        """
        Remove state change callback.
        
        Args:
            state_type: Type of state
            callback: Callback to remove
            key_filter: Optional key pattern
        """
        callback_key = f"{state_type.value}:{key_filter or '*'}"
        
        if callback_key in self._callbacks:
            try:
                self._callbacks[callback_key].remove(callback)
            except ValueError:
                pass
    
    def _notify_change(
        self,
        state_type: str,
        key: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """Notify callbacks of state change."""
        # Global callbacks for this type
        global_key = f"{state_type}:*"
        if global_key in self._callbacks:
            for callback in self._callbacks[global_key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        # Specific callbacks
        specific_key = f"{state_type}:{key}"
        if specific_key in self._callbacks:
            for callback in self._callbacks[specific_key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def _load_state(self) -> None:
        """Load state from disk."""
        for state_file in self.state_dir.glob("*.json"):
            try:
                state_type = state_file.stem
                
                with open(state_file, "r") as f:
                    data = json.load(f)
                
                self._state_cache[state_type] = data
                
                logger.debug(f"Loaded state: {state_type}")
                
            except Exception as e:
                logger.error(f"Failed to load state {state_file}: {e}")
    
    def _save_state(self, state_type: str) -> None:
        """Save state to disk."""
        try:
            state_file = self.state_dir / f"{state_type}.json"
            
            data = self._state_cache.get(state_type, {})
            
            with open(state_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved state: {state_type}")
            
        except Exception as e:
            logger.error(f"Failed to save state {state_type}: {e}")
    
    def clear_state(self, state_type: Optional[StateType] = None) -> None:
        """
        Clear state data.
        
        Args:
            state_type: Specific type to clear, or None for all
        """
        if state_type:
            type_key = state_type.value
            if type_key in self._state_cache:
                self._state_cache[type_key].clear()
                self._save_state(type_key)
        else:
            # Clear all
            self._state_cache.clear()
            
            # Remove all state files
            for state_file in self.state_dir.glob("*.json"):
                state_file.unlink()
        
        logger.info(f"Cleared state: {state_type.value if state_type else 'all'}")
    
    def export_state(self, export_path: Path) -> bool:
        """
        Export all state data.
        
        Args:
            export_path: Path to export to
            
        Returns:
            Success status
        """
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "state": self._state_cache,
            }
            
            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported state to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export state: {e}")
            return False
    
    def import_state(self, import_path: Path) -> bool:
        """
        Import state data.
        
        Args:
            import_path: Path to import from
            
        Returns:
            Success status
        """
        try:
            with open(import_path, "r") as f:
                import_data = json.load(f)
            
            # Replace current state
            self._state_cache = import_data.get("state", {})
            
            # Save all state types
            for state_type in self._state_cache:
                self._save_state(state_type)
            
            logger.info(f"Imported state from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import state: {e}")
            return False