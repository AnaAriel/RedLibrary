from fastapi import FastAPI, Depends, HTTPException
from amazon_paapi import AmazonApi
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from . import models, database, crud
import os

models.Base.metadata.create_all(bind=database.engine)
# 🔑 Carregar variáveis do arquivo .env
load_dotenv()

ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")

# 📦 Criar cliente Amazon (Brasil)
amazon = AmazonApi(ACCESS_KEY, SECRET_KEY, PARTNER_TAG, "BR", throttling=1.5)

# 🚀 Iniciar app FastAPI
app = FastAPI()

# ----------------------------
# Rotas
# ----------------------------

# Dependência para pegar a sessão do banco
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "API de Livros com Amazon PAAPI 5.0"}

# 🔎 Buscar livro por ASIN (código único da Amazon)
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

# 🔎 Buscar livros por palavra-chave (ex.: título ou autor)
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