import os, re, shutil, sqlite3
from datetime import date, datetime
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pwdlib import PasswordHash
from database import engine, get_db, SessionLocal
from models import Base, User, Module, Progress, Activity
from modules.content import MODULES, QUIZZES

APP_SECRET = os.getenv('SECRET_KEY', '')
if not APP_SECRET and os.getenv('ENVIRONMENT') == 'production':
    raise RuntimeError('Defina SECRET_KEY nas variáveis de ambiente.')
APP_SECRET = APP_SECRET or 'dev-only-change-this-secret-before-deploying'
password_hash = PasswordHash.recommended()
app = FastAPI(title='Radar Acadêmico', version='1.0.0')
app.add_middleware(SessionMiddleware, secret_key=APP_SECRET, session_cookie='radar_session', same_site='lax', https_only=os.getenv('ENVIRONMENT') == 'production', max_age=60*60*8)
BASE_DIR = Path(__file__).resolve().parent
app.mount('/static', StaticFiles(directory=BASE_DIR/'static'), name='static')
templates = Jinja2Templates(directory=BASE_DIR/'templates')

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for i, (slug,title,summary,content) in enumerate(MODULES, 1):
            if not db.scalar(select(Module).where(Module.slug == slug)):
                db.add(Module(slug=slug,title=title,summary=summary,content=content,order=i))
        admin_cpf = re.sub(r'\D','',os.getenv('INITIAL_PRECEPTOR_CPF',''))
        admin_password = os.getenv('INITIAL_PRECEPTOR_PASSWORD','')
        if admin_cpf and len(admin_cpf)==11 and admin_password and len(admin_password)>=12:
            user = db.scalar(select(User).where(User.cpf==admin_cpf))
            if not user:
                db.add(User(nome=os.getenv('INITIAL_PRECEPTOR_NAME','Preceptor Administrador'), cpf=admin_cpf,
                            password_hash=password_hash.hash(admin_password), role='preceptor', status='ativo'))
        db.commit()
    finally:
        db.close()

def current_user(request: Request, db: Session):
    uid = request.session.get('user_id')
    return db.get(User, uid) if uid else None

def require_user(request: Request, db: Session):
    user = current_user(request, db)
    if not user or user.status != 'ativo': raise HTTPException(401, 'Faça login para continuar.')
    return user

def require_preceptor(request: Request, db: Session):
    user = require_user(request, db)
    if user.role != 'preceptor': raise HTTPException(403, 'Acesso restrito ao preceptor.')
    return user

def page(request, name, **context):
    return templates.TemplateResponse(request=request, name=name, context=context)

@app.get('/health')
def health(): return {'status':'ok','app':'Radar Acadêmico'}

@app.get('/', response_class=HTMLResponse)
def login_page(request: Request, db: Session=Depends(get_db)):
    user=current_user(request,db)
    if user and user.status=='ativo': return RedirectResponse('/painel',303)
    return page(request,'login.html',error=None)

@app.post('/login')
def login(request: Request, cpf: str=Form(...), senha: str=Form(...), db: Session=Depends(get_db)):
    normalized=re.sub(r'\D','',cpf)
    user=db.scalar(select(User).where(User.cpf==normalized))
    if not user or not password_hash.verify(senha,user.password_hash):
        return page(request,'login.html',error='CPF ou senha inválidos.')
    if user.status!='ativo': return page(request,'login.html',error='Cadastro aguardando liberação do preceptor.')
    request.session.clear(); request.session['user_id']=user.id
    return RedirectResponse('/painel',303)

@app.get('/cadastro', response_class=HTMLResponse)
def cadastro_page(request: Request): return page(request,'cadastro.html',error=None)

@app.post('/cadastro')
def cadastro(request: Request, nome: str=Form(...), cpf: str=Form(...), faculdade: str=Form(''), periodo: str=Form(''), senha: str=Form(...), confirmar: str=Form(...), db: Session=Depends(get_db)):
    normalized=re.sub(r'\D','',cpf)
    if len(normalized)!=11: return page(request,'cadastro.html',error='Informe um CPF com 11 dígitos.')
    if senha != confirmar or len(senha)<10: return page(request,'cadastro.html',error='As senhas devem ser iguais e ter pelo menos 10 caracteres.')
    if db.scalar(select(User).where(User.cpf==normalized)): return page(request,'cadastro.html',error='Já existe cadastro com este CPF.')
    db.add(User(nome=nome.strip(),cpf=normalized,faculdade=faculdade.strip(),periodo=periodo.strip(),password_hash=password_hash.hash(senha),role='aluno',status='pendente'))
    db.commit()
    return page(request,'cadastro.html',success='Cadastro enviado. Aguarde a liberação do preceptor.')

@app.post('/logout')
def logout(request: Request): request.session.clear(); return RedirectResponse('/',303)

@app.get('/painel', response_class=HTMLResponse)
def painel(request: Request, db: Session=Depends(get_db)):
    user=require_user(request,db)
    if user.role=='preceptor': return RedirectResponse('/preceptor',303)
    modules=db.scalars(select(Module).order_by(Module.order)).all()
    rows=db.scalars(select(Progress).where(Progress.user_id==user.id)).all()
    progress={p.module_id:p for p in rows}
    completed=sum(1 for p in rows if p.completed)
    activities=db.scalars(select(Activity).where(Activity.user_id==user.id).order_by(Activity.created_at.desc()).limit(5)).all()
    return page(request,'painel_aluno.html',user=user,modules=modules,progress=progress,completed=completed,activities=activities)

