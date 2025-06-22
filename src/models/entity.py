"""Entity model for managing LLC and personal entities"""

from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from config.config import EntityType
import uuid
import enum


class EntityTypeEnum(str, enum.Enum):
    PERSONAL = EntityType.PERSONAL
    BUSINESS = EntityType.BUSINESS
    LLC = EntityType.LLC
    CORPORATION = EntityType.CORPORATION


class Entity(Base, TimestampMixin):
    __tablename__ = "entities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    entity_type = Column(SQLEnum(EntityTypeEnum), nullable=False)
    
    # Owner
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Business details (optional)
    ein = Column(String)  # Employer Identification Number
    business_name = Column(String)
    business_address = Column(JSON)
    formation_date = Column(String)
    state_of_formation = Column(String)
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Relationships
    owner = relationship("User", back_populates="entities")
    accounts = relationship("Account", back_populates="entity", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="entity", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="entity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Entity(id={self.id}, name={self.name}, type={self.entity_type})>"