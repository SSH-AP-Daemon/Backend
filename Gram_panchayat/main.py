from fastapi import FastAPI,APIRouter,Depends,status,Response,HTTPException
from sqlalchemy.orm import Session
from .import schemas,models
from .database import engine,get_db
from .database import SessionLocal
from passlib.context import CryptContext
from .hashing import Hash
from .routers import user


app = FastAPI()

models.Base.metadata.create_all(bind=engine) # this will create all the tables in the database

app.include_router(user.router)

# Dependency




