
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query  
from fastapi.responses import HTMLResponse, RedirectResponse                
from fastapi.templating import Jinja2Templates                              
from fastapi.staticfiles import StaticFiles                                 
from sqlalchemy.orm import Session                                          
from pathlib import Path      
from typing import List, Optional                                           
from dotenv import load_dotenv                                              
import os                                                                   
import requests 
from starlette.middleware.sessions import SessionMiddleware                                                            
from . import models, database, crud                                        
from .auth import hash_password, verify_password 
from app.utils import hash_password, verify_password



env_path = Path(__file__).parent.parent / '.env'                             
load_dotenv(dotenv_path=env_path)                                            
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")                     

BASE_URL = "https://www.googleapis.com/books/v1/volumes"                     

templates = Jinja2Templates(directory="app/templates") 

from datetime import datetime

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

# registra o filtro no Jinja2
templates.env.filters["format_date"] = format_date


app = FastAPI()                                                              

app.mount("/static", StaticFiles(directory="app/static"), name="static")     

models.Base.metadata.create_all(bind=database.engine)

app.add_middleware(SessionMiddleware, secret_key="sua_chave_secreta")

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

def google_search(query: str, max_results: int = 40) -> List[dict]:          
    params = {"q": query, "key": GOOGLE_BOOKS_API_KEY, "maxResults": 40}     
    r = requests.get(BASE_URL, params=params)                                
    data = r.json()                                                          
    items = data.get("items", [])                                            
    return [normalize_book(it) for it in items][:max_results]                

def featured_from_google():
    termos_fixos = ["A Lâmina da Assassina", "Trono de Vidro", "Coroa da Meia-Noite", "Herdeira do Fogo", "Rainha das Sombras", "Império de Tempestades", "Torre do Alvorecer", "Reino de Cinzas", "A Vida Invisível de Addie Larue", "Noites Brancas"]
    featured = []
    for termo in termos_fixos:
        resultado = google_search(f'intitle:"{termo}"', max_results=1)
        if resultado:
            featured.append(resultado[0])
    return featured

    seen = set()                                                              
    unique = []                                                               
    for b in featured:                                                        
        if b["title"] not in seen and b["thumbnail"]:                         
            unique.append(b)                                                  
            seen.add(b["title"])                                              
        if len(unique) == 12:                                                 
            break                                                             
    return unique                                                             

@app.get("/", response_class=HTMLResponse)                                    
def home(request: Request):                                                   
    featured_books = featured_from_google()    
    user_id = request.session.get("user_id")                               
    return templates.TemplateResponse(                                        
        "index.html",                                                         
        {                                                                
            "request": request,
            "featured_books": featured_books,
            "user_id": user_id  # passa para o HTML                      
        }
    )

@app.get("/login", response_class=HTMLResponse)                               
def login_form(request: Request):                                             
    return templates.TemplateResponse("login.html", {"request": request})     

@app.post("/login")
def login_user(                                                             
    request: Request,                                                  
    email: str = Form(...),                                                  
    password: str = Form(...),                                              
    db: Session = Depends(get_db)                                            
):
    user = crud.get_user_by_email(db, email)                                  
    if not user:                                                              
        raise HTTPException(status_code=400, detail="Email não encontrado")   
    if not verify_password(password, user.password_hash):                     
        raise HTTPException(status_code=400, detail="Senha incorreta")       

    #SALVA O USUÁRIO NA SESSÃO
    request.session["user_id"] = user.id

    return RedirectResponse(url="/", status_code=303)  

    

@app.get("/register", response_class=HTMLResponse)                            
def register_form(request: Request):                                          
    return templates.TemplateResponse("register.html", {"request": request})   

@app.post("/register")                                                        
def register_user(                                                         
    request: Request,                                                         
    full_name: str = Form(...),                                               
    email: str = Form(...),                                               
    password: str = Form(...),                                              
    db: Session = Depends(get_db)                                             
):
    existing_user = crud.get_user_by_email(db, email)                       
    if existing_user:                                                        
        raise HTTPException(status_code=400, detail="Email já cadastrado")   
    hashed_pw = hash_password(password)                                       
    crud.create_user(db, full_name, email, hashed_pw)                         
    return RedirectResponse(url="/login", status_code=303) 

@app.get("/logout")
def logout(request: Request):
    request.session.clear()  # limpa a sessão
    return RedirectResponse(url="/", status_code=303)


@app.get("/search", response_class=HTMLResponse)                               
def search_books(                                                              
    request: Request,                                                          
    keyword: str = Query(..., min_length=1),                                   
    search_by: str = Query("title"),                                           
    page: int = Query(1, ge=1),                                                
):
    # Monta a query da API conforme seleção do usuário
    if search_by == "author":                                                  
        query = f'inauthor:"{keyword}"'                                        
    else:                                                                      
        query = f'intitle:"{keyword}"'                                         

    # Busca na Google Books
    raw_results = google_search(query, max_results=120)                        
    total_books = len(raw_results)                                             

    # Paginação manual (20 por página)
    per_page = 20                                                              
    start = (page - 1) * per_page                                              
    end = start + per_page                                                     
    books = raw_results[start:end]                                             

    # Cálculo das informações de exibição
    displayed_start = 0 if total_books == 0 else start + 1                     
    displayed_end = min(end, total_books)                                      
    total_pages = max(1, (total_books + per_page - 1) // per_page)             

    # Renderiza o template de resultados
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
        }
    )
