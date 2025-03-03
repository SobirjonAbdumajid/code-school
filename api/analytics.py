# analytics.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from schemas import UserPerformanceResponse, TopicPerformanceResponse, QuestionDifficultyResponse
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Test, Topic, Question, UserResponse
from database import SessionLocal
from auth import get_current_user
from datetime import datetime, timedelta


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@router.get("/performance/user", response_model=UserPerformanceResponse)
async def get_user_performance(
        db: db_dependency,
        current_user: user_dependency,
        period: Optional[str] = Query("all", enum=["week", "month", "year", "all"]),
):
    # Base query for completed tests by current user
    query = db.query(Test).filter(
        Test.user_id == current_user["id"],
        Test.completed_at != None
    )

    # Apply time period filter
    if period == "week":
        start_date = datetime.now() - timedelta(days=7)
        query = query.filter(Test.completed_at >= start_date)
    elif period == "month":
        start_date = datetime.now() - timedelta(days=30)
        query = query.filter(Test.completed_at >= start_date)
    elif period == "year":
        start_date = datetime.now() - timedelta(days=365)
        query = query.filter(Test.completed_at >= start_date)

    # Get tests
    tests = query.all()

    if not tests:
        return {
            "total_tests": 0,
            "average_score": 0,
            "best_score": 0,
            "worst_score": 0,
            "recent_scores": [],
            "completion_rate": 0
        }

    # Calculate statistics
    total_tests = len(tests)
    average_score = sum(test.score for test in tests) / total_tests if total_tests > 0 else 0
    best_score = max(test.score for test in tests) if total_tests > 0 else 0
    worst_score = min(test.score for test in tests) if total_tests > 0 else 0

    # Get recent scores (last 5 tests)
    recent_tests = query.order_by(Test.completed_at.desc()).limit(5).all()
    recent_scores = [{"date": test.completed_at, "score": test.score} for test in recent_tests]

    # Calculate completion rate (completed tests / total started tests)
    all_tests_count = db.query(func.count(Test.id)).filter(Test.user_id == current_user["id"]).scalar()
    completion_rate = (total_tests / all_tests_count) * 100 if all_tests_count > 0 else 0

    return {
        "total_tests": total_tests,
        "average_score": round(average_score, 2),
        "best_score": best_score,
        "worst_score": worst_score,
        "recent_scores": recent_scores,
        "completion_rate": round(completion_rate, 2)
    }


@router.get("/performance/topics", response_model=List[TopicPerformanceResponse])
async def get_topic_performance(db: db_dependency, current_user: user_dependency):
    # Query to get performance metrics by topic
    topic_stats = db.query(
        Topic.id,
        Topic.name,
        func.count(Test.id).label("tests_count"),
        func.avg(Test.score).label("average_score"),
        func.max(Test.score).label("best_score")
    ).join(
        Test, Test.topic_id == Topic.id
    ).filter(
        Test.user_id == current_user["id"],
        Test.completed_at != None
    ).group_by(
        Topic.id
    ).all()

    result = []
    for topic_id, name, tests_count, avg_score, best_score in topic_stats:
        # Get question count for this topic
        question_count = db.query(func.count(Question.id)).filter(
            Question.topic_id == topic_id
        ).scalar()

        # Get tests with perfect scores
        perfect_scores = db.query(func.count(Test.id)).filter(
            Test.topic_id == topic_id,
            Test.user_id == current_user["id"],
            Test.score == 100.0
        ).scalar()

        result.append({
            "topic_id": topic_id,
            "topic_name": name,
            "tests_taken": tests_count,
            "average_score": round(avg_score, 2) if avg_score else 0,
            "best_score": best_score if best_score else 0,
            "question_count": question_count,
            "perfect_scores": perfect_scores
        })

    return result


@router.get("/questions/difficulty", response_model=List[QuestionDifficultyResponse])
async def get_question_difficulty_analysis(
        db: db_dependency,
        current_user: user_dependency,
        topic_id: Optional[int] = None

):
    # Base query for questions with response stats
    query = db.query(
        Question.id,
        Question.question_text,
        Question.difficulty,
        func.count(UserResponse.id).label("attempts"),
        func.sum(case((UserResponse.is_correct == True, 1), else_=0)).label("correct_answers")
    ).join(
        UserResponse, UserResponse.question_id == Question.id
    ).join(
        Test, Test.id == UserResponse.test_id
    ).filter(
        Test.user_id == current_user["id"]
    )

    # Apply topic filter if provided
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)

    # Group and execute query
    stats = query.group_by(Question.id).all()

    result = []
    for q_id, q_text, difficulty, attempts, correct in stats:
        success_rate = (correct / attempts) * 100 if attempts > 0 else 0

        # Compare actual difficulty with rated difficulty
        perceived_difficulty = 5 - int((success_rate / 100) * 4)  # Scale 1-5 where 5 is most difficult

        result.append({
            "question_id": q_id,
            "question_text": q_text,
            "rated_difficulty": difficulty,
            "attempts": attempts,
            "success_rate": round(success_rate, 2),
            "perceived_difficulty": perceived_difficulty
        })

    # Sort by success rate ascending (hardest questions first)
    result.sort(key=lambda x: x["success_rate"])

    return result