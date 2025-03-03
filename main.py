from fastapi import FastAPI
from api.user import router as user_router
from api.test import router as test_router
from api.question import router as question_router
from api.topic import router as topic_router
from api.analytics import router as analytics_router

app = FastAPI()


app.include_router(user_router)
app.include_router(question_router)
app.include_router(topic_router)
app.include_router(analytics_router)
app.include_router(test_router)
