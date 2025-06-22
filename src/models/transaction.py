"""Transaction model for tracking all financial movements"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, JSON, Numeric, DateTime, Boolean, Text, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from config.config import TransactionType, InterEntityTransferType
import uuid
import enum


class TransactionTypeEnum(str, enum.Enum):
    DEBIT = TransactionType.DEBIT
    CREDIT = TransactionType.CREDIT
    TRANSFER = TransactionType.TRANSFER


class InterEntityTransferTypeEnum(str, enum.Enum):
    EQUITY_CONTRIBUTION = InterEntityTransferType.EQUITY_CONTRIBUTION
    OWNER_DRAW = InterEntityTransferType.OWNER_DRAW
    DISTRIBUTION = InterEntityTransferType.DISTRIBUTION
    LOAN_TO_ENTITY = InterEntityTransferType.LOAN_TO_ENTITY
    LOAN_FROM_ENTITY = InterEntityTransferType.LOAN_FROM_ENTITY
    EXPENSE_REIMBURSEMENT = InterEntityTransferType.EXPENSE_REIMBURSEMENT


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transaction_date", "transaction_date"),
        Index("idx_entity_date", "entity_id", "transaction_date"),
        Index("idx_account_date", "account_id", "transaction_date"),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core fields
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    transaction_type = Column(SQLEnum(TransactionTypeEnum), nullable=False)
    
    # Transaction details
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    posted_date = Column(DateTime(timezone=True))
    
    # Description and categorization
    description = Column(String, nullable=False)
    merchant_name = Column(String)
    category = Column(String)
    subcategory = Column(String)
    tags = Column(JSON, default=list)
    
    # Inter-entity transfer tracking
    is_inter_entity = Column(Boolean, default=False)
    inter_entity_type = Column(SQLEnum(InterEntityTransferTypeEnum))
    related_transaction_id = Column(String, ForeignKey("transactions.id"))
    related_entity_id = Column(String, ForeignKey("entities.id"))
    
    # Workflow tracking
    workflow_execution_id = Column(String, ForeignKey("workflow_executions.id"))
    
    # External references
    plaid_transaction_id = Column(String, unique=True)
    bank_reference = Column(String)
    check_number = Column(String)
    
    # Status and flags
    is_pending = Column(Boolean, default=False)
    is_reconciled = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    
    # Notes and attachments
    notes = Column(Text)
    attachments = Column(JSON, default=list)  # List of file references
    
    # Audit fields
    imported_at = Column(DateTime(timezone=True))
    import_source = Column(String)  # 'plaid', 'csv', 'manual', etc.
    
    # Relationships
    entity = relationship("Entity", back_populates="transactions", foreign_keys=[entity_id])
    account = relationship("Account", back_populates="transactions")
    related_transaction = relationship("Transaction", remote_side=[id], foreign_keys=[related_transaction_id])
    workflow_execution = relationship("WorkflowExecution", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, date={self.transaction_date})>"