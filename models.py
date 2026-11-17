from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(140))
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    faculdade: Mapped[str] = mapped_column(String(180), default='')
    periodo: Mapped[str] = mapped_column(String(40), default='')
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='aluno', index=True)
    status: Mapped[str] = mapped_column(String(20), default='pendente', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    progress = relationship('Progress', back_populates='user', cascade='all, delete-orphan')

class Module(Base):
    __tablename__ = 'modules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(180))
    summary: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, unique=True)

class Progress(Base):
    __tablename__ = 'progress'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey('modules.id'), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship('User', back_populates='progress')
    module = relationship('Module')
    __table_args__ = (UniqueConstraint('user_id','module_id', name='uq_user_module'),)

class Activity(Base):
    __tablename__ = 'activities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    activity_date: Mapped[date] = mapped_column(Date, default=date.today)
    description: Mapped[str] = mapped_column(Text)
    hours: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default='pendente', index=True)
    preceptor_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
