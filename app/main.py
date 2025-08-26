from fastapi import FastAPI, Depends, HTTPException
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
from . import models, database, crud
import os
import requests

# Carregar variáveis do .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

print("--- CHECANDO VARIÁVEIS DE AMBIENTE ---")
print(f"GOOGLE_BOOKS_API_KEY: {GOOGLE_BOOKS_API_KEY}")
print("--------------------------------------")

# Configurações Google Books
BASE_URL = "https://www.googleapis.com/books/v1/volumes"

# Iniciar app FastAPI
app = FastAPI()

# Criar tabelas no banco
models.Base.metadata.create_all(bind=database.engine)

# Dependência de sessão com o banco
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# FUNÇÃO auxiliar para buscar dados no Google Books
# ----------------------------
def extract_isbn(volume_info: dict):
    """Extrai ISBN-10 e ISBN-13 de um volumeInfo"""
    isbn_10, isbn_13 = None, None
    for ident in volume_info.get("industryIdentifiers", []):
        if ident.get("type") == "ISBN_10":
            isbn_10 = ident.get("identifier")
        elif ident.get("type") == "ISBN_13":
            isbn_13 = ident.get("identifier")
    # Se ISBN-13 existir, usa ele; senão usa ISBN-10
    isbn = isbn_13 if isbn_13 else isbn_10
    return isbn_10, isbn_13, isbn

def get_book_data(title: str):
    try:
        params = {
            "q": title,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": 1
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "items" not in data:
            return None

        book = data["items"][0]
        vi = book.get("volumeInfo", {})
        ai = book.get("accessInfo", {})

        isbn_10, isbn_13, isbn = extract_isbn(vi)

        return {
            "title": vi.get("title", "Título não encontrado"),
            "authors": vi.get("authors", ["Desconhecido"]),
            "publisher": vi.get("publisher"),
            "publishedDate": vi.get("publishedDate"),
            "description": vi.get("description", "Descrição não disponível"),
            "categories": vi.get("categories"),
            "pageCount": vi.get("pageCount"),
            "thumbnail": (vi.get("imageLinks") or {}).get("thumbnail"),
            "infoLink": vi.get("infoLink"),
            "previewLink": vi.get("previewLink"),
            "webReaderLink": ai.get("webReaderLink"),
            "isbn": isbn,
            "isbn_10": isbn_10,
            "isbn_13": isbn_13
        }

    except Exception as e:
        print("Erro ao buscar no Google Books:", e)
        return None

# ----------------------------
# ROTAS
# ----------------------------

@app.get("/")
def home():
    return {"message": "API de Livros com Google Books"}

@app.get("/book/{book_id}")
def get_book(book_id: str):
    try:
        response = requests.get(f"{BASE_URL}/{book_id}", params={"key": GOOGLE_BOOKS_API_KEY})
        data = response.json()

        if "volumeInfo" not in data:
            return {"error": "Livro não encontrado"}

        vi = data.get("volumeInfo", {})
        ai = data.get("accessInfo", {})
        isbn_10, isbn_13, isbn = extract_isbn(vi)

        return {
            "title": vi.get("title", "Título não encontrado"),
            "authors": vi.get("authors", []),
            "publisher": vi.get("publisher"),
            "publishedDate": vi.get("publishedDate"),
            "description": vi.get("description", "Descrição não disponível"),
            "categories": vi.get("categories"),
            "pageCount": vi.get("pageCount"),
            "thumbnail": (vi.get("imageLinks") or {}).get("thumbnail"),
            "infoLink": vi.get("infoLink"),
            "previewLink": vi.get("previewLink"),
            "webReaderLink": ai.get("webReaderLink"),
            "isbn": isbn,
            "isbn_10": isbn_10,
            "isbn_13": isbn_13,
            "url": data.get("selfLink")
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/search")
def search_books(keyword: str, count: int = 10):
    try:
        params = {
            "q": keyword,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": count
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if "items" not in data:
            return []

        results = []
        for item in data["items"]:
            vi = item.get("volumeInfo", {})
            ai = item.get("accessInfo", {})
            isbn_10, isbn_13, isbn = extract_isbn(vi)

            results.append({
                "title": vi.get("title", "Título não encontrado"),
                "authors": vi.get("authors", []),
                "publisher": vi.get("publisher"),
                "publishedDate": vi.get("publishedDate"),
                "description": vi.get("description", "Descrição não disponível"),
                "categories": vi.get("categories"),
                "pageCount": vi.get("pageCount"),
                "thumbnail": (vi.get("imageLinks") or {}).get("thumbnail"),
                "infoLink": vi.get("infoLink"),
                "previewLink": vi.get("previewLink"),
                "webReaderLink": ai.get("webReaderLink"),
                "isbn": isbn,
                "url": item.get("selfLink")
            })
        return results

    except Exception as e:
        return {"error": str(e)}

@app.post("/books/")
def add_book(title: str, db: Session = Depends(get_db)):
    book_data = get_book_data(title)
    if not book_data:
        raise HTTPException(status_code=404, detail="Livro não encontrado no Google Books")
    return crud.create_book(db, book_data)

@app.get("/books/")
def list_books(db: Session = Depends(get_db)):
    return crud.get_books(db)