@app.get('/modulo/{slug}', response_class=HTMLResponse)
def modulo(slug: str, request: Request, db: Session=Depends(get_db)):
    user=require_user(request,db)
    mod=db.scalar(select(Module).where(Module.slug==slug))
    if not mod: raise HTTPException(404,'Módulo não encontrado.')
    quiz=QUIZZES.get(slug,[])
    return page(request,'modulo.html',user=user,module=mod,quiz=quiz)

@app.post('/modulo/{slug}/concluir')
def concluir(slug: str, request: Request, db: Session=Depends(get_db)):
    user=require_user(request,db); mod=db.scalar(select(Module).where(Module.slug==slug))
    if not mod: raise HTTPException(404)
    row=db.scalar(select(Progress).where(Progress.user_id==user.id,Progress.module_id==mod.id))
    if not row: row=Progress(user_id=user.id,module_id=mod.id); db.add(row)
    row.completed=True; row.updated_at=datetime.utcnow(); db.commit()
    return RedirectResponse('/painel?msg=modulo-concluido',303)

@app.post('/modulo/{slug}/quiz')
async def enviar_quiz(slug: str, request: Request, db: Session=Depends(get_db)):
    user=require_user(request,db); mod=db.scalar(select(Module).where(Module.slug==slug))
    if not mod or slug not in QUIZZES: raise HTTPException(404)
    form=await request.form()
    questions=QUIZZES[slug]; score=sum(1 for i,q in enumerate(questions) if form.get(f'answer_{i}')==str(q[2]))
    percent=round(score/len(questions)*100)
    row=db.scalar(select(Progress).where(Progress.user_id==user.id,Progress.module_id==mod.id))
    if not row: row=Progress(user_id=user.id,module_id=mod.id); db.add(row)
    row.quiz_score=percent
    if percent>=70: row.completed=True
    db.commit()
    return RedirectResponse(f'/modulo/{slug}?score={percent}',303)

@app.post('/atividade')
def registrar_atividade(request: Request, descricao: str=Form(...), horas: int=Form(...), data_atividade: date=Form(...), db: Session=Depends(get_db)):
    user=require_user(request,db)
    if horas<1 or horas>24 or len(descricao.strip())<8: raise HTTPException(400,'Informe descrição e carga horária válida.')
    db.add(Activity(user_id=user.id,description=descricao.strip(),hours=horas,activity_date=data_atividade)); db.commit()
    return RedirectResponse('/painel',303)

@app.get('/certificado', response_class=HTMLResponse)
def certificado(request: Request, db: Session=Depends(get_db)):
    user=require_user(request,db)
    modules=db.scalars(select(Module)).all()
    done=db.scalar(select(func.count(Progress.id)).where(Progress.user_id==user.id,Progress.completed==True)) or 0
    if done<len(MODULES): raise HTTPException(403,'Conclua os oito módulos para liberar o certificado.')
    return page(request,'certificado.html',user=user,today=date.today())

@app.get('/preceptor', response_class=HTMLResponse)
def preceptor(request: Request, db: Session=Depends(get_db)):
    admin=require_preceptor(request,db)
    pending=db.scalars(select(User).where(User.status=='pendente').order_by(User.created_at)).all()
    activities=db.scalars(select(Activity).where(Activity.status=='pendente').order_by(Activity.created_at)).all()
    students=db.scalars(select(User).where(User.role=='aluno').order_by(User.nome)).all()
    return page(request,'painel_preceptor.html',user=admin,pending=pending,activities=activities,students=students)

@app.post('/preceptor/usuario/{user_id}/ativar')
def ativar_usuario(user_id: int, request: Request, db: Session=Depends(get_db)):
    admin=require_preceptor(request,db); user=db.get(User,user_id)
    if not user: raise HTTPException(404)
    user.status='ativo'; db.commit(); return RedirectResponse('/preceptor',303)

@app.post('/preceptor/atividade/{activity_id}/validar')
def validar_atividade(activity_id: int, request: Request, status: str=Form(...), feedback: str=Form(''), db: Session=Depends(get_db)):
    admin=require_preceptor(request,db); activity=db.get(Activity,activity_id)
    if not activity: raise HTTPException(404)
    if status not in ('validada','rejeitada'): raise HTTPException(400)
    activity.status=status; activity.feedback=feedback.strip(); activity.preceptor_id=admin.id; db.commit()
    return RedirectResponse('/preceptor',303)

@app.get('/preceptor/backup')
def backup(request: Request, db: Session=Depends(get_db)):
    require_preceptor(request,db)
    if not str(engine.url).startswith('sqlite'): raise HTTPException(400,'Banco PostgreSQL: utilize a rotina de backup do provedor.')
    source=Path(engine.url.database)
    if not source.exists(): raise HTTPException(404,'Banco ainda não criado.')
    dest=BASE_DIR/'backups'/f'radar_backup_{datetime.utcnow():%Y%m%d_%H%M%S}.db'
    dest.parent.mkdir(exist_ok=True)
    with sqlite3.connect(source) as src, sqlite3.connect(dest) as dst: src.backup(dst)
    return FileResponse(dest,filename=dest.name,media_type='application/octet-stream')
