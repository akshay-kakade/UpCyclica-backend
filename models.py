from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from db import Base
from datetime import datetime

class WasteSubmission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=False), primary_key=True)
    user_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    file_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    suggested_method = Column(String, nullable=True)
    roi_estimate = Column(String, nullable=True)
    co2_saved_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ New fields
    waste_type = Column(String, nullable=True)
    source = Column(String, nullable=True)
    batch_weight = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
