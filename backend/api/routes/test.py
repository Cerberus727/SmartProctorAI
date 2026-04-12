from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from api.models.database import get_db
from api.models.domain import Test, Question, Submission, Answer, ProctorLog, User
from api.schemas.schemas import TestCreate, ResponseModel, TestResponse, QuestionResponse, SubmissionSchema
from api.dependencies.auth import get_admin_user, get_current_user

router = APIRouter()

@router.post("/create", response_model=ResponseModel)
def create_test(test: TestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    db_test = Test(title=test.title, duration=test.duration, created_by=current_user.id)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)

    for q in test.questions:
        db_q = Question(
            test_id=db_test.id, question_text=q.question_text,
            option_a=q.option_a, option_b=q.option_b, option_c=q.option_c, option_d=q.option_d,
            correct_answer=q.correct_answer
        )
        db.add(db_q)
    db.commit()

    return ResponseModel(success=True, message="Test created successfully", data={"test_id": db_test.id})

@router.delete("/{test_id}", response_model=ResponseModel)
def delete_test(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    db.delete(test)
    db.commit()
    return ResponseModel(success=True, message="Test deleted successfully")     

@router.get("/list", response_model=ResponseModel)
def list_tests(db: Session = Depends(get_db)):
    tests = db.query(Test).all()
    test_list = [
        TestResponse(
            id=t.id,
            title=t.title,
            duration=t.duration,
            created_at=t.created_at,
            question_count=len(t.questions)
        ) for t in tests
    ]
    return ResponseModel(success=True, data=test_list)

@router.get("/{test_id}/questions", response_model=ResponseModel)
def get_questions(test_id: int, db: Session = Depends(get_db)):
    questions = db.query(Question).filter(Question.test_id == test_id).all()    
    q_list = [QuestionResponse(id=q.id, question_text=q.question_text, option_a=q.option_a, option_b=q.option_b, option_c=q.option_c, option_d=q.option_d) for q in questions]
    return ResponseModel(success=True, data=q_list)

@router.post("/submit", response_model=ResponseModel)
def submit_test(sub: SubmissionSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_sub = Submission(user_id=current_user.id, test_id=sub.test_id, score=sub.score)
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)

    for ans in sub.answers:
        db_ans = Answer(submission_id=db_sub.id, question_id=ans.question_id, selected_answer=ans.selected_answer)
        db.add(db_ans)
    db.commit()
    return ResponseModel(success=True, message="Test submitted successfully")   

@router.get("/submissions", response_model=ResponseModel)
def get_submissions(db: Session = Depends(get_db)):
    subs = db.query(Submission).order_by(Submission.submitted_at.desc()).all()
    data = []
    for s in subs:
        user = db.query(User).filter(User.id == s.user_id).first()
        test = db.query(Test).filter(Test.id == s.test_id).first()
        
        # Fetch proctor logs
        logs = db.query(ProctorLog).filter(ProctorLog.user_id == s.user_id, ProctorLog.test_id == s.test_id).all()
        log_data = [{"event_type": l.event_type, "timestamp": l.timestamp.isoformat()} for l in logs]
        
        data.append({
            "id": s.id, 
            "user_name": user.name if user else "Unknown",
            "test_title": test.title if test else "Unknown",
            "score": s.score, 
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "violations": log_data
        })
    return ResponseModel(success=True, data=data)
