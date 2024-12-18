from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
