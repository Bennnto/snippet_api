from fastapi import FastAPI, Depends, Path, Query, HTTPException
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Optional

# Data Base Module
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://snippet_db_19se_user:snippet_db_19se_user@localhost:5432/snippet_db_19se")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enable CORS for all origins - MUST be first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class snipDB(Base):
    __tablename__ = "code"
    
    topic_id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    description = Column(String, nullable=True)
    code = Column(String)
    update = Column(DateTime, default=datetime.utcnow)
# Create Data Base
Base.metadata.create_all(bind=engine)
    
class CodeSnip(BaseModel):
    topic: str
    description: str | None = None
    code: str
    update: datetime = Field(default_factory=datetime.utcnow)

class CodeResponse(CodeSnip):
    topic_id: int    

class CodeEditRequest(BaseModel):
    old_code : str | None = None
    new_code : str
    
def get_db():
    db = SessionLocal()
    try :
        yield db
    finally:
        db.close()

@app.post("/snip/")
async def create_snip(code: CodeSnip, db: Session = Depends(get_db)):
    db_snip = snipDB(**code.dict())
    db.add(db_snip)
    db.commit()
    db.refresh(db_snip)
    return db_snip

@app.get("/snip/")
async def all_snip(db: Session = Depends(get_db)):
    return db.query(snipDB).all()

@app.get("/snip/{topic_id}", response_model=CodeResponse)
async def retrieve_snip(topic_id: int, db: Session = Depends(get_db)):
    code = db.query(snipDB).filter(snipDB.topic_id == topic_id).first()
    if code:
        return code
    return {"Message": "Cannot Retrieved Code"}

@app.put("/snip/{topic_id}", response_model=CodeResponse)
async def update_snip(topic_id: int, code: CodeSnip, db: Session = Depends(get_db)):
    db_code = db.query(snipDB).filter(snipDB.topic_id == topic_id).first()
    if db_code:
        for key, value in code.dict().items():
            setattr(db_code, key, value)
        db_code.update = datetime.utcnow()
        db.commit()
        db.refresh(db_code)
        return db_code
    return {"Message": "Not Found Code"}

@app.delete("/snip/{topic_id}")
async def delete_code(topic_id: int, db: Session = Depends(get_db)):
    db_code = db.query(snipDB).filter(snipDB.topic_id == topic_id).first()
    if db_code:
        db.delete(db_code)
        db.commit()
        return {"Message": "Delete Code"}
    return {"Message": "Not Found Code"}

@app.put("/snip/{topic_id}/edit")
async def edit_code(topic_id: int, edit_request: CodeEditRequest, db: Session = Depends(get_db)):
    db_code = db.query(snipDB).filter(snipDB.topic_id == topic_id).first()
    if not db_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snippet not found"
        )
    
    if edit_request.old_code:
        if edit_request.old_code not in db_code.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code block not found in snippet"
            )
        db_code.code = db_code.code.replace(edit_request.old_code, edit_request.new_code)
    else:
        db_code.code = edit_request.new_code
    
    db_code.update = datetime.utcnow()
    db.commit()
    db.refresh(db_code)
    
    return {
        "message": "Code updated successfully",
        "topic_id": db_code.topic_id,
        "updated_code": db_code.code,
        "update_timestamp": db_code.update
    }