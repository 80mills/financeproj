"""Account model for managing bank accounts, credit cards, loans, etc."""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, JSON, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from config.config import AccountType
import uuid
import enum


class AccountTypeEnum(str, enum.Enum):
    CHECKING = AccountType.CHECKING
    SAVINGS = AccountType.SAVINGS
    CREDIT_CARD = AccountType.CREDIT_CARD
    LOAN = AccountType.LOAN
    INVESTMENT = AccountType.INVESTMENT
    CASH = AccountType.CASH


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    account_type = Column(SQLEnum(AccountTypeEnum), nullable=False)
    
    # Entity relationship
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    
    # Account details
    institution_name = Column(String)
    account_number_masked = Column(String)  # Last 4 digits only
    routing_number = Column(String)
    
    # Balance information
    current_balance = Column(Numeric(precision=12, scale=2), default=0)
    available_balance = Column(Numeric(precision=12, scale=2), default=0)
    credit_limit = Column(Numeric(precision=12, scale=2))  # For credit cards
    minimum_payment = Column(Numeric(precision=12, scale=2))  # For credit cards/loans
    
    # Interest rates
    interest_rate = Column(Numeric(precision=5, scale=2))  # APR percentage
    
    # Plaid integration
    plaid_account_id = Column(String, unique=True)
    plaid_item_id = Column(String)
    plaid_access_token = Column(String)  # Encrypted
    
    # Status
    is_active = Column(Boolean, default=True)
    is_manual = Column(Boolean, default=False)  # True if manually entered, not from Plaid
    last_synced = Column(DateTime(timezone=True))
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    entity = relationship("Entity", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="account")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, type={self.account_type})>"