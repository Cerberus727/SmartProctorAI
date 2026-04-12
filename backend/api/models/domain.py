from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from api.models.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # 'admin' or 'student'
    
    tests_created = relationship("Test", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True)
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    duration = Column(Integer, default=60) # changed from duration_minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User", back_populates="tests_created")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan", passive_deletes=True)
    submissions = relationship("Submission", back_populates="test", cascade="all, delete-orphan", passive_deletes=True)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    question_text = Column(String)
    option_a = Column(String)
    option_b = Column(String)
    option_c = Column(String)
    option_d = Column(String)
    correct_answer = Column(String) # changed from correct_option
    test = relationship("Test", back_populates="questions")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="submissions")
    test = relationship("Test", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan", passive_deletes=True)

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    selected_answer = Column(String)
    
    submission = relationship("Submission", back_populates="answers")

class ProctorLog(Base):
    __tablename__ = "proctor_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
