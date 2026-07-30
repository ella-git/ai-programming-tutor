from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class SemanticKeywordEmbedding(Base):
    __tablename__ = "semantic_keyword_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    vector: Mapped[str] = mapped_column(Text, nullable=False)
