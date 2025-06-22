"""Bill models for managing recurring payments and bills"""

from sqlalchemy import Column, String, ForeignKey, JSON, Numeric, Date, Boolean, Integer
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
import uuid


class Bill(Base, TimestampMixin):
    __tablename__ = "bills"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    
    # Account relationship
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    
    # Bill details
    payee = Column(String, nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    
    # Due date configuration
    due_day = Column(Integer)  # Day of month (1-31)
    frequency = Column(String, default="monthly")  # 'monthly', 'quarterly', 'yearly', 'custom'
    custom_frequency_days = Column(Integer)  # For custom frequency
    
    # Auto-pay settings
    auto_pay_enabled = Column(Boolean, default=False)
    auto_pay_days_before = Column(Integer, default=1)  # Pay X days before due
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Category
    category = Column(String)
    
    # Notification settings
    reminder_enabled = Column(Boolean, default=True)
    reminder_days_before = Column(Integer, default=3)
    
    # Additional details
    account_number = Column(String)  # Bill account number (encrypted)
    notes = Column(String)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    account = relationship("Account", back_populates="bills")
    payments = relationship("BillPayment", back_populates="bill", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Bill(id={self.id}, name={self.name}, amount={self.amount})>"


class BillPayment(Base, TimestampMixin):
    __tablename__ = "bill_payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = Column(String, ForeignKey("bills.id"), nullable=False)
    
    # Payment details
    amount_paid = Column(Numeric(precision=12, scale=2), nullable=False)
    payment_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Transaction reference
    transaction_id = Column(String, ForeignKey("transactions.id"))
    
    # Status
    status = Column(String, default="pending")  # 'pending', 'completed', 'failed', 'cancelled'
    
    # Payment method
    payment_method = Column(String)  # 'auto', 'manual', 'workflow'
    
    # Confirmation
    confirmation_number = Column(String)
    
    # Notes
    notes = Column(String)
    
    # Relationships
    bill = relationship("Bill", back_populates="payments")
    
    def __repr__(self):
        return f"<BillPayment(id={self.id}, bill_id={self.bill_id}, amount={self.amount_paid})>"