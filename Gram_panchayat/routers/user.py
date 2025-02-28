from fastapi import APIRouter,Depends,status,Response,HTTPException,Body
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models,schemas
from ..hashing import Hash
from  .. import token
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post('/register', status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserRegisterUnion, db: Session = Depends(get_db)):
    
    if db.query(models.User).filter(models.User.User_name == payload.User_name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    
    new_user = models.User(
        User_name=payload.User_name,
        Password=Hash.bcrypt(payload.Password),
        Name=payload.Name,
        Email=payload.Email,
        Contact_number=payload.Contact_number,
        User_type=payload.User_type
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    
    if isinstance(payload, schemas.Citizen):
        new_detail = models.Citizen(
            
            Date_of_birth=payload.Date_of_birth,
            Date_of_death=payload.Date_of_death,
            Gender=payload.Gender,
            Address=payload.Address,
            Educational_qualification=payload.Educational_qualification,
            Occupation=payload.Occupation
        )
        db.add(new_detail)
    elif isinstance(payload, schemas.Admin):
        new_detail = models.Admin(
           
            Gender=payload.Gender,
            Date_of_birth=payload.Date_of_birth,
            Address=payload.Address
        )
        db.add(new_detail)
    elif isinstance(payload, schemas.PanchayatEmployee):
        new_detail = models.PanchayatEmployee(
            
            Role=payload.Role
        )
        db.add(new_detail)
    elif isinstance(payload, schemas.GovernmentAgencies):
        new_detail = models.GovernmentAgencies(
           
            Role=payload.Role
        )
        db.add(new_detail)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type provided")
    
    db.commit()
    return new_user



@router.post('/login',status_code=status.HTTP_200_OK)
def login_user(request:schemas.Login,db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.User_name == request.User_name).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Invalid Credentials")
    if not Hash.verify(user.Password,request.Password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Incorrect Password")
    access_token = token.create_access_token(
        data={"sub": user.User_name}
    )
    
    return {
        "JWT": access_token,
        "token_type": "bearer",
        "Name": user.Name,
        "User_name": user.User_name,
        "User_type": user.User_type,
        "Email": user.Email,
        "Contact_number": user.Contact_number
        
    }
    





    



