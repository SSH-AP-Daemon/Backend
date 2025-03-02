from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . import jwt_handler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")#from the login url its going to fetch the token


def get_current_user(data: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return jwt_handler.verify_token(data, credentials_exception)
