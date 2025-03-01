# Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): 2025-03-01 14:47:04
# Current User's Login: SRINJOY59

from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, Annotated, List
from datetime import date

# Base Models
class BaseUser(BaseModel):
    User_name: str
    Password: str
    Name: str
    Email: Optional[str] = None
    Contact_number: str
    User_type: Literal["CITIZEN", "ADMIN", "GOVERNMENT_AGENCY", "PANCHAYAT_EMPLOYEE"]

    class Config:
        from_attributes = True

# User Type Models
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

# Authentication Models
class Login(BaseModel):
    User_name: str
    Password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    User_name: Optional[str] = None

# Asset Models
class AgriculturalLandBase(BaseModel):
    Year: int
    Season: str
    Crop_type: str
    Area_cultivated: float
    Yield: float
    
    class Config:
        from_attributes = True

class AssetBase(BaseModel):
    Type: str
    Valuation: str
    
    class Config:
        from_attributes = True

class AgriculturalLand(AgriculturalLandBase):
    Land_id: int
    Asset_id: int

class Asset(AssetBase):
    Asset_id: int
    User_name: str
    agricultural_land: Optional[AgriculturalLand] = None

class AssetData(BaseModel):
    type: str
    valuation: str
    Year: Optional[int] = None
    Season: Optional[str] = None
    Crop_type: Optional[str] = None
    Area_cultivated: Optional[float] = None
    Yield: Optional[float] = None
    
    class Config:
        from_attributes = True

class AssetsResponse(BaseModel):
    data: List[AssetData]
    message: str
    statusCode: int

# Family Models
class FamilyMemberData(BaseModel):
    User_name: str
    
    class Config:
        from_attributes = True

class FamilyResponse(BaseModel):
    data: List[FamilyMemberData]
    message: str
    statusCode: int

# Issue Models
class IssueBase(BaseModel):
    description: str
    
    class Config:
        from_attributes = True

class IssueCreate(IssueBase):
    pass

class IssueData(IssueBase):
    Issue_id: int
    status: str
    
    class Config:
        from_attributes = True

class IssuesResponse(BaseModel):
    data: List[IssueData]
    message: str
    statusCode: int

class IssueCreateResponse(BaseModel):
    Issue_id: int
    message: str
    statusCode: int

# Profile Models
class CitizenProfileData(BaseModel):
    User_name: str
    Name: str
    Email: Optional[str]
    Contact_number: str
    Date_of_birth: date
    Gender: str
    Address: str
    Educational_qualification: str
    Occupation: str
    
    class Config:
        from_attributes = True

class CitizenProfileResponse(BaseModel):
    data: CitizenProfileData
    message: str
    statusCode: int

# Generic Response Model
class ResponseModel(BaseModel):
    message: str
    statusCode: int