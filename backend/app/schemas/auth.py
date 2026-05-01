from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    model_config = {"str_strip_whitespace": True}


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    model_config = {"from_attributes": True}


class RegisterRequest(UserCreate):
    pass


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
