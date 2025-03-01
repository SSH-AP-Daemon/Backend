# app/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, Annotated
from datetime import date

class BaseUser(BaseModel):
    User_name: str
    Password: str
    Name: str
    Email: Optional[str] = None
    Contact_number: str
    User_type: Literal["CITIZEN", "ADMIN", "GOVERNMENT_AGENCY", "PANCHAYAT_EMPLOYEE"]

    class Config:
       
        from_attributes = True

class Citizen(BaseUser):
    
    User_type: Literal["CITIZEN"] = "CITIZEN"
    Date_of_birth: date
    Date_of_death: Optional[date] = None
    Gender: str
    Address: str
    Educational_qualification: str
    Occupation: str

class Admin(BaseUser):
    User_type: Literal["ADMIN"] = "ADMIN"
    Gender: str
    Date_of_birth: date
    Address: str

class GovernmentAgencies(BaseUser):
    User_type: Literal["GOVERNMENT_AGENCY"] = "GOVERNMENT_AGENCY"
    Role: str

class PanchayatEmployee(BaseUser):
    User_type: Literal["PANCHAYAT_EMPLOYEE"] = "PANCHAYAT_EMPLOYEE"
    Role: str

# Create a union of the registration models using a discriminator
UserRegisterUnion = Annotated[
    Union[Citizen, Admin, GovernmentAgencies, PanchayatEmployee],
    Field(discriminator="User_type")
]

class Login(BaseModel):
    User_name: str
    Password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    User_name: Optional[str] = None
