from fastapi import APIRouter,Depends,status,Response,HTTPException,Body
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models,schemas
from ..hashing import Hash
from  .. import jwt_handler
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def create_user(payload: schemas.UserRegisterUnion, db: Session = Depends(get_db)):
    
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
            User_name=payload.User_name,
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
            User_name=payload.User_name,
            Gender=payload.Gender,
            Date_of_birth=payload.Date_of_birth,
            Address=payload.Address
        )
        db.add(new_detail)
    elif isinstance(payload, schemas.PanchayatEmployee):
        new_detail = models.PanchayatEmployee(
            User_name=payload.User_name,
            Role=payload.Role
        )
        db.add(new_detail)
    elif isinstance(payload, schemas.GovernmentAgencies):
        new_detail = models.GovernmentAgencies(
            User_name=payload.User_name,
            Role=payload.Role
        )
        db.add(new_detail)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type provided")
    
    db.commit()
    return new_user



@router.post('/login',status_code=status.HTTP_200_OK)
async def login_user(request:schemas.Login,db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.User_name == request.User_name).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Invalid Credentials")
    if not Hash.verify(user.Password,request.Password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Incorrect Password")
    if(user.is_verified == 0):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"User not verified")
    access_token = jwt_handler.create_access_token(
        data={"sub": user.User_name}
    )
    
    if user.User_type == "CITIZEN":
        citizen = db.query(models.Citizen).filter(models.Citizen.User_name == user.User_name).first()
        return {"access_token": access_token, "token_type": "bearer",
                "username": user.User_name, 
                "name": user.Name,
                "email": user.Email,
                "contact_number": user.Contact_number,
                "user_type": user.User_type,
                "Date_of_birth": citizen.Date_of_birth,
                "Date_of_death": citizen.Date_of_death,
                "Gender": citizen.Gender,
                "Address": citizen.Address,
                "Educational_qualification": citizen.Educational_qualification,
                "Occupation": citizen.Occupation
                }
    elif user.User_type == "ADMIN":
        admin = db.query(models.Admin).filter(models.Admin.User_name == user.User_name).first()
        return{
            "access_token": access_token, "token_type": "bearer",
            "username": user.User_name, 
            "name": user.Name,
            "email": user.Email,
            "contact_number": user.Contact_number,
            "user_type": user.User_type,
            "Gender": admin.Gender,
            "Date_of_birth": admin.Date_of_birth,
            "Address": admin.Address
        }
    elif user.User_type == "GOVERNMENT_AGENCY":
        governmentagency = db.query(models.GovernmentAgencies).filter(models.GovernmentAgencies.User_name == user.User_name).first()
        return{
            "access_token": access_token, "token_type": "bearer",
            "username": user.User_name, 
            "name": user.Name,
            "email": user.Email,
            "contact_number": user.Contact_number,
            "user_type": user.User_type,
            "Role": governmentagency.Role
        }
    elif user.User_type == "PANCHAYAT_EMPLOYEE":
        panchayatemployee = db.query(models.PanchayatEmployee).filter(models.PanchayatEmployee.User_name == user.User_name).first()
        return{
            "access_token": access_token, "token_type": "bearer",
            "username": user.User_name, 
            "name": user.Name,
            "email": user.Email,
            "contact_number": user.Contact_number,
            "user_type": user.User_type,
            "Role": panchayatemployee.Role
        }
        
        
        
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"User not found")