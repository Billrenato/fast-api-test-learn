# Importações essenciais para a aplicação
from fastapi import FastAPI, Depends, HTTPException # Importa classes do FastAPI:
# FastAPI: Classe principal para criar a aplicação web.
# Depends: Função usada para injeção de dependência (como a sessão do banco de dados).
# HTTPException: Classe usada para levantar erros HTTP (como 404 Not Found).

from sqlalchemy.orm import Session # Importa o tipo Session do SQLAlchemy para lidar com a sessão do banco.
import models # Importa o módulo 'models.py' que contém as definições dos modelos/tabelas (ex: Produto).
import schemas # Importa o módulo 'schemas.py' que contém os schemas Pydantic para validação e serialização de dados (entrada/saída).
from database import SessionLocal, engine # Importa do módulo 'database.py':
# SessionLocal: Classe de sessão configurada para interagir com o banco de dados.
# engine: O motor (engine) do banco de dados (neste caso, SQLite).

# --- Configuração Inicial do Banco de Dados ---
# Criar tabelas SQLite automaticamente (se ainda não existirem)
models.Base.metadata.create_all(bind=engine)
# models.Base é a classe base declarativa do SQLAlchemy.
# .metadata.create_all(bind=engine) instrui o SQLAlchemy a criar todas as tabelas
# definidas nos modelos (models.py) no banco de dados associado ao 'engine'.

# --- Inicialização da Aplicação FastAPI ---
app = FastAPI(title="FastAPI com SQLite")
# Instancia a aplicação FastAPI. O parâmetro 'title' é útil para a documentação interativa (Swagger UI/ReDoc).

# --- Dependência para a Sessão do Banco de Dados ---
# Dependência para obter sessão do banco
def get_db():
    # Esta função é um gerador de dependência.
    db = SessionLocal() # 1. Cria uma nova sessão de banco de dados.
    try:
        yield db # 2. 'yield' a sessão, tornando-a disponível para a função de rota (endpoint) que a chamou.
        # O código após o 'yield' (a cláusula 'finally') é executado após a rota ter terminado de processar,
        # mesmo que tenha ocorrido uma exceção.
    finally:
        db.close() # 3. Garante que a sessão do banco de dados seja fechada, liberando a conexão,
        # essencial para evitar vazamento de recursos.

# --- Definição das Rotas (Endpoints) da API ---

## 📦 Rota para Criar um Novo Produto (POST)
@app.post("/produtos", response_model=schemas.Produto)
# Define uma rota POST em '/produtos'.
# response_model=schemas.Produto: Especifica que a resposta (o produto criado) deve ser validada e formatada
# usando o schema Pydantic 'schemas.Produto'.
def criar_produto(produto: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    # produto: Recebe os dados do corpo da requisição, validados pelo schema Pydantic 'schemas.ProdutoCreate'.
    # db: Recebe a sessão do banco de dados, injetada pela dependência 'Depends(get_db)'.
    
    # Cria uma nova instância do modelo SQLAlchemy 'models.Produto'.
    # **produto.dict() desempacota os dados validados do Pydantic no construtor do modelo SQLAlchemy.
    novo = models.Produto(**produto.dict())
    
    db.add(novo) # Adiciona o novo objeto à sessão de banco de dados.
    db.commit() # Confirma as alterações no banco de dados (persiste o produto).
    db.refresh(novo) # Atualiza a instância 'novo' com os dados do banco (incluindo o ID gerado automaticamente).
    
    return novo # Retorna o objeto produto criado.

# ---
    
## 📋 Rota para Listar Todos os Produtos (GET)
@app.get("/produtos", response_model=list[schemas.Produto])
# Define uma rota GET em '/produtos'.
# response_model=list[schemas.Produto]: Indica que a resposta é uma lista de objetos, cada um formatado
# usando o schema 'schemas.Produto'.
def listar_produtos(db: Session = Depends(get_db)):
    # Executa uma consulta (query) no modelo 'models.Produto' e busca todos os resultados (.all()).
    # Isso retorna uma lista de instâncias de 'models.Produto'.
    return db.query(models.Produto).all()

# ---

## 🔍 Rota para Obter um Produto Específico (GET)
@app.get("/produtos/{produto_id}", response_model=schemas.Produto)
# Define uma rota GET em '/produtos/{produto_id}'. O '{produto_id}' é um parâmetro de caminho.
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    # produto_id: Recebe o valor do parâmetro de caminho, tipado como 'int'.
    
    # Consulta o banco de dados:
    # 1. db.query(models.Produto): Seleciona o modelo.
    # 2. .filter(models.Produto.id == produto_id): Adiciona a condição WHERE (filtra pelo ID).
    # 3. .first(): Pega o primeiro resultado (ou None se não encontrado).
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    
    if not produto:
        # Se o produto não for encontrado, levanta uma exceção HTTP 404.
        raise HTTPException(404, "Produto não encontrado")
    
    return produto # Retorna o objeto produto encontrado.

# ---

## ✏️ Rota para Atualizar um Produto Específico (PUT)
@app.put("/produtos/{produto_id}", response_model=schemas.Produto)
# Define uma rota PUT em '/produtos/{produto_id}' para atualização.
def atualizar_produto(produto_id: int, dados: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    # dados: Recebe os dados de atualização, validados pelo schema 'schemas.ProdutoCreate'.
    
    # 1. Busca o produto existente (mesma lógica da rota GET).
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    
    if not produto:
        # Se não encontrado, levanta HTTPException 404.
        raise HTTPException(404, "Produto não encontrado")

    # 2. Atualiza os campos do objeto produto existente com os novos dados.
    # Itera sobre os pares chave/valor do objeto Pydantic 'dados'.
    for campo, valor in dados.dict().items():
        # setattr(objeto, nome_do_campo, valor): Define o valor de um atributo (campo) em um objeto.
        setattr(produto, campo, valor)
        
    db.commit() # Confirma as alterações no banco de dados.
    db.refresh(produto) # Atualiza a instância com o estado mais recente do banco.
    
    return produto # Retorna o objeto produto atualizado.

# ---

## 🗑️ Rota para Deletar um Produto Específico (DELETE)
@app.delete("/produtos/{produto_id}")
# Define uma rota DELETE em '/produtos/{produto_id}' para exclusão.
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    # 1. Busca o produto existente (mesma lógica das rotas GET/PUT).
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    
    if not produto:
        # Se não encontrado, levanta HTTPException 404.
        raise HTTPException(404, "Produto não encontrado")

    # 2. Deleta o objeto da sessão.
    db.delete(produto)
    db.commit() # Confirma a exclusão no banco de dados.

    # 3. Retorna uma mensagem de sucesso (não há 'response_model' definido, então retorna um dicionário simples).
    return {"mensagem": "Produto deletado com sucesso"}