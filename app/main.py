from fastapi import FastAPI, Depends, HTTPException
from amazon_paapi import AmazonApi
from dotenv import load_dotenv
from pathlib import Path  # <--- GARANTA QUE ESTA LINHA ESTEJA AQUI
from sqlalchemy.orm import Session
from typing import List
from . import models, database, crud  # <-- certifique-se que models/database/crud estão corretamente configurados
import os

# 🔑 Carregar variáveis do .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")

print("--- CHECANDO VARIÁVEIS DE AMBIENTE ---")
print(f"ACCESS_KEY: {ACCESS_KEY}")
print(f"SECRET_KEY: {SECRET_KEY}")
print(f"PARTNER_TAG: {PARTNER_TAG}")
print("--------------------------------------")

# 📦 Criar cliente Amazon (Brasil)
amazon = AmazonApi(ACCESS_KEY, SECRET_KEY, PARTNER_TAG, "BR", throttling=1.5)

# 🚀 Iniciar app FastAPI
app = FastAPI()

# 💾 Criar tabelas no banco
models.Base.metadata.create_all(bind=database.engine)

# 🔁 Dependência de sessão com o banco
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# FUNÇÃO auxiliar para buscar dados na Amazon
# ----------------------------
def get_book_data(title: str):
    try:
        results = amazon.search_items(
            keywords=title,
            search_index="Books",
            item_count=1
        )
        if not results:
            return None

        book = results[0]
        return {
            "title": book.title,
            "author": ", ".join(book.authors) if book.authors else "Desconhecido",
            "description": book.description if hasattr(book, "description") else "Descrição não disponível",
            "cover_url": book.images.large if book.images else None
        }

    except Exception as e:
        print("Erro ao buscar na Amazon:", e)
        return None

# ----------------------------
# ROTAS
# ----------------------------

@app.get("/")
def home():
    return {"message": "API de Livros com Amazon PAAPI 5.0"}

@app.get("/book/{asin}")
def get_book(asin: str):
    try:
        products = amazon.get_items([asin])
        if not products:
            return {"error": "Livro não encontrado"}

        book = products[0]
        return {
            "title": book.title,
            "author": book.authors,
            "description": book.description if hasattr(book, "description") else "Descrição não disponível",
            "url": book.url,
            "image": book.images.large if book.images else None
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/search")
def search_books(keyword: str, count: int = 10):
    try:
        products = amazon.search_items(
            keywords=keyword,
            search_index="Books",
            item_count=count
        )
        return [
            {
                "title": p.title,
                "author": p.authors,
                "description": p.description if hasattr(p, "description") else "Descrição não disponível",
                "url": p.url,
                "image": p.images.large if p.images else None
            }
            for p in products
        ]
    except Exception as e:
        return {"error": str(e)}

@app.post("/books/")
def add_book(title: str, db: Session = Depends(get_db)):
    book_data = get_book_data(title)
    if not book_data:
        raise HTTPException(status_code=404, detail="Livro não encontrado na Amazon")
    return crud.create_book(db, book_data)

@app.get("/books/")
def list_books(db: Session = Depends(get_db)):
    return crud.get_books(db)
