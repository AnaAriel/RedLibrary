from passlib.context import CryptContext

# Configuração do algoritmo de hashing de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Função para gerar hash da senha
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Função para verificar senha durante login
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)
