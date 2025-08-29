# ============================== IMPORTAÇÕES PADRÃO ==============================
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query  # Importa classes e funções do FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse                # Respostas HTML e redirecionamento
from fastapi.templating import Jinja2Templates                              # Integração dos templates Jinja2
from fastapi.staticfiles import StaticFiles                                 # Servir arquivos estáticos (CSS/Imagens/JS)
from sqlalchemy.orm import Session                                          # Sessões do SQLAlchemy
from pathlib import Path                                                    # Manuseio de caminhos de arquivos
from typing import List, Optional                                           # Tipagem para listas e opcionais
from dotenv import load_dotenv                                              # Carregar variáveis de ambiente de .env
import os                                                                   # Acesso ao sistema operacional (variáveis etc.)
import requests                                                             # Requisições HTTP para a API do Google Books

# ============================== IMPORTAÇÕES DO PROJETO ==========================
from . import models, database, crud                                        # Importa módulos internos do app
from .auth import hash_password, verify_password                             # Funções de hash e verificação de senha

# ============================== CONFIG .ENV =====================================
env_path = Path(__file__).parent.parent / '.env'                             # Define o caminho do arquivo .env (na raiz)
load_dotenv(dotenv_path=env_path)                                            # Carrega as variáveis do .env
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")                     # Lê a chave da API do Google Books

# ============================== CONSTANTES DA API GOOGLE BOOKS ==================
BASE_URL = "https://www.googleapis.com/books/v1/volumes"                     # URL base da API de livros do Google

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


# ============================== INICIALIZAÇÃO DO APP ============================
app = FastAPI()                                                              # Cria a instância principal do FastAPI

app.mount("/static", StaticFiles(directory="app/static"), name="static")     # Mapeia a pasta de estáticos em /static

models.Base.metadata.create_all(bind=database.engine)                        # Cria as tabelas do banco (se não existirem)

# ============================== DEPENDÊNCIA DB =================================
def get_db():                                                                # Função geradora para obter sessão do DB
    db = database.SessionLocal()                                             # Cria uma sessão
    try:                                                                     # Tenta usar a sessão
        yield db                                                             # Entrega a sessão para quem pediu
    finally:                                                                 # Ao final do request
        db.close()                                                           # Fecha a sessão, evitando vazamento

# ============================== AUXILIARES GOOGLE BOOKS =========================
def extract_isbn(volume_info: dict):                                         # Função para extrair ISBNs do volumeInfo
    isbn_10, isbn_13 = None, None                                            # Inicializa variáveis de ISBN
    for ident in volume_info.get("industryIdentifiers", []):                 # Percorre identificadores, se existirem
        if ident.get("type") == "ISBN_10":                                   # Se for ISBN-10
            isbn_10 = ident.get("identifier")                                # Guarda valor do ISBN-10
        elif ident.get("type") == "ISBN_13":                                 # Se for ISBN-13
            isbn_13 = ident.get("identifier")                                # Guarda valor do ISBN-13
    isbn = isbn_13 if isbn_13 else isbn_10                                   # Prefere ISBN-13, senão usa ISBN-10
    return isbn_10, isbn_13, isbn                                            # Retorna tupla com ambos e o escolhido

