from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from datetime import date

Base = declarative_base()

class Estagiario(Base):
    __tablename__ = 'estagiarios'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    faculdade = Column(String)
    periodo = Column(String)
    data_inicio = Column(Date, default=date.today)
    data_termino = Column(Date, nullable=True)
    senha_hash = Column(String)
    status = Column(String, default="Ativo")

class Setor(Base):
    __tablename__ = 'setores'
    id = Column(Integer, primary_key=True, index=True)
    nome_setor = Column(String, unique=True, index=True)
    conteudo_teorico = Column(Text)

class RegistroDiario(Base):
    __tablename__ = 'registros_diario'
    id = Column(Integer, primary_key=True, index=True)
    estagiario_id = Column(Integer, ForeignKey('estagiarios.id'))
    setor_id = Column(Integer, ForeignKey('setores.id'))
    data_atividade = Column(Date, default=date.today)
    descricao_pratica = Column(Text)
    carga_horaria = Column(Integer)
    validado_preceptor = Column(Boolean, default=False)