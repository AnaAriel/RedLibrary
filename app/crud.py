from sqlalchemy.orm import Session
from . import models

def create_book(db: Session, book_data: dict):
    db_book = models.Book(
        title=book_data["title"],
        author=book_data.get("author", ""),
        description=book_data.get("description", ""),
        url=book_data.get("url", ""),
        image=book_data.get("image", "")
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_books(db: Session):
    return db.query(models.Book).all()