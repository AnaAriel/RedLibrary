from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    # Corrigido para 'authors' (plural) para consistência
    authors = Column(String, default="Desconhecido")
    description = Column(String, default="Descrição não disponível")
    # Campos que faltavam:
    thumbnail = Column(String)
    isbn = Column(String, unique=True, index=True, nullable=True)
    publisher = Column(String, default="—")
    pageCount = Column(Integer, nullable=True)
    publishedDate = Column(String, default="—")

    # Relação com UserBook
    users = relationship("UserBook", back_populates="book")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Relação com UserBook
    books = relationship("UserBook", back_populates="user")


# Status possível para os livros na estante
class BookStatus(str, enum.Enum):
    lido = "lido"
    lendo = "lendo"
    quero_ler = "quero ler"


class UserBook(Base):
    __tablename__ = "user_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    status = Column(Enum(BookStatus), nullable=False)
    rating = Column(Integer, default=None)  # avaliação de 1 a 5

    # Relações
    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="users")