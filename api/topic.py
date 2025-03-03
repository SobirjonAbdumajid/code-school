# topic.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from schemas import TopicCreate, TopicUpdate, TopicResponse, TopicDetailResponse
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session
from models import Topic
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
    prefix="/topics",
    tags=["topics"]
)


@router.post("/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(topic: TopicCreate, db: db_dependency, current_user: user_dependency):
    # Check if topic with same name exists
    existing_topic = db.query(Topic).filter(Topic.name == topic.name).first()
    if existing_topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic with this name already exists"
        )

    topic_data = Topic(
        name=topic.name,
        description=topic.description,
        created_at=datetime.now()
    )

    db.add(topic_data)
    db.commit()
    db.refresh(topic_data)

    return topic_data


@router.get("/", response_model=List[TopicResponse])
async def get_topics(
        db: db_dependency,
        skip: int = 0,
        limit: int = 100,
):
    topics = db.query(Topic).offset(skip).limit(limit).all()
    return topics


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(topic_id: int, db: db_dependency):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    return topic


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
        topic_id: int,
        topic_update: TopicUpdate,
        db: db_dependency,
        current_user: user_dependency
):
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Check for name conflict if name is being updated
    if topic_update.name and topic_update.name != topic.name:
        existing_topic = db.query(Topic).filter(Topic.name == topic_update.name).first()
        if existing_topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic with this name already exists"
            )

    # Update fields
    if topic_update.name:
        topic.name = topic_update.name
    if topic_update.description:
        topic.description = topic_update.description

    db.commit()
    db.refresh(topic)

    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: int, db: db_dependency, current_user: user_dependency):
    # Check if topic exists
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    # Delete topic
    db.delete(topic)
    db.commit()

    return None

