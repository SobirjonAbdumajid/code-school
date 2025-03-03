from database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, ForeignKey
from datetime import datetime
from typing import Optional


class UserResponse(Base):
    __tablename__ = 'user_responses'

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    option_id: Mapped[Optional[int]] = mapped_column(ForeignKey('options.id'), nullable=True)
    response_text: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(server_default=func.now())
