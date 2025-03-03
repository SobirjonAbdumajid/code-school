# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    full_name: str
    username: str
    phone: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    phone: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetConfirm(BaseModel):
    username: str
    token: str
    new_password: str


# Topic schemas
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TopicResponse(TopicBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class TopicDetailResponse(TopicResponse):
    question_count: int

    class Config:
        orm_mode = True


# Question schemas
class OptionBase(BaseModel):
    option_text: str
    is_correct: bool = False


class OptionCreate(OptionBase):
    pass


class OptionResponse(OptionBase):
    id: int
    question_id: int

    class Config:
        orm_mode = True


class QuestionBase(BaseModel):
    topic_id: int
    question_text: str
    question_type: str  # "multiple_choice", "true_false", "open_ended"
    difficulty: int = Field(ge=1, le=5)
    correct_answer: Optional[str] = None  # For open-ended questions


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    topic_id: Optional[int] = None
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    correct_answer: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: int

    class Config:
        orm_mode = True


class QuestionDetailResponse(QuestionResponse):
    options: List[OptionResponse] = []

    class Config:
        orm_mode = True


# Test schemas
class TestBase(BaseModel):
    topic_id: int


class TestCreate(TestBase):
    pass


class TestResponse(TestBase):
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    score: Optional[float] = None

    class Config:
        orm_mode = True


class UserResponseBase(BaseModel):
    question_id: int
    option_id: Optional[int] = None  # For multiple choice
    response_text: Optional[str] = None  # For open-ended


class UserResponseCreate(UserResponseBase):
    pass


class UserResponseResponse(UserResponseBase):
    id: int
    test_id: int
    is_correct: bool
    submitted_at: datetime

    class Config:
        orm_mode = True


class TestDetailResponse(TestResponse):
    topic_name: str
    responses: List[UserResponseResponse] = []

    class Config:
        orm_mode = True


# Analytics schemas
class ScoreRecord(BaseModel):
    date: datetime
    score: float


class UserPerformanceResponse(BaseModel):
    total_tests: int
    average_score: float
    best_score: float
    worst_score: float
    recent_scores: List[ScoreRecord]
    completion_rate: float  # Percentage of started tests that were completed


class TopicPerformanceResponse(BaseModel):
    topic_id: int
    topic_name: str
    tests_taken: int
    average_score: float
    best_score: float
    question_count: int
    perfect_scores: int  # Number of tests with 100% score


class QuestionDifficultyResponse(BaseModel):
    question_id: int
    question_text: str
    rated_difficulty: int  # The difficulty rating assigned (1-5)
    attempts: int  # Number of times this question was answered
    success_rate: float  # Percentage of correct answers
    perceived_difficulty: int  # Calculated difficulty based on success rate (1-5)
