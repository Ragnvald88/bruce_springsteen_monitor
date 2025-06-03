# src/utils/distributed.py
import os
import json
import logging
import time
import random
import hashlib
import asyncio
import socket
from typing import List, Dict, Optional, Tuple, Any, Set
from pathlib import Path
import uuid

import redis
from redis.exceptions import LockError, WatchError

logger = logging.getLogger(__name__)

class AdvancedDistributedCoordinator:
    """
    Advanced distributed coordinator using Redis for real-time coordination,
    work stealing, heartbeats, and sophisticated workload distribution.
    """
    
    def __init__(
        self, 
        instance_id: str = None,
        redis_url: str = "redis://localhost:6379/0",
        namespace: str = "ticketbot:",
        heartbeat_interval: int = 5,
        instance_timeout: int = 30,
        auto_failover: bool = True,
        auto_start_heartbeat: bool = True
    ):
        # Generate a unique ID if none provided
        self.instance_id = instance_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.redis_url = redis_url
        self.namespace = namespace
        self.heartbeat_interval = heartbeat_interval
        self.instance_timeout = instance_timeout
        self.auto_failover = auto_failover
        
        # Initialize Redis client
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._heartbeat_task = None
        
        # Redis key prefixes
        self.instances_key = f"{namespace}instances"
        self.targets_key = f"{namespace}targets"
        self.assignments_key = f"{namespace}assignments"
        self.heartbeats_key = f"{namespace}heartbeats"
        self.stats_key = f"{namespace}stats"
        self.locks_key = f"{namespace}locks"
        self.hits_key = f"{namespace}hits"
        
        # Start heartbeat if requested
        if auto_start_heartbeat:
            self.start_heartbeat()
            
        logger.info(f"Advanced distributed coordinator initialized with ID: {self.instance_id}")
        logger.info(f"Connected to Redis at {redis_url}")
    
    def start_heartbeat(self):
        """Start the heartbeat loop in a background thread"""
        if self._heartbeat_task:
            return
            
        import threading
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name=f"heartbeat-{self.instance_id}"
        )
        self._heartbeat_thread.start()
        logger.info(f"Started heartbeat loop for instance {self.instance_id}")
    
    def stop_heartbeat(self):
        """Stop the heartbeat loop"""
        self._heartbeat_running = False
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)
        logger.info(f"Stopped heartbeat loop for instance {self.instance_id}")
    
    def _heartbeat_loop(self):
        """Background thread for sending heartbeats"""
        self._heartbeat_running = True
        while self._heartbeat_running:
            try:
                # Update heartbeat
                self.redis.hset(self.heartbeats_key, self.instance_id, time.time())
                
                # Check and handle any failed instances if auto_failover is enabled
                if self.auto_failover:
                    self._check_for_failed_instances()
                    
                # Sleep for the heartbeat interval
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(self.heartbeat_interval)  # Still sleep to avoid rapid retries
    
    def _check_for_failed_instances(self):
        """Check for failed instances and reassign their work"""
        try:
            # Get all heartbeats
            all_heartbeats = self.redis.hgetall(self.heartbeats_key)
            current_time = time.time()
            
            # Find failed instances (no heartbeat for timeout period)
            failed_instances = [
                instance_id for instance_id, last_beat in all_heartbeats.items()
                if current_time - float(last_beat) > self.instance_timeout
            ]
            
            # If there are failed instances, reassign their work
            if failed_instances:
                logger.warning(f"Detected failed instances: {failed_instances}")
                
                # For each failed instance, reassign its targets
                for failed_id in failed_instances:
                    try:
                        # Get targets assigned to failed instance
                        failed_assignments = self.redis.smembers(f"{self.assignments_key}:{failed_id}")
                        if not failed_assignments:
                            logger.info(f"No assignments found for failed instance {failed_id}")
                            continue
                            
                        logger.info(f"Reassigning {len(failed_assignments)} targets from failed instance {failed_id}")
                        
                        # Get all active instances (excluding the failed one)
                        active_instances = self.get_active_instances()
                        active_instances.discard(failed_id)
                        
                        if not active_instances:
                            logger.warning("No active instances available for reassignment")
                            continue
                            
                        # Distribute failed instance's targets among active instances
                        active_list = list(active_instances)
                        for i, target_id in enumerate(failed_assignments):
                            # Assign to next instance round-robin
                            new_owner = active_list[i % len(active_list)]
                            
                            # Update assignment
                            pipe = self.redis.pipeline()
                            pipe.srem(f"{self.assignments_key}:{failed_id}", target_id)
                            pipe.sadd(f"{self.assignments_key}:{new_owner}", target_id)
                            pipe.hset(f"{self.targets_key}:ownership", target_id, new_owner)
                            pipe.execute()
                            
                            logger.info(f"Reassigned target {target_id} from {failed_id} to {new_owner}")
                        
                        # Remove the failed instance's heartbeat
                        self.redis.hdel(self.heartbeats_key, failed_id)
                        logger.info(f"Removed heartbeat for failed instance {failed_id}")
                        
                    except Exception as e:
                        logger.error(f"Error reassigning work from failed instance {failed_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error checking for failed instances: {e}")
    
    def get_active_instances(self) -> Set[str]:
        """Get set of currently active instances based on recent heartbeats"""
        try:
            all_heartbeats = self.redis.hgetall(self.heartbeats_key)
            current_time = time.time()
            
            # Filter to only include instances with recent heartbeats
            active_instances = {
                instance_id for instance_id, last_beat in all_heartbeats.items()
                if current_time - float(last_beat) <= self.instance_timeout
            }
            
            return active_instances
        except Exception as e:
            logger.error(f"Error getting active instances: {e}")
            return {self.instance_id}  # Fallback to just this instance
    
    def register_instance(self) -> bool:
        """Register this instance and set initial heartbeat"""
        try:
            # Set instance data
            instance_data = {
                "hostname": socket.gethostname(),
                "ip": socket.gethostbyname(socket.gethostname()),
                "started_at": time.time(),
                "pid": os.getpid()
            }
            
            # Register in instances set
            self.redis.hset(self.instances_key, self.instance_id, json.dumps(instance_data))
            
            # Set initial heartbeat
            self.redis.hset(self.heartbeats_key, self.instance_id, time.time())
            
            # Initialize stats
            self.redis.hset(f"{self.stats_key}:{self.instance_id}", "targets_checked", 0)
            self.redis.hset(f"{self.stats_key}:{self.instance_id}", "hits_found", 0)
            
            logger.info(f"Instance {self.instance_id} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register instance: {e}")
            return False
    
    def deregister_instance(self) -> bool:
        """Deregister this instance and cleanup"""
        try:
            # Stop heartbeat
            self.stop_heartbeat()
            
            # Remove from instances
            self.redis.hdel(self.instances_key, self.instance_id)
            
            # Remove heartbeat
            self.redis.hdel(self.heartbeats_key, self.instance_id)
            
            # Get all assigned targets
            assigned_targets = self.redis.smembers(f"{self.assignments_key}:{self.instance_id}")
            
            # Reassign targets if needed
            active_instances = self.get_active_instances()
            active_instances.discard(self.instance_id)
            
            if active_instances and assigned_targets:
                # Distribute targets among other active instances
                active_list = list(active_instances)
                for i, target_id in enumerate(assigned_targets):
                    # Assign to next instance round-robin
                    new_owner = active_list[i % len(active_list)]
                    
                    # Update assignment
                    pipe = self.redis.pipeline()
                    pipe.srem(f"{self.assignments_key}:{self.instance_id}", target_id)
                    pipe.sadd(f"{self.assignments_key}:{new_owner}", target_id)
                    pipe.hset(f"{self.targets_key}:ownership", target_id, new_owner)
                    pipe.execute()
            
            # Remove assignment key
            self.redis.delete(f"{self.assignments_key}:{self.instance_id}")
            
            logger.info(f"Instance {self.instance_id} deregistered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister instance: {e}")
            return False
    
    def register_targets(self, targets: List[Dict]) -> bool:
        """Register targets in the shared Redis store"""
        try:
            pipe = self.redis.pipeline()
            
            # Clear existing targets if needed
            pipe.delete(f"{self.targets_key}:all")
            pipe.delete(f"{self.targets_key}:details")
            
            # Add all targets
            for i, target in enumerate(targets):
                # Generate a stable target ID
                target_key = target.get("url", "") or f"{target.get('platform', 'unknown')}_{i}"
                target_id = hashlib.md5(target_key.encode()).hexdigest()
                
                # Store in set of all targets
                pipe.sadd(f"{self.targets_key}:all", target_id)
                
                # Store target details
                pipe.hset(f"{self.targets_key}:details", target_id, json.dumps(target))
            
            pipe.execute()
            logger.info(f"Registered {len(targets)} targets in Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to register targets: {e}")
            return False
    
    def get_assigned_targets(self, all_targets: List[Dict]) -> List[Dict]:
        """Get targets assigned to this instance using advanced workload distribution"""
        try:
            # First register all targets if they're not already in Redis
            if not self.redis.exists(f"{self.targets_key}:all"):
                self.register_targets(all_targets)
            
            # Get active instances
            active_instances = self.get_active_instances()
            if not self.instance_id in active_instances:
                active_instances.add(self.instance_id)
            
            # Get number of active instances
            num_instances = len(active_instances)
            if num_instances == 0:
                logger.warning("No active instances found, using just this instance")
                num_instances = 1
                active_instances = {self.instance_id}
            
            # Sort instance IDs for consistent assignment
            sorted_instances = sorted(active_instances)
            try:
                instance_idx = sorted_instances.index(self.instance_id)
            except ValueError:
                logger.warning(f"Instance {self.instance_id} not in active instances, adding")
                instance_idx = len(sorted_instances)
                sorted_instances.append(self.instance_id)
            
            # Get all target IDs
            all_target_ids = list(self.redis.smembers(f"{self.targets_key}:all"))
            if not all_target_ids:
                logger.warning("No targets found in Redis, using all targets")
                return all_targets
            
            # Get existing assignments for this instance
            existing_assignments = self.redis.smembers(f"{self.assignments_key}:{self.instance_id}")
            
            # Calculate which targets should be assigned to this instance
            # Use a hash-based approach for more stable assignments
            assigned_target_ids = set()
            for target_id in all_target_ids:
                # Determine which instance owns this target
                # First check if already assigned
                owner = self.redis.hget(f"{self.targets_key}:ownership", target_id)
                
                if owner is None:
                    # Not assigned yet, use consistent hashing
                    hash_val = int(target_id[:8], 16)  # Use first 8 chars of hash as int
                    owner_idx = hash_val % num_instances
                    owner = sorted_instances[owner_idx]
                    # Record the ownership
                    self.redis.hset(f"{self.targets_key}:ownership", target_id, owner)
                
                if owner == self.instance_id:
                    assigned_target_ids.add(target_id)
                    # Record assignment in set
                    self.redis.sadd(f"{self.assignments_key}:{self.instance_id}", target_id)
            
            # Get the full target config for each assigned ID
            assigned_targets = []
            for target_id in assigned_target_ids:
                target_json = self.redis.hget(f"{self.targets_key}:details", target_id)
                if target_json:
                    try:
                        target_config = json.loads(target_json)
                        assigned_targets.append(target_config)
                    except:
                        logger.error(f"Error parsing target JSON for {target_id}")
            
            # Log assignment stats
            total_targets = len(all_target_ids)
            assigned_count = len(assigned_targets)
            logger.info(f"Advanced distribution: Assigned {assigned_count} targets to {self.instance_id} (out of {total_targets} total)")
            logger.info(f"Active instances: {sorted_instances}")
            
            # Save assignments for visibility
            assignments_data = {}
            for instance_id in active_instances:
                instance_targets = list(self.redis.smembers(f"{self.assignments_key}:{instance_id}"))
                instance_target_details = []
                for tid in instance_targets:
                    t_json = self.redis.hget(f"{self.targets_key}:details", tid)
                    if t_json:
                        try:
                            t_detail = json.loads(t_json)
                            instance_target_details.append(t_detail.get("event_name", tid))
                        except:
                            instance_target_details.append(tid)
                
                assignments_data[instance_id] = instance_target_details
            
            self.redis.hset(f"{self.targets_key}:summary", "last_updated", time.time())
            self.redis.hset(f"{self.targets_key}:summary", "assignments", json.dumps(assignments_data))
            
            return assigned_targets
            
        except Exception as e:
            logger.error(f"Error assigning targets: {e}")
            # Fall back to using all targets directly
            return all_targets
    
    def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire a distributed lock"""
        lock_key = f"{self.locks_key}:{lock_name}"
        try:
            # Try to set key with NX (only if it doesn't exist) and expiration
            result = self.redis.set(lock_key, self.instance_id, nx=True, ex=timeout)
            return bool(result)
        except Exception as e:
            logger.error(f"Error acquiring lock {lock_name}: {e}")
            return False
    
    def release_lock(self, lock_name: str) -> bool:
        """Release a distributed lock"""
        lock_key = f"{self.locks_key}:{lock_name}"
        try:
            # Only delete if this instance owns the lock
            pipe = self.redis.pipeline()
            pipe.watch(lock_key)
            lock_value = pipe.get(lock_key)
            
            if lock_value != self.instance_id:
                pipe.reset()
                return False
                
            pipe.multi()
            pipe.delete(lock_key)
            pipe.execute()
            return True
        except WatchError:
            logger.warning(f"Lock {lock_name} modified while releasing")
            return False
        except Exception as e:
            logger.error(f"Error releasing lock {lock_name}: {e}")
            return False
    
    def record_hit(self, target_id: str, hit_info: Dict) -> bool:
        """Record a ticket hit in the shared store"""
        try:
            hit_id = str(uuid.uuid4())
            hit_data = {
                "id": hit_id,
                "target_id": target_id,
                "instance_id": self.instance_id,
                "timestamp": time.time(),
                "details": hit_info
            }
            
            # Record the hit
            self.redis.hset(self.hits_key, hit_id, json.dumps(hit_data))
            
            # Update stats
            self.redis.hincrby(f"{self.stats_key}:{self.instance_id}", "hits_found", 1)
            
            # Publish hit notification to all instances
            self.redis.publish(f"{self.namespace}hits_channel", json.dumps({
                "type": "hit",
                "instance_id": self.instance_id,
                "target_id": target_id,
                "hit_id": hit_id,
                "timestamp": time.time()
            }))
            
            return True
        except Exception as e:
            logger.error(f"Error recording hit: {e}")
            return False
    
    def update_target_status(self, target_id: str, status: str) -> bool:
        """Update status for a target (checked, error, blocked, etc.)"""
        try:
            status_key = f"{self.targets_key}:status"
            self.redis.hset(status_key, target_id, json.dumps({
                "status": status,
                "updated_by": self.instance_id,
                "timestamp": time.time()
            }))
            
            # Increment check counter
            if status == "checked":
                self.redis.hincrby(f"{self.stats_key}:{self.instance_id}", "targets_checked", 1)
                
            return True
        except Exception as e:
            logger.error(f"Error updating target status: {e}")
            return False
    
    def get_work_stats(self) -> Dict:
        """Get statistics about workload distribution"""
        try:
            stats = {
                "instances": {},
                "targets": {
                    "total": 0,
                    "assigned": 0,
                    "unassigned": 0
                },
                "hits": {
                    "total": 0,
                    "by_instance": {}
                }
            }
            
            # Get instance stats
            all_instances = self.redis.hgetall(self.instances_key)
            active_heartbeats = self.redis.hgetall(self.heartbeats_key)
            
            for instance_id, instance_data in all_instances.items():
                try:
                    instance_info = json.loads(instance_data)
                    # Add heartbeat info
                    last_beat = active_heartbeats.get(instance_id)
                    is_active = False
                    
                    if last_beat:
                        last_beat_time = float(last_beat)
                        instance_info["last_heartbeat"] = last_beat_time
                        instance_info["is_active"] = time.time() - last_beat_time <= self.instance_timeout
                        is_active = instance_info["is_active"]
                    
                    # Get targets assigned to this instance
                    assigned_count = self.redis.scard(f"{self.assignments_key}:{instance_id}")
                    instance_info["assigned_targets"] = assigned_count
                    
                    # Get hit count
                    hits_found = self.redis.hget(f"{self.stats_key}:{instance_id}", "hits_found")
                    instance_info["hits_found"] = int(hits_found) if hits_found else 0
                    
                    # Add to stats
                    stats["instances"][instance_id] = instance_info
                    
                    # Update target counts
                    if is_active:
                        stats["targets"]["assigned"] += assigned_count
                        stats["hits"]["by_instance"][instance_id] = instance_info["hits_found"]
                        stats["hits"]["total"] += instance_info["hits_found"]
                        
                except Exception as e:
                    logger.error(f"Error processing instance data for {instance_id}: {e}")
            
            # Get total targets
            stats["targets"]["total"] = self.redis.scard(f"{self.targets_key}:all")
            stats["targets"]["unassigned"] = stats["targets"]["total"] - stats["targets"]["assigned"]
            
            return stats
        except Exception as e:
            logger.error(f"Error getting work stats: {e}")
            return {"error": str(e)}
    
    def __enter__(self):
        """Context manager entry"""
        self.register_instance()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.deregister_instance()
        
    async def wait_for_hit_notification(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        Wait for a hit notification from any instance.
        Requires asyncio integration, useful for GUI updates.
        """
        try:
            # Create a pubsub to listen for hit notifications
            pubsub = self.redis.pubsub()
            pubsub.subscribe(f"{self.namespace}hits_channel")
            
            # Check messages with timeout
            start_time = time.time()
            while timeout is None or time.time() - start_time < timeout:
                message = pubsub.get_message(timeout=0.1)
                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        return data
                    except:
                        continue
                
                # Small delay to prevent busy loop
                await asyncio.sleep(0.1)
                
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for hit notification: {e}")
            return None
        finally:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except:
                pass
