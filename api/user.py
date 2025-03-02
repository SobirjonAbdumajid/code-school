from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/")
async def get_users():
    pass


@router.post("/register/")
async def register():
    pass


@router.post("/login/")
async def login():
    pass


@router.post("/logout/")
async def logout():
    pass


@router.post("/reset/")
async def reset():
    pass



