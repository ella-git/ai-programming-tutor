from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class SemanticAnalysisConfig(Base):
    __tablename__ = "semantic_analysis_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
