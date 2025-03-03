from database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey


class Option(Base):
    __tablename__ = 'options'

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    option_text: Mapped[str] = mapped_column(nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)
