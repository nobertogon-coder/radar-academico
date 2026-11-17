import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

url = os.getenv('DATABASE_URL', '').strip()
if url.startswith('postgres://'):
    url = url.replace('postgres://', 'postgresql+psycopg://', 1)
elif url.startswith('postgresql://'):
    url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
if not url:
    data_dir = Path(os.getenv('DATA_DIR', './data'))
    data_dir.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{(data_dir / 'radar_academico.db').resolve()}"
connect_args = {'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite') else {}
engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
if url.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def set_sqlite_pragmas(dbapi_connection, _):
        cur = dbapi_connection.cursor()
        cur.execute('PRAGMA foreign_keys=ON')
        cur.execute('PRAGMA journal_mode=WAL')
        cur.execute('PRAGMA busy_timeout=30000')
        cur.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
