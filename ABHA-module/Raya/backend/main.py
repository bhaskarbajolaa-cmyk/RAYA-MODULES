from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import users, abha, tokens, face
from app.core.database import abha_engine, raya_engine
from app.models import domain

# Create database tables if they don't exist
domain.Base.metadata.create_all(bind=abha_engine)
domain.Base.metadata.create_all(bind=raya_engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(abha.router, prefix="/api/abha", tags=["abha"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["tokens"])
app.include_router(face.router, prefix="/api/face", tags=["face"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}
