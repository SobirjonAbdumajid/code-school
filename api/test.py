# test.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from schemas import TestCreate, TestResponse, TestDetailResponse, UserResponseCreate, UserResponseResponse
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from models import Test, Topic, Question, UserResponse, Option
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
    prefix="/tests",
    tags=["tests"]
)


@router.post("/", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def start_test(test: TestCreate, db: db_dependency, current_user: user_dependency):
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == test.topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Create new test
    test_data = Test(
        user_id=current_user["id"],
        topic_id=test.topic_id,
        started_at=datetime.now(),
        completed_at=None,
        score=None
    )

    db.add(test_data)
    db.commit()
    db.refresh(test_data)

    return test_data


@router.post("/{test_id}/responses", response_model=UserResponseResponse)
async def submit_response(
        test_id: int,
        response: UserResponseCreate,
        db: db_dependency,
        current_user: user_dependency
):
    # Check if test exists and belongs to current user
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    if test.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test"
        )

    # Check if test is still active
    if test.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test is already completed"
        )

    # Check if question exists
    question = db.query(Question).filter(Question.id == response.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Determine if response is correct
    is_correct = False

    # Handle different question types
    if question.question_type == "open_ended":
        # For open-ended, compare with correct answer
        if response.response_text and question.correct_answer:
            # This is a simple comparison - in a real app, you might want
            # more sophisticated matching for open-ended questions
            is_correct = response.response_text.lower() == question.correct_answer.lower()
    else:
        # For multiple choice or true/false, check if selected option is correct
        if response.option_id:
            option = db.query(Option).filter(
                Option.id == response.option_id,
                Option.question_id == question.id
            ).first()

            if not option:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Option not found or does not belong to this question"
                )

            is_correct = option.is_correct

    # Create user response
    user_response = UserResponse(
        test_id=test_id,
        question_id=response.question_id,
        option_id=response.option_id,
        response_text=response.response_text,
        is_correct=is_correct,
        submitted_at=datetime.now()
    )

    db.add(user_response)
    db.commit()
    db.refresh(user_response)

    return user_response


@router.put("/{test_id}/complete", response_model=TestDetailResponse)
async def complete_test(test_id: int, db: db_dependency, current_user: user_dependency):
    # Check if test exists and belongs to current user
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    if test.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test"
        )

    # Check if test is already completed
    if test.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test is already completed"
        )

    # Calculate score
    responses = db.query(UserResponse).filter(UserResponse.test_id == test_id).all()

    if not responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No responses found for this test"
        )

    correct_count = sum(1 for r in responses if r.is_correct)
    total_count = len(responses)
    score = (correct_count / total_count) * 100 if total_count > 0 else 0

    # Update test
    test.completed_at = datetime.now()
    test.score = score

    db.commit()
    db.refresh(test)

    return test


@router.get("/{test_id}", response_model=TestDetailResponse)
async def get_test(test_id: int, db: db_dependency, current_user: user_dependency):
    # Check if test exists and belongs to current user
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )

    if test.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test"
        )

    return test


@router.get("/", response_model=List[TestResponse])
async def get_user_tests(
        db: db_dependency,
        current_user: user_dependency,
        topic_id: Optional[int] = None,
        completed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
):
    # Base query for current user's tests
    query = db.query(Test).filter(Test.user_id == current_user["id"])

    # Apply filters if provided
    if topic_id:
        query = query.filter(Test.topic_id == topic_id)

    if completed is not None:
        if completed:
            query = query.filter(Test.completed_at != None)
        else:
            query = query.filter(Test.completed_at == None)

    # Get tests with pagination
    tests = query.order_by(Test.started_at.desc()).offset(skip).limit(limit).all()

    return tests
