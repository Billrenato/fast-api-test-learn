from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Criar engine do SQLite (arquivo local)
DATABASE_URL = "sqlite:///./meubanco.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Necessário para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

