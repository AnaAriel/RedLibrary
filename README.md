# RedLibrary

REQUIREMENTS
pip install fastapi → framework principal da API.
pip install uvicorn → servidor ASGI para rodar o FastAPI.
pip install sqlalchemy → ORM para conectar e manipular o banco de dados SQLite.
pip install requests → usado para consumir a API do Google Books.
pip install passlib[bcrypt] → para hashear/verificar senhas de usuários.
pip install python-dotenv → carregar variáveis de ambiente do arquivo .env.
pip install jinja2 → motor de templates para renderizar páginas HTML.
pip install python-multipart → pacote que o FastAPI usa para lidar com formulários HTML enviados via POST.
pip install itsdangerous → 

Para iniciar a aplicação é preciso utilizar o comando:
uvicorn app.main:app --reload