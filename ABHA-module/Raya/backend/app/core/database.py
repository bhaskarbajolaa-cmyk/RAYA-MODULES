import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Connect to the local databases
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.path.join(BASE_DIR, "database").replace("\\", "/")

# Create connection URLs
ABHA_DB_URL = f"sqlite:///{DATABASE_DIR}/abha.db"
RAYA_DB_URL = f"sqlite:///{DATABASE_DIR}/raya.db"

# Engines
abha_engine = create_engine(ABHA_DB_URL, connect_args={"check_same_thread": False})
raya_engine = create_engine(RAYA_DB_URL, connect_args={"check_same_thread": False})

# Session locals
SessionLocalABHA = sessionmaker(autocommit=False, autoflush=False, bind=abha_engine)
SessionLocalRaya = sessionmaker(autocommit=False, autoflush=False, bind=raya_engine)

Base = declarative_base()

# Dependencies
def get_abha_db():
    db = SessionLocalABHA()
    try:
        yield db
    finally:
        db.close()

def get_raya_db():
    db = SessionLocalRaya()
    try:
        yield db
    finally:
        db.close()
