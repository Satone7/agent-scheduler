from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import datetime
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SchedulerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

@dataclass
class SchedulerConfig:
    """
    Configuration settings for the Agent Scheduler.
    """
    max_concurrent_tasks: int = 5
    poll_interval_seconds: int = 10
    retry_limit: int = 3
    timeout_seconds: Optional[int] = None
    extra_options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SchedulerState:
    """
    Tracks the current state and metrics of the Agent Scheduler.
    """
    status: SchedulerStatus = SchedulerStatus.IDLE
    active_tasks: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_update: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

@dataclass
class AgentTask:
    """
    Represents an actionable task for an Agent.
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unnamed Task"
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    
    # Timestamps
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    
    # Execution Details
    retry_count: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
