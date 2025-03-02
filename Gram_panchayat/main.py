from fastapi import FastAPI,APIRouter,Depends,status,Response,HTTPException
from sqlalchemy.orm import Session
from .import schemas,models
from .database import engine,get_db
from .database import SessionLocal
from passlib.context import CryptContext
from .hashing import Hash
from .routers import user
from .routers import admin
from .routers import citizen
from .routers import panchayat_employee
from .routers import government_agency
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change to specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

models.Base.metadata.create_all(bind=engine) 

app.include_router(user.router)
app.include_router(admin.router)
app.include_router(citizen.router)
app.include_router(panchayat_employee.router)
app.include_router(government_agency.router)


# Dependency




