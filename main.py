from fastapi import FastAPI, Depends, Path, Query, HTTPException, status
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Optional, Annotated

# Data Base Module
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# For Create Password / Username
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials

load_dotenv()

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- HTML Page Routes ---
@app.get("/home", response_class=FileResponse)
async def serve_home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/edit", response_class=FileResponse)
async def serve_edit():
    return FileResponse(os.path.join(BASE_DIR, "edit.html"))

@app.get("/index", response_class=FileResponse)
async def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "addendum.html"))

security = HTTPBasic()
# Use PostgreSQL on Render (set DATABASE_URL env var), fall back to SQLite locally
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///snipDB.db")

# SQLAlchemy requires "postgresql://" not "postgres://" (Render uses the old prefix)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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

# Association table for many-to-many relationship
snippet_tags = Table(
    'snippet_tags',
    Base.metadata,
    Column('snippet_id', Integer, ForeignKey('code.topic_id')),
    Column('tag_id', Integer, ForeignKey('tag.tag_id'))
)

class snipDB(Base):
    __tablename__ = "code"
    
    topic_id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    description = Column(String, nullable=True)
    code = Column(String)
    category_id = Column(Integer, ForeignKey("category.category_id"), nullable=True)
    update = Column(DateTime, default=datetime.utcnow)
    
    category = relationship("Category", back_populates="snippets")
    tags = relationship("Tag", secondary=snippet_tags)
# Create Data Base
Base.metadata.create_all(bind=engine)

class CodeEditRequest(BaseModel):
    old_code : str | None = None
    new_code : str
    
class Category(Base):
    __tablename__ = "category"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, index=True, nullable=False)
    color = Column(String, default="#007BFF")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    snippets = relationship("snipDB", back_populates="category")

class Tag(Base):
    __tablename__ = "tag"
    tag_id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String, index=True)

class Create_Category(BaseModel):
    category_name : str 
    color : str 
    
class Create_Tag(BaseModel):
    tag_name : str
    
class Category_Response(BaseModel):
    category_id : int
    category_name : str 
    color : str 
    
class Tag_Response(BaseModel):
    tag_id : int
    tag_name : str 
    
class CodeSnip(BaseModel):
    topic: str
    description: str | None = None
    code: str
    category_id: Optional[int] = None
    tag_ids: Optional[list[int]] = []
    update: datetime = Field(default_factory=datetime.utcnow)

class CodeResponse(CodeSnip):
    topic_id: int    
    category: Optional[Category_Response] = None
    tags: list[Tag_Response] = []
    
        
def get_db():
    db = SessionLocal()
    try :
        yield db
    finally:
        db.close()

def get_current_username(credentials: Annotated[HTTPBasicCredentials, Depends(security)],):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"Benpromkaew"
    is_correct_username = secrets.compare_digest(current_username_bytes, correct_username_bytes)
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"Ben107468"
    is_correct_password = secrets.compare_digest(current_password_bytes, correct_password_bytes)
    if not (is_correct_password and is_correct_username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect username or password",
            headers = { "WWW-Authenticate": "Basic" }
        )
        return credentials.username, credentials.password

# ==== User Endpoint ==== #
@app.get("/users/me")
def read_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    return {"username":credentials.username, "password":credentials.password}

# ====== Tag Endpoint ====== #
@app.post("/tags", response_model=Tag_Response, dependencies=[Depends(get_current_username)])
def create_tag(tag: Create_Tag, db: Session = Depends(get_db)):
    db_tag = Tag(tag_name=tag.tag_name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@app.get("/tags", response_model=list[Tag_Response])
def list_tag(db: Session = Depends(get_db)):
    return db.query(Tag).all()

@app.delete("/tags/{tag_id}", dependencies=[Depends(get_current_username)])
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.tag_id == tag_id).first()
    if not tag :
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted"}

# ===== Category Endpoint ====== #
@app.post("/categories", response_model=Category_Response, dependencies=[Depends(get_current_username)])
def create_category(category: Create_Category, db: Session = Depends(get_db)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get('/categories', response_model=list[Category_Response])
def list_category(db: Session = Depends(get_db)):
    category = db.query(Category).all()
    return category

@app.get('/categories/{category_id}', response_model=Category_Response)
def get_category(category_id:int, db : Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.delete("/categories/{category_id}", dependencies=[Depends(get_current_username)])
def delete_category(category_id:int, db : Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}

# ==== Snippet Endpoint ==== #
@app.post("/snip/", response_model=CodeResponse, dependencies=[Depends(get_current_username)])
async def create_snip(code: CodeSnip, db: Session = Depends(get_db)):
    db_snip = snipDB(
        topic=code.topic,
        description=code.description,
        code=code.code,
        category_id=code.category_id
    )
    if code.tag_ids:
        tags = db.query(Tag).filter(Tag.tag_id.in_(code.tag_ids)).all()
        db_snip.tags = tags
        
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
