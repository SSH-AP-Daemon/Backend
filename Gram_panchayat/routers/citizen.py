from fastapi import APIRouter, Depends, status, Response, HTTPException, Body, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..database import get_db
from .. import jwt_handler, models, schemas
from pydantic import BaseModel
import logging
from datetime import date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/citizen",
    tags=['Citizen']
)

def get_current_user(
    authorization: Optional[str] = Header(None),
    JWT: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    logger.info("get_current_user function called")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    jwt_token = None
    
    if authorization:
        try:
            scheme, token = authorization.split()
            logger.info(f"Auth scheme: {scheme}")
            logger.info(f"Token: {token[:10]}...")  
            if scheme.lower() == "bearer":
                jwt_token = token
        except Exception as e:
            logger.error(f"Failed to process authorization header: {str(e)}")
    
    if not jwt_token and JWT:
        jwt_token = JWT
        logger.info("Using token from JWT header")
    
    if not jwt_token:
        logger.error("No token found in headers")
        raise credentials_exception
    
    try:
        payload = jwt_handler.verify_token(jwt_token, credentials_exception)
        username: str = payload.get("sub")
        if username is None:
            logger.error("No username in token payload")
            raise credentials_exception
        token_data = schemas.TokenData(User_name=username)
        logger.info(f"Authenticated user: {username}")
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.User_name == token_data.User_name).first()
    if user is None:
        logger.error(f"No user found for username: {token_data.User_name}")
        raise credentials_exception
    return user

def is_citizen(user: models.User):
    if user.User_type != "CITIZEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can access this resource"
        )
    return user

