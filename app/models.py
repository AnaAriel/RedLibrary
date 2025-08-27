from sqlalchemy import Column, Integer, String
from .database import Base

# Modelo para a tabela de livros (já existente)
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)  # ID único do livro
    title = Column(String, index=True, nullable=False)  # Título do livro
    author = Column(String, default="Desconhecido")     # Autor do livro
    description = Column(String, default="Descrição não disponível")  # Descrição
    url = Column(String)                                # Link externo do livro
    image = Column(String)                              # URL da imagem da capa

# Modelo para a tabela de usuários
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # ID único do usuário
    full_name = Column(String, nullable=False)          # Nome completo do usuário
    email = Column(String, unique=True, index=True, nullable=False)  # Email único
    password_hash = Column(String, nullable=False)      # Senha armazenada em hash
