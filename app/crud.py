from sqlalchemy.orm import Session
from . import models

def create_book(db: Session, book_data: dict):
    db_book = models.Book(
        title=book_data["title"],
        author=book_data.get("author", "Desconhecido"),
        description=book_data.get("description", "Descrição não disponível"),
        url=book_data.get("url", ""),
        image=book_data.get("cover_url", "")  # <- campo retornado pela função get_book_data
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_books(db: Session):
    return db.query(models.Book).all()