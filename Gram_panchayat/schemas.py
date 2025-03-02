from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, Annotated, List
from datetime import date, datetime
from pydantic import validator

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
    
class AssetCreate(AssetBase):
    User_name: str


class AssetResponse(AssetBase):
    Asset_id: int
    User_name: str

    class Config:
        orm_mode = True
    
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
    
# this part is for family schems panchayat employee##########################################################################
# Update the schemas with the corrected response format

class FamMemberResp(BaseModel):
    member_citizen_id: int
    member_user_name: str

    class Config:
        orm_mode = True


# This is for the GET response which will include all members
class FamRespWithMembers(BaseModel):
    family_id: int
    head_citizen_id: int
    members: List[FamMemberResp]

    class Config:
        orm_mode = True


# This is for the POST response which just has family_id and head_citizen_id
class FamCreateResp(BaseModel):
    family_id: int
    head_citizen_id: int

    class Config:
        orm_mode = True


class FamReq(BaseModel):
    user_name: str  # username of the head


# Response model for GET (with members)
class FamRespModel(BaseModel):
    data: List[FamRespWithMembers]
    message: str
    statusCode: int

    class Config:
        orm_mode = True


# Response model for POST (simplified)
class FamCreateRespModel(BaseModel):
    data: FamCreateResp
    message: str
    statusCode: int

    class Config:
        orm_mode = True
        
# Add these schemas to your existing schemas.py file

class FamMemberReq(BaseModel):
    family_id: int
    member_user_name: str


class FamMemberData(BaseModel):
    member_citizen_id: int
    member_user_name: str

    class Config:
        from_attributes = True  # Using from_attributes instead of orm_mode for Pydantic v2


class FamMemberRespModel(BaseModel):
    data: FamMemberData
    message: str
    statusCode: int

    class Config:
        from_attributes = True  # Using from_attributes instead of orm_mode for Pydantic v2
        ###############################################
        
        


# this part is for schemas for issues panchayat employee###################################################
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class IssueResponse(BaseModel):
    issue_id: int
    description: str
    status: str
    citizen_id: int
    user_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IssuesListResponse(BaseModel):
    data: List[IssueResponse]
    message: str
    statusCode: int

    class Config:
        from_attributes = True
        
class UpdateIssueRequest(BaseModel):
    issue_id: int
    status: str

    # Validate that status is one of the allowed values
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['PENDING', 'IN_PROGRESS', 'RESOLVED', 'REJECTED']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v

class UpdateIssueResponse(BaseModel):
    message: str
    statusCode: int
    
    
# this part is for schemas for documents panchayat employee###################################################
class DocumentResponse(BaseModel):
    Doc_id: int
    Type: str
    Pdf_data: str  # Will contain base64 encoded PDF data
    Citizen_id: int
    user_name: str

    class Config:
        from_attributes = True

class DocumentsListResponse(BaseModel):
    data: List[DocumentResponse]
    message: str
    statusCode: int

class GetDocumentRequest(BaseModel):
    user_name: str
    
class DocumentUploadRequest(BaseModel):
    Type: str
    pdf_data: str
    user_name: str

class DocumentCreatedResponse(BaseModel):
    Doc_id: int
    Citizen_id: int

class DocumentUploadResponse(BaseModel):
    data: List[DocumentCreatedResponse]
    message: str
    statusCode: int
    
class DocumentDeleteResponse(BaseModel):
    message: str
    statusCode: int
    
    
# this part is for schemas for financial records panchayat employee###################################################
class FinancialDataRequest(BaseModel):
    year: int
    Annual_Income: float
    Income_source: str
    Tax_paid: float
    Tax_liability: float
    Debt_liability: float
    Credit_score: Optional[int] = None
    user_name: str

class FinancialDataResponse(BaseModel):
    Financial_id: int
    Last_updated: datetime
    Citizen_fk: int

class FinancialCreateResponse(BaseModel):
    data: List[FinancialDataResponse]
    message: str
    statusCode: int

class FinancialDataGetRequest(BaseModel):
    user_name: str
    year: Optional[int] = None

# Response models
class FinancialDataItem(BaseModel):
    Financial_id: int
    year: int
    Annual_Income: float
    Income_source: str
    Tax_paid: float
    Tax_liability: float
    Debt_liability: float
    Credit_score: Optional[int]
    Last_updated: datetime
    Citizen_fk: int

class FinancialDataGetResponse(BaseModel):
    data: List[FinancialDataItem] = []
    message: str
    statusCode: int
    
class BasicResponse(BaseModel):
    message: str
    statusCode: int
    
    
# this part is for schemas for welfare schemes panchayat employee###################################################

class WelfareSchemeItem(BaseModel):
    Scheme_id: int
    Scheme_name: str
    Description: Optional[str] = None
    Application_deadline: Optional[date] = None

class WelfareSchemesResponse(BaseModel):
    data: List[WelfareSchemeItem] = []
    message: str
    statusCode: int
    
class WelfareEnrolItem(BaseModel):
    Citizen_fk: int
    user_name: str
    Scheme_fk: int
    scheme_name: str
    status: str

class WelfareEnrolResponse(BaseModel):
    data: List[WelfareEnrolItem] = []
    message: str
    statusCode: int
    
class WelfareEnrolUpdateRequest(BaseModel):
    scheme_id: int
    citizen_id: int
    status: str
    
    
    
# this part is for schemas for infrastructure panchayat employee###################################################

class InfrastructureItem(BaseModel):
    Infra_id: int
    Description: Optional[str] = None
    Location: Optional[str] = None
    Funding: float
    Actual_cost: float
    Government_agencies_fk: int
    government_agency_user_name: str

class InfrastructureResponse(BaseModel):
    data: List[InfrastructureItem] = []
    message: str
    statusCode: int
    
    
class InfrastructureUpdateRequest(BaseModel):
    Infra_id: int
    actual_cost: float
    
    
class EnvironmentalDataItem(BaseModel):
    Year: int
    Aqi: float
    Forest_cover: float
    Odf: float
    Afforestation_data: float
    Precipitation: float
    Water_quality: float

class EnvironmentalDataResponse(BaseModel):
    data: List[EnvironmentalDataItem] = []
    message: str
    statusCode: int
