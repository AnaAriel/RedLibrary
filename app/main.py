# app/main.py

from fastapi import FastAPI, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List
from dotenv import load_dotenv
import os
import re
import requests
from starlette.middleware.sessions import SessionMiddleware
from . import models, database, crud
from .auth import hash_password, verify_password
from datetime import datetime

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

BASE_URL = "https://www.googleapis.com/books/v1/volumes"

templates = Jinja2Templates(directory="app/templates")

def format_date(value: str):
    if not value:
        return "—"
    try:
        if len(value) == 4:
            return value
        elif len(value) == 7:
            return datetime.strptime(value, "%Y-%m").strftime("%m/%Y")
        else:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return value

templates.env.filters["format_date"] = format_date

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

models.Base.metadata.create_all(bind=database.engine)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "sua_chave_secreta"))

EMAIL_REGEX = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}$"

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def extract_isbn(volume_info: dict):
    isbn_10, isbn_13 = None, None
    for ident in volume_info.get("industryIdentifiers", []):
        if ident.get("type") == "ISBN_10":
            isbn_10 = ident.get("identifier")
        elif ident.get("type") == "ISBN_13":
            isbn_13 = ident.get("identifier")
    isbn = isbn_13 if isbn_13 else isbn_10
    return isbn_10, isbn_13, isbn

def normalize_book(item: dict) -> dict:
    vi = item.get("volumeInfo", {})
    ai = item.get("accessInfo", {})
    isbn_10, isbn_13, isbn = extract_isbn(vi)
    image_links = vi.get("imageLinks") or {}
    return {
        "title": vi.get("title", "Título não encontrado"),
        "authors": vi.get("authors", ["Desconhecido"]),
        "publisher": vi.get("publisher", "—"),
        "publishedDate": vi.get("publishedDate", "—"),
        "description": vi.get("description", "Descrição não disponível"),
        "categories": vi.get("categories", []),
        "pageCount": vi.get("pageCount", "—"),
        "thumbnail": image_links.get("thumbnail") or image_links.get("smallThumbnail") or "",
        "infoLink": vi.get("infoLink", ""),
        "previewLink": vi.get("previewLink", ""),
        "webReaderLink": ai.get("webReaderLink", ""),
        "isbn": isbn,
        "isbn_10": isbn_10,
        "isbn_13": isbn_13,
        "url": item.get("selfLink", ""),
    }

def google_search(query: str, max_results: int = 40, start_index: int = 0) -> (List[dict], int):
    """
    Busca na API do Google e retorna uma tupla: (lista de livros, total de itens encontrados).
    """
    # Garante que max_results não passe de 40
    if max_results > 40:
        max_results = 40

    params = {
        "q": query,
        "key": GOOGLE_BOOKS_API_KEY,
        "maxResults": max_results,
        "startIndex": start_index
    }

    try:
        r = requests.get(BASE_URL, params=params)
        r.raise_for_status()
        data = r.json()
        
        items = data.get("items", [])
        total_items = data.get("totalItems", 0)

        normalized_books = [normalize_book(it) for it in items]
        return (normalized_books, total_items)

    except requests.exceptions.RequestException as e:
        return ([], 0)
    except Exception as e:
        return ([], 0)

def featured_from_google():
    termos_fixos = [
        "A Lâmina da Assassina", "Trono de Vidro", "Coroa da Meia-Noite",
        "Herdeira do Fogo", "Rainha das Sombras", "Império de Tempestades",
        "Torre do Alvorecer", "Reino de Cinzas", "A Vida Invisível de Addie Larue",
        "Noites Brancas"
    ]
    featured = []
    for termo in termos_fixos:
        resultado = google_search(f'intitle:"{termo}"', max_results=1)
        if resultado:
            featured.append(resultado[0])
    return featured

def set_flash(request: Request, key: str, message: str):
    request.session[key] = message

def pop_flash(request: Request, key: str):
    return request.session.pop(key, None)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    featured_books = featured_from_google()
    user_id = request.session.get("user_id")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "featured_books": featured_books,
            "user_id": user_id
        }
    )

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    error_message = pop_flash(request, "flash_error")
    return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})

