from sqlalchemy.orm import Session
from . import models
from app.models import User

# -------------------------------
# CRUD de Livros
# -------------------------------
def create_book(db: Session, book_data: dict):
    # Cria um novo livro no banco a partir dos dados recebidos
    db_book = models.Book(
        title=book_data["title"],
        author=book_data.get("author", "Desconhecido"),
        description=book_data.get("description", "Descrição não disponível"),
        url=book_data.get("url", ""),
        image=book_data.get("cover_url", "")
    )
    db.add(db_book)     # Adiciona o livro na sessão
    db.commit()         # Confirma no banco
    db.refresh(db_book) # Atualiza o objeto com o ID gerado
    return db_book

def get_books(db: Session):
    # Retorna todos os livros cadastrados
    return db.query(models.Book).all()

# -------------------------------
# CRUD de Usuários
# -------------------------------
def create_user(db: Session, full_name: str, email: str, password_hash: str):
    # Cria um novo usuário no banco
    db_user = models.User(full_name=full_name, email=email, password_hash=password_hash)
    db.add(db_user)      # Adiciona o usuário
    db.commit()          # Salva no banco
    db.refresh(db_user)  # Atualiza com ID
    return db_user

def get_user_by_email(db: Session, email: str):
    # Busca um usuário pelo email
    return db.query(models.User).filter(models.User.email == email).first()
