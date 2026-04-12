from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime

class ResponseModel(BaseModel):
    success: bool
    data: Any = None
    message: str = ""

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class QuestionSchema(BaseModel):
    question_text: str = Field(..., min_length=1)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_answer: str = Field(..., pattern="^[A-D]$")

class TestCreate(BaseModel):
    title: str = Field(..., min_length=3)
    duration: int = Field(..., gt=0)
    questions: List[QuestionSchema] = Field(..., min_items=1)

class TestResponse(BaseModel):
    id: int
    title: str
    duration: int
    created_at: datetime
    question_count: int = 0
    
class QuestionResponse(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

class AnswerSchema(BaseModel):
    question_id: int
    selected_answer: str

class SubmissionSchema(BaseModel):
    test_id: int
    score: float
    answers: List[AnswerSchema] = []