@router.get('/assets', response_model=schemas.AssetsResponse)
def get_citizen_assets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_assets called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    assets = db.query(models.Asset).filter(models.Asset.User_name == current_user.User_name).all()
    logger.info(f"Found {len(assets)} assets for user: {current_user.User_name}")
    
    # Format the response
    asset_data_list = []
    for asset in assets:
        asset_data = {
            "type": asset.Type,
            "valuation": asset.Valuation
        }
        
        if asset.Type.lower() == "agricultural_land" and asset.agricultural_land:
            agri_land = asset.agricultural_land
            asset_data.update({
                "Year": agri_land.Year,
                "Season": agri_land.Season,
                "Crop_type": agri_land.Crop_type,
                "Area_cultivated": agri_land.Area_cultivated,
                "Yield": agri_land.Yield
            })
            
        asset_data_list.append(schemas.AssetData(**asset_data))
    
    return schemas.AssetsResponse(
        data=asset_data_list,
        message="Assets retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

# Get citizen family
@router.get('/family', response_model=schemas.FamilyResponse)
def get_citizen_family(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_family called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    family_members_as_head = db.query(models.Family).filter(
        models.Family.User_name == current_user.User_name
    ).all()
    
    families_as_member = db.query(models.Family).filter(
        models.Family.Member_name == current_user.User_name
    ).all()
    
    logger.info(f"Found {len(family_members_as_head)} members as head, {len(families_as_member)} families as member")
    
    family_data_list = []
    
    for family in family_members_as_head:
        family_data_list.append(schemas.FamilyMemberData(
            User_name=family.Member_name
        ))
    
    for family in families_as_member:
        family_data_list.append(schemas.FamilyMemberData(
            User_name=family.User_name
        ))
    
    unique_members = {member.User_name: member for member in family_data_list}
    
    if current_user.User_name in unique_members:
        unique_members.pop(current_user.User_name)
    
    unique_member_list = list(unique_members.values())
    
    return schemas.FamilyResponse(
        data=unique_member_list,
        message="Family members retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

@router.get('/issues', response_model=schemas.IssuesResponse)
def get_citizen_issues(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Log the function call
    logger.info(f"get_citizen_issues called for user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Get all issues raised by the current user
    issues = db.query(models.Issue).filter(
        models.Issue.User_name == current_user.User_name
    ).all()
    
    logger.info(f"Found {len(issues)} issues for user: {current_user.User_name}")
    
    # Format the response
    issue_data_list = []
    for issue in issues:
        issue_data = {
            "Issue_id": issue.Issue_id,
            "description": issue.description,
            "status": issue.status
        }
        issue_data_list.append(schemas.IssueData(**issue_data))
    
    return schemas.IssuesResponse(
        data=issue_data_list,
        message="Issues retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

# Delete an issue
@router.delete('/issue', status_code=status.HTTP_200_OK)
def delete_citizen_issue(
    Issue_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Log the function call
    logger.info(f"delete_citizen_issue called for issue ID: {Issue_id} by user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Get the issue
    issue = db.query(models.Issue).filter(
        models.Issue.Issue_id == Issue_id
    ).first()
    
    # Check if issue exists
    if not issue:
        logger.error(f"Issue with ID {Issue_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with ID {Issue_id} not found"
        )
    
    # Check if issue belongs to the current user
    if issue.User_name != current_user.User_name:
        logger.error(f"Issue {Issue_id} does not belong to user {current_user.User_name}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own issues"
        )
    
    # Check if issue is in 'OPEN' status
    if issue.status != 'OPEN':
        logger.error(f"Issue {Issue_id} is not in 'OPEN' status, current status: {issue.status}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete issues with 'OPEN' status"
        )
    
    # Delete the issue
    db.delete(issue)
    db.commit()
    
    logger.info(f"Issue {Issue_id} deleted successfully")
    
    return {
        "message": "Issue deleted successfully",
        "statusCode": status.HTTP_200_OK
    }

# Get citizen documents
@router.get('/document', response_model=schemas.DocumentResponse)
def get_citizen_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Log the function call
    logger.info(f"get_citizen_documents called for user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Get all documents for the current user
    documents = db.query(models.Document).filter(
        models.Document.User_name == current_user.User_name
    ).all()
    
    logger.info(f"Found {len(documents)} documents for user: {current_user.User_name}")
    
    # Format the response
    document_data_list = []
    for document in documents:
        document_data = {
            "Type": document.Type,
            "Pdf_data": document.Pdf_data  # This will be base64 encoded
        }
        document_data_list.append(schemas.DocumentData(**document_data))
    
    return schemas.DocumentResponse(
        data=document_data_list,
        message="Documents retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

@router.get('/financial-data', response_model=schemas.FinancialDataResponse)
def get_citizen_financial_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_financial_data called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    financial_data = db.query(models.FinancialData).filter(
        models.FinancialData.User_name == current_user.User_name
    ).all()
    
    logger.info(f"Found {len(financial_data)} financial records for user: {current_user.User_name}")
    
    financial_data_list = []
    for data in financial_data:
        financial_record = {
            "year": data.year,
            "Annual_Income": data.Annual_Income,
            "Income_source": data.Income_source,
            "Tax_paid": data.Tax_paid,
            "Tax_liability": data.Tax_liability,
            "Debt_liability": data.Debt_liability,
            "Credit_score": data.Credit_score,
            "Last_updated": data.Last_updated
        }
        financial_data_list.append(schemas.FinancialRecordData(**financial_record))
    
    return schemas.FinancialDataResponse(
        data=financial_data_list,
        message="Financial data retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

@router.get('/welfare-scheme', response_model=schemas.WelfareSchemeResponse)
def get_citizen_welfare_schemes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_welfare_schemes called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    welfare_schemes = db.query(models.WelfareScheme).all()
    
    enrolled_schemes = db.query(models.WelfareEnrol).filter(
        models.WelfareEnrol.User_name == current_user.User_name
    ).all()
    
    enrolled_scheme_dict = {enrol.Scheme_fk: enrol.status for enrol in enrolled_schemes}
    
    # Format the response
    scheme_data_list = []
    for scheme in welfare_schemes:
        scheme_data = {
            "Scheme_fk": scheme.Scheme_id,
            "Scheme_name": scheme.Scheme_name,
            "Description": scheme.Description,
            "Application_deadline": scheme.Application_deadline,
            "status": enrolled_scheme_dict.get(scheme.Scheme_id, "NOT_APPLIED")
        }
        scheme_data_list.append(schemas.WelfareSchemeData(**scheme_data))
    
    logger.info(f"Found {len(scheme_data_list)} welfare schemes, {len(enrolled_schemes)} enrolled")
    
    return schemas.WelfareSchemeResponse(
        data=scheme_data_list,
        message="Welfare schemes retrieved successfully",
        statusCode=status.HTTP_200_OK
    )
    
@router.post('/welfare-enrol', response_model=schemas.WelfareEnrolResponse)
def enrol_in_welfare_scheme(
    Scheme_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"enrol_in_welfare_scheme called for scheme ID: {Scheme_id} by user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    scheme = db.query(models.WelfareScheme).filter(
        models.WelfareScheme.Scheme_id == Scheme_id
    ).first()
    
    if not scheme:
        logger.error(f"Welfare scheme with ID {Scheme_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Welfare scheme with ID {Scheme_id} not found"
        )
    
    if scheme.Application_deadline and scheme.Application_deadline < date.today():
        logger.error(f"Application deadline for scheme {Scheme_id} has passed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application deadline for this scheme has passed"
        )
    
    existing_enrolment = db.query(models.WelfareEnrol).filter(
        models.WelfareEnrol.User_name == current_user.User_name,
        models.WelfareEnrol.Scheme_fk == Scheme_id
    ).first()
    
    if existing_enrolment:
        logger.error(f"User {current_user.User_name} already enrolled in scheme {Scheme_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this scheme"
        )
    
    new_enrolment = models.WelfareEnrol(
        User_name=current_user.User_name,
        Scheme_fk=Scheme_id,
        status="PENDING"  # Default status
    )
    
    db.add(new_enrolment)
    db.commit()
    db.refresh(new_enrolment)
    
    logger.info(f"User {current_user.User_name} successfully enrolled in scheme {Scheme_id}")
    
    return schemas.WelfareEnrolResponse(
        data=new_enrolment.status,
        message="Successfully applied for welfare scheme",
        statusCode=status.HTTP_201_CREATED
    )

@router.get('/infrastructure', response_model=schemas.InfrastructureResponse)
def get_infrastructure_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_infrastructure_projects called by user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    infrastructure_projects = db.query(models.Infrastructure).all()
    
    logger.info(f"Found {len(infrastructure_projects)} infrastructure projects")
    
    project_data_list = []
    for project in infrastructure_projects:
        project_data = {
            "Description": project.Description,
            "Location": project.Location,
            "Funding": project.Funding,
            "Actual_cost": project.Actual_cost
        }
        project_data_list.append(schemas.InfrastructureData(**project_data))
    
    return schemas.InfrastructureResponse(
        data=project_data_list,
        message="Infrastructure projects retrieved successfully",
        statusCode=status.HTTP_200_OK
    )