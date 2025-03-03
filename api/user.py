from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schemas import UserBase, Token, UserResponse
from typing import Annotated, List
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal
from auth import get_current_user, create_access_token, verify_password
from passlib.context import CryptContext
from datetime import datetime, timedelta
from settings import get_settings

settings = get_settings()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ACCESS_TOKEN_EXPIRE_MINUTES = 30
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_URL)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/", response_model=List[UserResponse])
async def get_users(db: db_dependency, current_user: user_dependency):
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all users"
        )

    users = db.query(User).all()
    return users


@router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(db: db_dependency, user: UserBase):

    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_phone = db.query(User).filter(User.phone == user.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )

    user_data = User(
        full_name=user.full_name,
        username=user.username,
        phone=user.phone,
        password_hash=bcrypt_context.hash(user.password),
        created_at=datetime.now()
    )
    db.add(user_data)
    db.commit()
    db.refresh(user_data)

    return UserResponse(
        id=user_data.id,
        full_name=user_data.full_name,
        username=user_data.username,
        phone=user_data.phone,
        created_at=user_data.created_at
    )


@router.post("/login/", response_model=Token)
async def login(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout/", status_code=status.HTTP_200_OK)
async def logout(current_user: user_dependency):
    return {"message": "Successfully logged out", "user": current_user["username"]}


# @router.post("/reset/", status_code=status.HTTP_200_OK)
# async def reset(reset_request: PasswordResetRequest, db: db_dependency):
#     # Find user by username
#     user = db.query(User).filter(User.username == reset_request.username).first()
#
#     # Don't reveal if user exists for security reasons
#     if not user:
#         return {"message": "If account exists, a password reset link has been sent to your email"}
#
#     # In a real application, you would:
#     # 1. Generate a reset token
#     # 2. Store the token with an expiration time
#     # 3. Send an email with a reset link
#
#     # Example of token generation (not stored or sent in this example)
#     reset_token = create_access_token(
#         data={"sub": user.username, "purpose": "password_reset"},
#         expires_delta=timedelta(hours=1)
#     )
#
#     # Simulate email sending
#     # send_reset_email(user.email, reset_token)
#
#     return {"message": "If account exists, a password reset link has been sent to your email"}
#
#
# @router.post("/reset-confirm/")
# async def reset_confirm(token: str, new_password: str, db: db_dependency):
#     # Validate token
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         username = payload.get("sub")
#         purpose = payload.get("purpose")
#
#         if not username or purpose != "password_reset":
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid reset token"
#             )
#
#         # Find user
#         user = db.query(User).filter(User.username == username).first()
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
#
#         # Update password
#         user.password_hash = bcrypt_context.hash(new_password)
#         db.commit()
#
#         return {"message": "Password updated successfully"}
#
#     except jwt.PyJWTError:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired token"
#         )
#
#
# @router.get("/me/", response_model=UserResponse)
# async def get_current_user_info(current_user: user_dependency, db: db_dependency):
#     user = db.query(User).filter(User.id == current_user["id"]).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
#
#     return user
