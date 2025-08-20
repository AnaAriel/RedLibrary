# RedLibrary

Instalar uma biblioteca para implementar a assinatura das requisições exigida pela Amazon

pip install python-amazon-paapi

--------------------------------

instalar o python-dotenv (biblioteca que lê senhas e chaves de um arquivo separado (.env) para que você não precise escrevê-las diretamente no código, deixando-o mais seguro.)

pip install python-dotenv

para iniciar a aplicação é preciso utilizar o comando:
uvicorn main:app --reload

--------------------------------

REQUIREMENTS
fastapi
uvicorn
python-dotenv
amazon-paapi
sqlalchemy

--------------------------------
pip install fastapi uvicorn[standard] python-dotenv sqlalchemy psycopg2-binary python-amazon-paapi

pip install -python-amazon-paapi