from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, get_db
import models

# Cria o banco de dados e as tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Radar Acadêmico")

# Aponta para a pasta onde estão as imagens (a logo)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Aponta para a pasta HTML
templates = Jinja2Templates(directory="templates")

# 1. Rota de Login
@app.get("/", response_class=HTMLResponse)
async def tela_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

# 2. Rota da Tela de Cadastro
@app.get("/cadastro", response_class=HTMLResponse)
async def tela_cadastro(request: Request):
    return templates.TemplateResponse(request=request, name="cadastro.html")

# 3. Função que grava o Novo Estagiário no Banco de Dados SQLite
@app.post("/cadastrar_usuario")
async def cadastrar_usuario(
    nome: str = Form(...),
    cpf: str = Form(...),
    faculdade: str = Form(...),
    periodo: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    # Grava os dados na tabela 'estagiarios'
    novo_estagiario = models.Estagiario(
        nome=nome,
        cpf=cpf,
        faculdade=faculdade,
        periodo=periodo,
        senha_hash=senha
    )
    db.add(novo_estagiario)
    db.commit()
    
    # Após cadastrar, redireciona o aluno de volta para a tela de login
    return RedirectResponse(url="/", status_code=303)

# 4. Rota do Painel do Aluno
@app.get("/painel", response_class=HTMLResponse)
async def painel_aluno(request: Request):
    return templates.TemplateResponse(request=request, name="painel_aluno.html")