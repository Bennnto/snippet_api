from fastapi import FastAPI, Depends, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from datetime import datetime


# Data Base Module
from sqlalchemy import create_engine, Column,  Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


app = FastAPI()
DATABASE_URL = "sqlite:///./snip.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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