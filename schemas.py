from pydantic import BaseModel


class UserBase(BaseModel):
    first_name: str
    username: str
    phone: str
    password: str
