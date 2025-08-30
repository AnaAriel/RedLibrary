from sqlalchemy import Column, Integer, String
from .database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)  
    title = Column(String, index=True, nullable=False)  
    author = Column(String, default="Desconhecido")     
    description = Column(String, default="Descrição não disponível")  
    url = Column(String)                                
    image = Column(String)                              


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  
    full_name = Column(String, nullable=False)          
    email = Column(String, unique=True, index=True, nullable=False)  
    password_hash = Column(String, nullable=False)      
