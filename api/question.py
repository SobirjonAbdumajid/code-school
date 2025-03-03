# question.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from schemas import QuestionCreate, QuestionUpdate, QuestionResponse, QuestionDetailResponse, OptionCreate, \
    OptionResponse
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from models import Question, Topic, Option
from database import SessionLocal
from auth import get_current_user
from datetime import datetime


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter(
    prefix="/questions",
    tags=["questions"]
)


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(question: QuestionCreate, db: db_dependency, current_user: user_dependency):
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == question.topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Validate question type
    valid_types = ["multiple_choice", "true_false", "open_ended"]
    if question.question_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question type must be one of: {', '.join(valid_types)}"
        )

    # Validate difficulty
    if question.difficulty < 1 or question.difficulty > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Difficulty must be between 1 and 5"
        )

    question_data = Question(
        topic_id=question.topic_id,
        question_text=question.question_text,
        question_type=question.question_type,
        difficulty=question.difficulty,
        correct_answer=question.correct_answer if question.question_type == "open_ended" else None
    )

    db.add(question_data)
    db.commit()
    db.refresh(question_data)

    return question_data


@router.post("/{question_id}/options", response_model=OptionResponse)
async def create_option(
        question_id: int,
        option: OptionCreate,
        db: db_dependency,
        current_user: user_dependency
):
    # Check if question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Check if question is multiple choice or true/false
    if question.question_type == "open_ended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add options to open-ended questions"
        )

    option_data = Option(
        question_id=question_id,
        option_text=option.option_text,
        is_correct=option.is_correct
    )

    db.add(option_data)
    db.commit()
    db.refresh(option_data)

    return option_data


@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
        db: db_dependency,
        topic_id: Optional[int] = None,
        difficulty: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
):
    query = db.query(Question)

    # Apply filters if provided
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.offset(skip).limit(limit).all()
    return questions


@router.get("/{question_id}", response_model=QuestionDetailResponse)
async def get_question(question_id: int, db: db_dependency):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
        question_id: int,
        question_update: QuestionUpdate,
        db: db_dependency,
        current_user: user_dependency
):
    # Check if question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Check topic if being updated
    if question_update.topic_id:
        topic = db.query(Topic).filter(Topic.id == question_update.topic_id).first()
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        question.topic_id = question_update.topic_id

    # Update other fields if provided
    if question_update.question_text:
        question.question_text = question_update.question_text

    if question_update.question_type:
        valid_types = ["multiple_choice", "true_false", "open_ended"]
        if question_update.question_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question type must be one of: {', '.join(valid_types)}"
            )
        question.question_type = question_update.question_type

    if question_update.difficulty:
        if question_update.difficulty < 1 or question_update.difficulty > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Difficulty must be between 1 and 5"
            )
        question.difficulty = question_update.difficulty

    if question_update.correct_answer is not None:
        if question.question_type == "open_ended":
            question.correct_answer = question_update.correct_answer
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Correct answer can only be set for open-ended questions"
            )

    db.commit()
    db.refresh(question)

    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: db_dependency, current_user: user_dependency):
    # Check if question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Delete question (and associated options via cascade)
    db.delete(question)
    db.commit()

    return None

