"""Code Sequence model for auto-generated codes."""
from sqlalchemy import Column, Integer, String, UniqueConstraint

from app.database import Base


class CodeSequence(Base):
    __tablename__ = "code_sequences"
    __table_args__ = (
        UniqueConstraint("entity_type", "date_part", name="uq_code_seq_entity_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(32), nullable=False)
    prefix = Column(String(16), nullable=False)
    date_part = Column(String(8), nullable=False)
    current_seq = Column(Integer, nullable=False, default=0)