def normalize_book(item: dict) -> dict:                                      # Converte item cru da API para um dict limpo
    vi = item.get("volumeInfo", {})                                          # volumeInfo com dados principais do livro
    ai = item.get("accessInfo", {})                                          # accessInfo com links de leitura
    isbn_10, isbn_13, isbn = extract_isbn(vi)                                # Extrai ISBNs
    image_links = vi.get("imageLinks") or {}                                 # Evita erro se imageLinks não existir
    return {                                                                 # Monta o dicionário final
        "title": vi.get("title", "Título não encontrado"),                   # Título do livro (ou fallback)
        "authors": vi.get("authors", ["Desconhecido"]),                      # Lista de autores (ou desconhecido)
        "publisher": vi.get("publisher", "—"),                               # Editora (ou travessão)
        "publishedDate": vi.get("publishedDate", "—"),                       # Data de publicação (ou travessão)
        "description": vi.get("description", "Descrição não disponível"),    # Descrição (ou fallback)
        "categories": vi.get("categories", []),                              # Categorias (lista)
        "pageCount": vi.get("pageCount", "—"),                               # Contagem de páginas (ou travessão)
        "thumbnail": image_links.get("thumbnail") or image_links.get("smallThumbnail") or "",  # Capa (ou vazio)
        "infoLink": vi.get("infoLink", ""),                                  # Link de info
        "previewLink": vi.get("previewLink", ""),                            # Link de preview
        "webReaderLink": ai.get("webReaderLink", ""),                        # Link de leitura web
        "isbn": isbn,                                                        # ISBN preferido
        "isbn_10": isbn_10,                                                  # ISBN-10
        "isbn_13": isbn_13,                                                  # ISBN-13
        "url": item.get("selfLink", ""),                                     # Link para o próprio recurso
    }

def google_search(query: str, max_results: int = 40) -> List[dict]:          # Busca livros no Google Books
    params = {"q": query, "key": GOOGLE_BOOKS_API_KEY, "maxResults": 40}     # Monta parâmetros (máx 40 por requisição)
    r = requests.get(BASE_URL, params=params)                                 # Faz a requisição HTTP GET
    data = r.json()                                                           # Converte resposta para JSON
    items = data.get("items", [])                                             # Pega a lista de itens (ou lista vazia)
    return [normalize_book(it) for it in items][:max_results]                 # Normaliza cada item e limita quantidade

def featured_from_google():
    termos_fixos = ["A Lâmina da Assassina", "Trono de Vidro", "Coroa da Meia-Noite", "Herdeira do Fogo", "Rainha das Sombras", "Império de Tempestades", "Torre do Alvorecer", "Reino de Cinzas", "A Vida Invisível de Addie Larue", "Noites Brancas"]
    featured = []
    for termo in termos_fixos:
        resultado = google_search(f'intitle:"{termo}"', max_results=1)
        if resultado:
            featured.append(resultado[0])
    return featured

    # Remove duplicados por título para não repetir cards
    seen = set()                                                              # Conjunto de títulos já vistos
    unique = []                                                               # Lista final única
    for b in featured:                                                        # Percorre cada livro coletado
        if b["title"] not in seen and b["thumbnail"]:                         # Se título inédito e com capa
            unique.append(b)                                                  # Adiciona à lista única
            seen.add(b["title"])                                              # Marca como visto
        if len(unique) == 12:                                                 # Queremos exibir 12 na home
            break                                                             # Quando atingir 12, parar
    return unique                                                             # Retorna a lista final de destaques

# ============================== ROTAS PÚBLICAS ==================================
@app.get("/", response_class=HTMLResponse)                                    # Rota GET da página inicial
def home(request: Request):                                                    # Função que atende "/"
    featured_books = featured_from_google()                                    # Busca livros em destaque
    return templates.TemplateResponse(                                         # Renderiza o template index.html
        "index.html",                                                          # Nome do arquivo de template
        {                                                                      # Contexto enviado ao template
            "request": request,                                                # Objeto request (obrigatório no Jinja2 do FastAPI)
            "featured_books": featured_books,                                  # Lista de livros para a grade da home
            "mensagem": "Bem-vindo ao RedLibrary!",                            # Mensagem de boas-vindas
        }
    )

@app.get("/login", response_class=HTMLResponse)                                # Rota GET da tela de login
def login_form(request: Request):                                              # Função que atende "/login"
    return templates.TemplateResponse("login.html", {"request": request})      # Renderiza login.html

