from database import Base
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy import ForeignKey
from enum import Enum as PyEnum


class QuestionType(PyEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"


class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'), nullable=False)
    question_text: Mapped[str] = mapped_column(nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(nullable=False)
    difficulty: Mapped[int] = mapped_column(nullable=False)
    correct_answer: Mapped[Optional[str]] = mapped_column(nullable=True)
