"""Budget models for zero-based budgeting and allocations"""

from sqlalchemy import Column, String, ForeignKey, JSON, Numeric, Date, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import uuid


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    
    # Entity relationship
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    
    # Budget period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Total budget amount
    total_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    
    # Budget type
    budget_type = Column(String, default="monthly")  # 'monthly', 'quarterly', 'yearly', 'custom'
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Relationships
    entity = relationship("Entity", back_populates="budgets")
    allocations = relationship("BudgetAllocation", back_populates="budget", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name={self.name}, amount={self.total_amount})>"


class BudgetAllocation(Base, TimestampMixin):
    __tablename__ = "budget_allocations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id = Column(String, ForeignKey("budgets.id"), nullable=False)
    
    # Allocation details
    category = Column(String, nullable=False)
    subcategory = Column(String)
    
    # Amounts
    allocated_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    spent_amount = Column(Numeric(precision=12, scale=2), default=0)
    remaining_amount = Column(Numeric(precision=12, scale=2), default=0)
    
    # Percentage of total budget
    percentage = Column(Numeric(precision=5, scale=2))
    
    # Envelope budgeting
    is_envelope = Column(Boolean, default=False)
    rollover_enabled = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String)
    
    # Relationships
    budget = relationship("Budget", back_populates="allocations")
    
    def __repr__(self):
        return f"<BudgetAllocation(id={self.id}, category={self.category}, amount={self.allocated_amount})>"