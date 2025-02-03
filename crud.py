# File: crud.py
from sqlalchemy.orm import Session
import models
import schemas
import uuid
from typing import List

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_chat_message(db: Session, message: schemas.ChatMessageCreate, user_id: str):
    db_message = models.ChatMessage(
        user_id=user_id,
        content=message.content,
        id=str(uuid.uuid4())
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history(db: Session, user_id: str, limit: int = 100):
    return db.query(models.ChatMessage)\
        .filter(models.ChatMessage.user_id == user_id)\
        .order_by(models.ChatMessage.timestamp.desc())\
        .limit(limit)\
        .all()

def create_file(db: Session, filename: str, user_id: str, blob_url: str, size: int):
    db_file = models.File(
        user_id=user_id,
        filename=filename,
        size=size,
        blob_url=blob_url,
        id=str(uuid.uuid4())
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_user_files(db: Session, user_id: str):
    return db.query(models.File)\
        .filter(models.File.user_id == user_id)\
        .order_by(models.File.upload_date.desc())\
        .all()

def delete_file(db: Session, file_id: str):
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False