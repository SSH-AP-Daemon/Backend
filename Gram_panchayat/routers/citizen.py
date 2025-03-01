from fastapi import APIRouter, Depends, status, Response, HTTPException, Body, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..database import get_db
from .. import jwt_handler, models, schemas
from pydantic import BaseModel
import logging

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
    
    # Try to get token from Authorization header
    if authorization:
        try:
            scheme, token = authorization.split()
            logger.info(f"Auth scheme: {scheme}")
            logger.info(f"Token from Authorization: {token[:10]}...")  # Only log part of the token
            if scheme.lower() == "bearer":
                jwt_token = token
        except Exception as e:
            logger.error(f"Failed to process authorization header: {str(e)}")
    
    # If not found in Authorization header, try JWT header
    if not jwt_token and JWT:
        jwt_token = JWT
        logger.info(f"Using token from JWT header: {JWT[:10]}...")  # Only log part of the token
    
    # If still no token, raise exception
    if not jwt_token:
        logger.error("No token found in headers")
        raise credentials_exception
    
    # Validate the token format (basic check)
    if not jwt_token or not "." in jwt_token or jwt_token.count(".") != 2:
        logger.error(f"Invalid token format: {jwt_token[:10]}...")
        raise credentials_exception
    
    try:
        logger.info("About to verify token")
        payload = jwt_handler.verify_token(jwt_token, credentials_exception)
        logger.info(f"Token verified successfully")
        
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

# Get citizen assets
@router.get('/assets', response_model=schemas.AssetsResponse)
def get_citizen_assets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Log the function call
    logger.info(f"get_citizen_assets called for user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Get all assets for the current user
    assets = db.query(models.Asset).filter(models.Asset.User_name == current_user.User_name).all()
    logger.info(f"Found {len(assets)} assets for user: {current_user.User_name}")
    
    # Format the response
    asset_data_list = []
    for asset in assets:
        asset_data = {
            "type": asset.Type,
            "valuation": asset.Valuation
        }
        
        # If asset type is agricultural land, add additional fields
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
    # Log the function call
    logger.info(f"get_citizen_family called for user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Get all family members where current user is the head
    family_members_as_head = db.query(models.Family).filter(
        models.Family.User_name == current_user.User_name
    ).all()
    
    # Get all families where current user is a member
    families_as_member = db.query(models.Family).filter(
        models.Family.Member_name == current_user.User_name
    ).all()
    
    logger.info(f"Found {len(family_members_as_head)} members as head, {len(families_as_member)} families as member")
    
    # Collect all unique family members
    family_data_list = []
    
    # Add members from families where user is head
    for family in family_members_as_head:
        family_data_list.append(schemas.FamilyMemberData(
            User_name=family.Member_name
        ))
    
    # Add heads from families where user is a member
    for family in families_as_member:
        family_data_list.append(schemas.FamilyMemberData(
            User_name=family.User_name
        ))
    
    # Remove duplicates by converting to a dictionary with User_name as key
    unique_members = {member.User_name: member for member in family_data_list}
    
    # Remove the current user from the list if present
    if current_user.User_name in unique_members:
        unique_members.pop(current_user.User_name)
    
    # Convert back to list
    unique_member_list = list(unique_members.values())
    
    return schemas.FamilyResponse(
        data=unique_member_list,
        message="Family members retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

# Get citizen issues
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

# Create an issue
@router.post('/issues', response_model=schemas.IssueCreateResponse, status_code=status.HTTP_201_CREATED)
def create_citizen_issue(
    issue_data: schemas.IssueCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Log the function call
    logger.info(f"create_citizen_issue called for user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Create a new issue
    new_issue = models.Issue(
        User_name=current_user.User_name,
        description=issue_data.description,
        status="PENDING"
    )
    
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    
    logger.info(f"Created issue with ID: {new_issue.Issue_id}")
    
    return schemas.IssueCreateResponse(
        Issue_id=new_issue.Issue_id,
        message="Issue created successfully",
        statusCode=status.HTTP_201_CREATED
    )

# Get citizen profile
@router.get('/profile', response_model=schemas.CitizenProfileResponse)
def get_citizen_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Log the function call
    logger.info(f"get_citizen_profile called for user: {current_user.User_name}")
    
    # Check if the user is a citizen
    is_citizen(current_user)
    
    # Get citizen details
    citizen = db.query(models.Citizen).filter(
        models.Citizen.User_name == current_user.User_name
    ).first()
    
    if not citizen:
        logger.error(f"No citizen profile found for user: {current_user.User_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found"
        )
    
    # Format the response
    profile_data = {
        "User_name": current_user.User_name,
        "Name": current_user.Name,
        "Email": current_user.Email,
        "Contact_number": current_user.Contact_number,
        "Date_of_birth": citizen.Date_of_birth,
        "Gender": citizen.Gender,
        "Address": citizen.Address,
        "Educational_qualification": citizen.Educational_qualification,
        "Occupation": citizen.Occupation
    }
    
    return schemas.CitizenProfileResponse(
        data=schemas.CitizenProfileData(**profile_data),
        message="Profile retrieved successfully",
        statusCode=status.HTTP_200_OK
    )