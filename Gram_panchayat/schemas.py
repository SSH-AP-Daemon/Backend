from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, Annotated, List
from datetime import date, datetime

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
class FamilyBase(BaseModel):
    Head_citizen_id: int
    Member_citizen_id: int
    Relationship: str
    
    class Config:
        from_attributes = True

class FamilyMemberData(BaseModel):
    User_name: str  # Keep User_name for display purposes
    
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

class IssueCreate(BaseModel):
    description: str
    
    class Config:
        from_attributes = True

class IssueData(IssueBase):
    Issue_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
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
    
    class Config:
        from_attributes = True

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
    
class DocumentData(BaseModel):
    Type: str
    Pdf_data: bytes
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    data: List[DocumentData]
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

class FinancialRecordData(BaseModel):
    year: int
    Annual_Income: float
    Income_source: str
    Tax_paid: float
    Tax_liability: float
    Debt_liability: float
    Credit_score: Optional[int] = None
    Last_updated: datetime
    
    class Config:
        from_attributes = True

class FinancialDataResponse(BaseModel):
    data: List[FinancialRecordData]
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

# For Welfare Scheme endpoint
class WelfareSchemeData(BaseModel):
    Scheme_fk: int
    Scheme_name: str
    Description: Optional[str] = None
    Application_deadline: Optional[date] = None
    status: str  # "NOT_APPLIED", "PENDING", "APPROVED", "REJECTED"
    
    class Config:
        from_attributes = True

class WelfareSchemeResponse(BaseModel):
    data: List[WelfareSchemeData]
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

class WelfareEnrolResponse(BaseModel):
    data: str  
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

class InfrastructureData(BaseModel):
    Description: Optional[str] = None
    Location: Optional[str] = None
    Funding: float
    Actual_cost: float
    
    class Config:
        from_attributes = True

class InfrastructureResponse(BaseModel):
    data: List[InfrastructureData]
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

class InfrastructureCreate(BaseModel):
    Description: Optional[str] = None
    Location: Optional[str] = None
    Funding: float
    Actual_cost: float = 0
    
    class Config:
        from_attributes = True

class InfrastructureCreateResponse(BaseModel):
    Infra_id: int
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

        
class WelfareSchemeCreate(BaseModel):
    Scheme_name: str
    Description: Optional[str] = None
    Application_deadline: Optional[date] = None
    
    class Config:
        from_attributes = True

class WelfareSchemeCreateResponse(BaseModel):
    Scheme_id: int
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

# Welfare scheme models for government agencies
class WelfareSchemeAgencyData(BaseModel):
    Scheme_id: int
    Scheme_name: str
    Description: Optional[str] = None
    Application_deadline: Optional[date] = None
    
    class Config:
        from_attributes = True

class WelfareSchemeListResponse(BaseModel):
    data: List[WelfareSchemeAgencyData]
    message: str
    statusCode: int
    
    class Config:
        from_attributes = True

# User login response
class UserLoginResponse(BaseModel):
    JWT: str
    token_type: str
    Name: str
    User_name: str
    User_type: str
    Email: Optional[str] = None
    Contact_number: str
    
    class Config:
        from_attributes = True

# User login request
class UserLogin(BaseModel):
    username: str
    password: str