@app.post("/login")                                                            # Rota POST para autenticar usuário
def login_user(                                                                # Função que processa o login
    request: Request,                                                          # Objeto de requisição
    email: str = Form(...),                                                    # Campo email vindo do formulário
    password: str = Form(...),                                                 # Campo senha vindo do formulário
    db: Session = Depends(get_db)                                              # Sessão do banco via dependência
):
    user = crud.get_user_by_email(db, email)                                   # Busca usuário por email
    if not user:                                                               # Se não encontrou
        raise HTTPException(status_code=400, detail="Email não encontrado")    # Retorna erro 400
    if not verify_password(password, user.password_hash):                      # Verifica a senha com hash
        raise HTTPException(status_code=400, detail="Senha incorreta")         # Retorna erro 400
    return RedirectResponse(url="/", status_code=303)                          # Se ok, redireciona para a home

@app.get("/register", response_class=HTMLResponse)                             # Rota GET da tela de cadastro
def register_form(request: Request):                                           # Função que atende "/register"
    return templates.TemplateResponse("register.html", {"request": request})   # Renderiza register.html

@app.post("/register")                                                         # Rota POST para criar usuário
def register_user(                                                             # Função que processa o cadastro
    request: Request,                                                          # Objeto de requisição
    full_name: str = Form(...),                                                # Nome completo vindo do form
    email: str = Form(...),                                                    # Email vindo do form
    password: str = Form(...),                                                 # Senha vinda do form
    db: Session = Depends(get_db)                                              # Sessão do banco via dependência
):
    existing_user = crud.get_user_by_email(db, email)                          # Verifica se já existe usuário no DB
    if existing_user:                                                          # Se encontrado
        raise HTTPException(status_code=400, detail="Email já cadastrado")     # Erro 400 de email duplicado
    hashed_pw = hash_password(password)                                        # Gera o hash da senha
    crud.create_user(db, full_name, email, hashed_pw)                          # Cria o usuário no banco
    return RedirectResponse(url="/login", status_code=303)                     # Redireciona para login

# ============================== BUSCA E LISTAGEM =================================
@app.get("/search", response_class=HTMLResponse)                               # Rota GET para resultados de busca
def search_books(                                                              # Função que processa a busca
    request: Request,                                                          # Objeto de requisição
    keyword: str = Query(..., min_length=1),                                   # Palavra-chave obrigatória
    search_by: str = Query("title"),                                           # Tipo de busca: 'title' ou 'author'
    page: int = Query(1, ge=1),                                                # Página atual da paginação (>=1)
):
    # Monta a query da API conforme seleção do usuário
    if search_by == "author":                                                  # Se for por autor
        query = f'inauthor:"{keyword}"'                                        # Usa operador inauthor:
    else:                                                                      # Caso contrário (título)
        query = f'intitle:"{keyword}"'                                         # Usa operador intitle:

    # Busca na Google Books
    raw_results = google_search(query, max_results=120)                        # Traz até 120 itens para paginar
    total_books = len(raw_results)                                             # Total de livros encontrados

    # Paginação manual (20 por página)
    per_page = 20                                                              # Define o limite por página
    start = (page - 1) * per_page                                              # Índice inicial do slice
    end = start + per_page                                                     # Índice final (não-inclusivo)
    books = raw_results[start:end]                                             # Fatia dos livros a exibir

    # Cálculo das informações de exibição
    displayed_start = 0 if total_books == 0 else start + 1                     # Número do primeiro item exibido
    displayed_end = min(end, total_books)                                      # Número do último item exibido
    total_pages = max(1, (total_books + per_page - 1) // per_page)             # Total de páginas (arredonda para cima)

    # Renderiza o template de resultados
    return templates.TemplateResponse(                                         # Retorna a página HTML
        "search_results.html",                                                 # Template da lista
        {
            "request": request,                                                # Objeto request (obrigatório)
            "keyword": keyword,                                                # Palavra pesquisada (para manter no input)
            "search_by": search_by,                                            # Tipo de busca (para manter seleção)
            "books": books,                                                    # Lista de livros paginada
            "total_books": total_books,                                        # Contagem total
            "displayed_books_start": displayed_start,                          # Primeiro número exibido
            "displayed_books_end": displayed_end,                              # Último número exibido
            "total_pages": total_pages,                                        # Quantidade de páginas
            "current_page": page,                                              # Página atual
            "per_page": per_page,                                              # Itens por página
        }
    )
