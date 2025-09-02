# app/crud.py

from sqlalchemy.orm import Session
from . import models

# -------------------------------
# CRUD de Usuários (Existente)
# -------------------------------
def create_user(db: Session, full_name: str, email: str, password_hash: str):
    db_user = models.User(full_name=full_name, email=email, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# -------------------------------
# CRUD de Livros (LÓGICA CORRIGIDA)
# -------------------------------

def get_book_by_isbn(db: Session, isbn: str):
    """Busca um livro pelo ISBN."""
    # Retorna o livro se o ISBN for uma string não vazia
    return db.query(models.Book).filter(models.Book.isbn == isbn).first() if isbn else None

def get_book_by_title_and_author(db: Session, title: str, authors: str):
    """NOVO: Busca um livro por título e autor como um plano B."""
    return db.query(models.Book).filter(models.Book.title == title, models.Book.authors == authors).first()

def create_book(db: Session, book_data: dict):
    """Cria um novo livro no banco de dados com todos os campos."""
    db_book = models.Book(
        title=book_data.get("title"),
        authors=", ".join(book_data.get("authors", [])),
        description=book_data.get("description"),
        thumbnail=book_data.get("thumbnail"),
        isbn=book_data.get("isbn"),
        publisher=book_data.get("publisher"),
        pageCount=book_data.get("pageCount"),
        publishedDate=book_data.get("publishedDate")
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_or_create_book(db: Session, book_data: dict):
    """
    Função aprimorada:
    1. Tenta encontrar o livro pelo ISBN (se houver).
    2. Se não encontrar (ou se não houver ISBN), tenta pelo título e autor.
    3. Se ainda assim não encontrar, cria um novo livro.
    """
    isbn = book_data.get("isbn")
    # Passo 1: Tenta pelo ISBN, que é o mais confiável
    if isbn:
        db_book = get_book_by_isbn(db, isbn)
        if db_book:
            return db_book
    
    # Passo 2: Plano B, tenta por título e autor
    title = book_data.get("title")
    authors_str = ", ".join(book_data.get("authors", []))
    db_book = get_book_by_title_and_author(db, title, authors_str)
    if db_book:
        return db_book

    # Passo 3: Se realmente não existe, cria um novo.
    return create_book(db, book_data)

# -------------------------------
# CRUD da Estante (UserBook)
# -------------------------------

def add_book_to_shelf(db: Session, user_id: int, book_id: int, status: models.BookStatus):
    """
    Adiciona um livro na estante de um usuário.
    Se o livro já estiver na estante, apenas atualiza seu status.
    """
    db_item = db.query(models.UserBook).filter_by(user_id=user_id, book_id=book_id).first()

    if db_item:
        db_item.status = status
        print(f"INFO: Livro (ID: {book_id}) já na estante. Status atualizado.")
    else:
        db_item = models.UserBook(user_id=user_id, book_id=book_id, status=status)
        db.add(db_item)
        print(f"INFO: Livro (ID: {book_id}) adicionado à estante.")
    
    db.commit()
    db.refresh(db_item)
    return db_item

def get_user_shelf(db: Session, user_id: int):
    """Retorna todos os livros da estante de um usuário."""
    return db.query(models.UserBook).filter(models.UserBook.user_id == user_id).all()

def update_shelf_item(db: Session, user_book_id: int, status: models.BookStatus, rating: int):
    """Atualiza o status e a avaliação de um item na estante."""
    db_item = db.query(models.UserBook).filter(models.UserBook.id == user_book_id).first()
    if db_item:
        db_item.status = status
        db_item.rating = rating if rating > 0 else None
        db.commit()
        db.refresh(db_item)
    return db_item

def remove_book_from_shelf(db: Session, user_book_id: int):
    """Remove um livro da estante de um usuário."""
    db_item = db.query(models.UserBook).filter(models.UserBook.id == user_book_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item