@app.post("/login")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not re.match(EMAIL_REGEX, email or ""):
        set_flash(request, "flash_error", "Formato de email inválido")
        return RedirectResponse(url="/login", status_code=303)
    user = crud.get_user_by_email(db, email)
    if not user:
        set_flash(request, "flash_error", "Email não cadastrado")
        return RedirectResponse(url="/login", status_code=303)
    if not verify_password(password, user.password_hash):
        set_flash(request, "flash_error", "Senha incorreta")
        return RedirectResponse(url="/login", status_code=303)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    error_message = pop_flash(request, "flash_error")
    return templates.TemplateResponse("register.html", {"request": request, "error_message": error_message})

@app.post("/register")
def register_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not re.match(EMAIL_REGEX, email or ""):
        set_flash(request, "flash_error", "Formato de email inválido")
        return RedirectResponse(url="/register", status_code=303)
    existing_user = crud.get_user_by_email(db, email)
    if existing_user:
        set_flash(request, "flash_error", "Email já cadastrado")
        return RedirectResponse(url="/register", status_code=303)
    hashed_pw = hash_password(password)
    crud.create_user(db, full_name, email, hashed_pw)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/search", response_class=HTMLResponse)
def search_books(
    request: Request,
    keyword: str = Query(..., min_length=1),
    search_by: str = Query("title"),
    page: int = Query(1, ge=1),
):
    query = f'inauthor:"{keyword}"' if search_by == "author" else f'intitle:"{keyword}"'
    
    per_page = 20 # Quantos livros você quer mostrar por página no seu site
    start_index = (page - 1) * per_page

    # A função agora retorna os livros JÁ PAGINADOS e o total de resultados
    books, total_books = google_search(query, max_results=per_page, start_index=start_index)
    total_books = min(total_books, 100)

    # A lógica de paginação agora usa o `total_books` retornado pela API
    displayed_start = 0 if total_books == 0 else start_index + 1
    displayed_end = min(start_index + len(books), total_books)
    total_pages = max(1, (total_books + per_page - 1) // per_page)

    user_id = request.session.get("user_id")

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "keyword": keyword,
            "search_by": search_by,
            "books": books,
            "total_books": total_books,
            "displayed_books_start": displayed_start,
            "displayed_books_end": displayed_end,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page,
            "user_id": user_id,
        }
    )

# =========================================================
# ============ NOVAS ROTAS PARA A ESTANTE =================
# =========================================================

@app.post("/shelf/add")
def add_to_shelf(
    request: Request,
    db: Session = Depends(get_db),
    # Dados do livro vêm do formulário
    book_title: str = Form(...),
    book_authors: str = Form(...),
    book_description: str = Form(...),
    book_thumbnail: str = Form(...),
    book_isbn: str = Form(None), # ISBN pode ser nulo
    status: str = Form(...)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    book_data = {
        "title": book_title,
        "authors": book_authors.split(','),
        "description": book_description,
        "thumbnail": book_thumbnail,
        "isbn": book_isbn
    }

    book = crud.get_or_create_book(db, book_data)
    crud.add_book_to_shelf(db, user_id=user_id, book_id=book.id, status=status)
    return RedirectResponse("/shelf", status_code=303)

@app.get("/shelf", response_class=HTMLResponse)
def view_shelf(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user_books = crud.get_user_shelf(db, user_id)
    
    return templates.TemplateResponse(
        "shelf.html",
        {
            "request": request,
            "user_id": user_id,
            "user_books": user_books
        }
    )

@app.post("/shelf/update/{user_book_id}")
def update_shelf(
    request: Request,
    user_book_id: int,
    db: Session = Depends(get_db),
    status: str = Form(...),
    rating: int = Form(0)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    
    crud.update_shelf_item(db, user_book_id, status, rating)
    return RedirectResponse("/shelf", status_code=303)

@app.post("/shelf/delete/{user_book_id}")
def delete_from_shelf(
    request: Request,
    user_book_id: int,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)
        
    crud.remove_book_from_shelf(db, user_book_id)
    return RedirectResponse("/shelf", status_code=303)