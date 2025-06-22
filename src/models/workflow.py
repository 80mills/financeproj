"""Workflow models for the visual workflow builder and automation"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, JSON, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from config.config import WorkflowNodeType, WorkflowStatus
import uuid
import enum


class WorkflowNodeTypeEnum(str, enum.Enum):
    SOURCE = WorkflowNodeType.SOURCE
    DESTINATION = WorkflowNodeType.DESTINATION
    CONDITION = WorkflowNodeType.CONDITION
    ACTION = WorkflowNodeType.ACTION
    SCHEDULE = WorkflowNodeType.SCHEDULE
    SPLIT = WorkflowNodeType.SPLIT
    MERGE = WorkflowNodeType.MERGE


class WorkflowStatusEnum(str, enum.Enum):
    DRAFT = WorkflowStatus.DRAFT
    ACTIVE = WorkflowStatus.ACTIVE
    PAUSED = WorkflowStatus.PAUSED
    ARCHIVED = WorkflowStatus.ARCHIVED


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Owner
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Status
    status = Column(SQLEnum(WorkflowStatusEnum), default=WorkflowStatusEnum.DRAFT)
    
    # Workflow configuration
    configuration = Column(JSON, nullable=False)  # Stores the visual layout
    
    # Trigger configuration
    trigger_type = Column(String)  # 'manual', 'schedule', 'event'
    trigger_config = Column(JSON)  # Cron expression, event type, etc.
    
    # Execution settings
    max_retries = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=300)
    
    # Version control
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)
    template_category = Column(String)
    
    # Analytics
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("User", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"


class WorkflowNode(Base, TimestampMixin):
    __tablename__ = "workflow_nodes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    
    # Node details
    node_type = Column(SQLEnum(WorkflowNodeTypeEnum), nullable=False)
    name = Column(String, nullable=False)
    
    # Position in visual editor
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    
    # Node configuration
    config = Column(JSON, nullable=False)  # Node-specific configuration
    
    # Connections
    input_connections = Column(JSON, default=list)  # List of node IDs
    output_connections = Column(JSON, default=list)  # List of node IDs
    
    # Execution order
    execution_order = Column(Integer)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")
    
    def __repr__(self):
        return f"<WorkflowNode(id={self.id}, type={self.node_type}, name={self.name})>"


class WorkflowExecution(Base, TimestampMixin):
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String, nullable=False)  # 'running', 'completed', 'failed', 'cancelled'
    error_message = Column(Text)
    
    # Trigger information
    triggered_by = Column(String)  # 'manual', 'schedule', 'event'
    trigger_details = Column(JSON)
    
    # Execution context
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # Node execution tracking
    node_executions = Column(JSON, default=dict)  # Node ID -> execution details
    
    # Performance metrics
    total_duration_ms = Column(Integer)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    transactions = relationship("Transaction", back_populates="workflow_execution")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"