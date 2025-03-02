from fastapi import APIRouter, Depends, status, Response, HTTPException, Body, Header
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from typing import List, Optional, Dict, Any
from ..database import get_db
from .. import jwt_handler, models, schemas
from pydantic import BaseModel
import logging
from datetime import date, datetime
from typing import List
from collections import defaultdict
from datetime import datetime
from ..models import Issue, Citizen, User,Document,FinancialData
from sqlalchemy import select
from ..schemas import IssuesListResponse, IssueResponse,  UpdateIssueRequest, UpdateIssueResponse,FinancialCreateResponse,FinancialDataResponse,FinancialDataRequest
from ..schemas import DocumentsListResponse, DocumentResponse,DocumentUploadRequest,DocumentUploadResponse,DocumentCreatedResponse,DocumentDeleteResponse
from base64 import b64encode, b64decode
from fastapi import File, UploadFile, Form
from pydantic import parse_obj_as
from typing import Optional




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



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

def verify_panchayat_employee(user: models.User, db: Session):
    """
    Verify if the user is a panchayat employee
    """
    if user.User_type != "PANCHAYAT_EMPLOYEE":
        return False
        
    # Verify that the user actually exists in the panchayat employee table
    panchayat_employee = db.query(models.PanchayatEmployee).filter(
        models.PanchayatEmployee.User_name == user.User_name
    ).first()
    
    return panchayat_employee is not None

router = APIRouter(
    prefix="/panchayat-employee",
    tags=["panchayat-employee"],
    responses={404: {"description": "Not found"}},
)


@router.post("/assets", response_model=schemas.AssetResponse)
async def create_asset(
    asset: schemas.AssetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new asset for a user. Only panchayat employees can add assets for users.
    """
    # Verify that the current user is a panchayat employee
    panchayat_role = verify_panchayat_employee(current_user, db)
    if not panchayat_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can add assets"
        )
    
    # Check if the target user exists
    target_user = db.query(models.User).filter(models.User.User_name == asset.User_name).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {asset.User_name} not found",
        )

    # Create the asset
    db_asset = models.Asset(
        User_name=asset.User_name,
        Type=asset.Type,
        Valuation=asset.Valuation
    )
    
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    return db_asset


@router.get("/assets/{user_name}", response_model=List[schemas.AssetResponse])
async def get_user_assets(
    user_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get all assets for a specific user by their username.
    Only panchayat employees can access this endpoint.
    """
    # Verify that the current user is a panchayat employee
    if not verify_panchayat_employee(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can view user assets",
        )
    
    # Check if the target user exists
    target_user = db.query(models.User).filter(models.User.User_name == user_name).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_name} not found",
        )
    
    assets = db.query(models.Asset).filter(models.Asset.User_name == user_name).all()
    
    return assets



@router.put("/assets/{asset_id}", response_model=schemas.AssetResponse)
async def update_asset(
    asset_id: int,
    asset_update: schemas.AssetBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update a specific asset by ID.
    Only panchayat employees can update assets.
    """
    # Verify that the current user is a panchayat employee
    if not verify_panchayat_employee(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can update assets",
        )
    
    asset = db.query(models.Asset).filter(models.Asset.Asset_id == asset_id).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {asset_id} not found",
        )
    
    # Update asset fields
    asset.Type = asset_update.Type
    asset.Valuation = asset_update.Valuation
    
    db.commit()
    db.refresh(asset)
    
    return asset


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a specific asset by ID.
    Only panchayat employees can delete assets.
    """
    # Verify that the current user is a panchayat employee
    if not verify_panchayat_employee(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can delete assets",
        )
    
    asset = db.query(models.Asset).filter(models.Asset.Asset_id == asset_id).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {asset_id} not found",
        )
    
    db.delete(asset)
    db.commit()
    
    return {"detail": "Asset deleted successfully"}




@router.post("/family", response_model=schemas.FamCreateRespModel)
async def create_family(
    request: schemas.FamReq,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a family record with the specified user as the head.
    Only panchayat employees can access this endpoint.
    
    Request Parameters:
    - JWT token (for authentication)
    - user_name (username of the family head)
    
    Response:
    - Created family_id and head_citizen_id
    """
    # Verify that the current user is a panchayat employee
    if not verify_panchayat_employee(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can create family records"
        )
    
    # Find the citizen by the username
    head_citizen = db.query(models.Citizen).filter(
        models.Citizen.User_name == request.user_name
    ).first()
    
    if not head_citizen:
        # Return error when user is not found
        return schemas.FamCreateRespModel(
            data=None,
            message=f"User {request.user_name} not found or is not a citizen",
            statusCode=status.HTTP_404_NOT_FOUND
        )
    
    # Create a family entry where the head is also a member (self-referential)
    new_family = models.Family(
        Head_citizen_id=head_citizen.Citizen_id,
        Member_citizen_id=head_citizen.Citizen_id,
        Relationship="Self"  # Self-relationship for the head
    )
    
    db.add(new_family)
    db.commit()
    db.refresh(new_family)
    
    # Return the response with family_id and head_citizen_id
    return schemas.FamCreateRespModel(
        data=schemas.FamCreateResp(
            family_id=new_family.Family_id,
            head_citizen_id=head_citizen.Citizen_id
        ),
        message="Family created successfully",
        statusCode=status.HTTP_201_CREATED
    )


# GET endpoint to retrieve family details (returns detailed response with members)
@router.get("/family/{user_name}", response_model=schemas.FamRespModel)
async def get_family_details(
    user_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    # Verify that the current user is a panchayat employee
    if not verify_panchayat_employee(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can view family details"
        )
    
    # Find the citizen by the username
    head_citizen = db.query(models.Citizen).filter(
        models.Citizen.User_name == user_name
    ).first()
    
    if not head_citizen:
        # Return empty response with appropriate message when user is not found
        return schemas.FamRespModel(
            data=[],
            message=f"User {user_name} not found or is not a citizen",
            statusCode=status.HTTP_404_NOT_FOUND
        )
    
    # Get all families where this citizen is the head
    families = db.query(models.Family).filter(
        models.Family.Head_citizen_id == head_citizen.Citizen_id
    ).all()
    
    if not families:
        # Return empty response with appropriate message when no families are found
        return schemas.FamRespModel(
            data=[],
            message=f"No family found where {user_name} is the head",
            statusCode=status.HTTP_200_OK
        )
    
    # Group families by family_id to organize members
    family_groups = defaultdict(list)
    
    for family in families:
        family_groups[family.Family_id].append({
            "member_citizen_id": family.Member_citizen_id,
            "head_citizen_id": family.Head_citizen_id,
            "relationship": family.Relationship
        })
    
    # Format the response
    result = []
    
    for family_id, members in family_groups.items():
        # Get citizen details for each member
        member_details = []
        
        for member in members:
            # Get the User_name for each member
            member_citizen = db.query(models.Citizen).filter(
                models.Citizen.Citizen_id == member["member_citizen_id"]
            ).first()
            
            if member_citizen:
                member_details.append(schemas.FamMemberResp(
                    member_citizen_id=member["member_citizen_id"],
                    member_user_name=member_citizen.User_name
                ))
        
        result.append(schemas.FamRespWithMembers(
            family_id=family_id,
            head_citizen_id=head_citizen.Citizen_id,
            members=member_details
        ))
    
    # Return the properly formatted response using the Pydantic model
    return schemas.FamRespModel(
        data=result,
        message="Family details retrieved successfully",
        statusCode=status.HTTP_200_OK
    )

@router.post("/family/member", response_model=schemas.FamMemberRespModel)
async def add_family_member(
    request: schemas.FamMemberReq,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get current user info for logging
    user_login = current_user.User_name if current_user else "Unknown"
    # current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # print(f"Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {current_time}")
    print(f"Current User's Login: {user_login}")
    
    # Verify that the current user is a panchayat employee
    panchayat_role = verify_panchayat_employee(current_user, db)
    if not panchayat_role:
        print(f"User {user_login} attempted to add family member but is not a panchayat employee")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can add family members"
        )
    
    # Check if the family exists by querying any member of that family
    family = db.query(models.Family).filter(
        models.Family.Family_id == request.family_id
    ).first()
    
    if not family:
        print(f"Family ID {request.family_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family with ID {request.family_id} not found"
        )
    
    # Find the family head
    head_citizen_id = family.Head_citizen_id
    
    # Find the citizen to add as family member
    member_citizen = db.query(models.Citizen).filter(
        models.Citizen.User_name == request.member_user_name
    ).first()
    
    if not member_citizen:
        print(f"Member user {request.member_user_name} not found or is not a citizen")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.member_user_name} not found or is not a citizen"
        )
    
    # Check if the member is already part of this family
    existing_member = db.query(models.Family).filter(
        models.Family.Family_id == request.family_id,
        models.Family.Member_citizen_id == member_citizen.Citizen_id
    ).first()
    
    if existing_member:
        print(f"User {request.member_user_name} is already a member of family {request.family_id}")
        return schemas.FamMemberRespModel(
            data=schemas.FamMemberData(
                member_citizen_id=member_citizen.Citizen_id,
                member_user_name=member_citizen.User_name
            ),
            message=f"User {request.member_user_name} is already a member of this family",
            statusCode=status.HTTP_200_OK
        )
    
    try:
        # Create a new family entry for the member WITHOUT specifying Family_id
        # Let SQLAlchemy/database handle the Family_id assignment
        new_family_member = models.Family(
            Family_id=request.family_id,
            Head_citizen_id=head_citizen_id,
            Member_citizen_id=member_citizen.Citizen_id,
            Relationship="Member"
        )
        
        # Execute raw SQL to avoid the unique constraint issue
        # This is needed if Family_id, Member_citizen_id forms a composite key
        stmt = text("""
            INSERT INTO "Family" ("Family_id", "Head_citizen_id", "Member_citizen_id", "Relationship") 
            VALUES (:family_id, :head_id, :member_id, :relationship)
        """)
        
        db.execute(stmt, {
            'family_id': request.family_id,
            'head_id': head_citizen_id,
            'member_id': member_citizen.Citizen_id,
            'relationship': "Member"
        })
        
        db.commit()
        
        print(f"User {user_login} added {request.member_user_name} to family {request.family_id}")
        
        return schemas.FamMemberRespModel(
            data=schemas.FamMemberData(
                member_citizen_id=member_citizen.Citizen_id,
                member_user_name=member_citizen.User_name
            ),
            message=f"Member {request.member_user_name} added to family successfully",
            statusCode=status.HTTP_201_CREATED
        )
    except Exception as e:
        db.rollback()
        print(f"Error adding family member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add family member: {str(e)}"
        )
        
@router.delete("/family/member", status_code=status.HTTP_204_NO_CONTENT)
async def remove_family_member(
    request: schemas.FamMemberReq,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Remove a member from a family.
    Only panchayat employees with role 'family_manager' can remove family members.
    
    Request Parameters:
    - JWT token (for authentication)
    - family_id: ID of the family to remove member from
    - member_user_name: Username of the citizen to remove from family
    
    Response:
    - 204 No Content on success
    """
    # Get current user info for logging
    user_login = current_user.User_name if current_user else "Unknown"
    # current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")/
    
    # print(f"[{current_time}] User {user_login} attempting to remove family member")
    
    # Verify that the current user is a panchayat employee
    panchayat_role = verify_panchayat_employee(current_user, db)
    if not panchayat_role:
        # print(f"[{current_time}] User {user_login} is not a panchayat employee")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can remove family members"
        )
        
    # Check if the employee has the correct role
    # if panchayat_role.Role != "family_manager":
    #     print(f"[{current_time}] User {user_login} doesn't have the family_manager role")
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only family managers can remove family members",
    #     )
    
    # Check if the family exists
    family = db.query(models.Family).filter(
        models.Family.Family_id == request.family_id
    ).first()
    
    if not family:
        # print(f"[{current_time}] Family ID {request.family_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family with ID {request.family_id} not found"
        )
    
    # Find the citizen to remove
    member_citizen = db.query(models.Citizen).filter(
        models.Citizen.User_name == request.member_user_name
    ).first()
    
    if not member_citizen:
        # print(f"[{current_time}] User {request.member_user_name} not found or is not a citizen")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.member_user_name} not found or is not a citizen"
        )
    
    # Find the family member relationship to delete
    family_member = db.query(models.Family).filter(
        models.Family.Family_id == request.family_id,
        models.Family.Member_citizen_id == member_citizen.Citizen_id
    ).first()
    
    if not family_member:
        # print(f"[{current_time}] User {request.member_user_name} is not a member of family {request.family_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.member_user_name} is not a member of this family"
        )
    
    # Don't allow removal of family head (head is likely also a member)
    if member_citizen.Citizen_id == family.Head_citizen_id:
        # print(f"[{current_time}] Cannot remove family head from family")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the family head from the family. Delete the family instead."
        )
    
    try:
        # Delete the family member relationship
        db.delete(family_member)
        db.commit()
        
        # print(f"[{current_time}] User {user_login} removed {request.member_user_name} from family {request.family_id}")
        
        # Return 204 No Content (handled by FastAPI based on the status_code in the decorator)
        return None
        
    except Exception as e:
        db.rollback()
        # print(f"[{current_time}] Error removing family member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove family member: {str(e)}"
        )
        
@router.delete("/family/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
  
    # Format current time for logging
    # current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # Get user login for logging
    # user_login = current_user.User_name if current_user else "Unknown"
    
    # print(f"[{current_time}] User {user_login} attempting to delete family {family_id}")
    
    # Verify that the current user is a panchayat employee
    panchayat_role = verify_panchayat_employee(current_user, db)
    if not panchayat_role:
        # print(f"[{current_time}] User {user_login} is not a panchayat employee")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can delete families"
        )
        
    # Check if the employee has the correct role
    # if panchayat_role.Role != "family_manager":
    #     # print(f"[{current_time}] User {user_login} doesn't have the family_manager role")
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only family managers can delete families",
    #     )
    
    # Check if the family exists
    family_members = db.query(models.Family).filter(
        models.Family.Family_id == family_id
    ).all()
    
    if not family_members:
        # print(f"[{current_time}] Family ID {family_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family with ID {family_id} not found"
        )
    
    try:
        # Get head information for logging purpose
        head_citizen_id = family_members[0].Head_citizen_id
        head_citizen = db.query(models.Citizen).filter(
            models.Citizen.Citizen_id == head_citizen_id
        ).first()
        
        head_username = head_citizen.User_name if head_citizen else "Unknown"
        
        # Delete all family members (this will delete the entire family)
        for member in family_members:
            db.delete(member)
        
        db.commit()
        
        # print(f"[{current_time}] User {user_login} deleted family {family_id} with head {head_username}")
        
        # Return 204 No Content (handled by FastAPI based on the status_code in the decorator)
        return None
        
    except Exception as e:
        db.rollback()
        # print(f"[{current_time}] Error deleting family: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete family: {str(e)}"
        )
        

@router.get("/issues", response_model=schemas.IssuesListResponse)
async def get_all_issues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify if the current user is a panchayat employee
    if not current_user.User_type == "PANCHAYAT_EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can access this endpoint"
        )

    # Query to get all issues with citizen and user information
    query = (
        select(Issue, Citizen.User_name)
        .join(Citizen, Issue.Citizen_id == Citizen.Citizen_id)
    )
    
    result = db.execute(query).all()
    
    # Format the response
    issues_list = [
        IssueResponse(
            issue_id=issue.Issue_id,
            description=issue.description,
            status=issue.status,
            citizen_id=issue.Citizen_id,
            user_name=user_name,
            created_at=issue.created_at,
            updated_at=issue.updated_at
        )
        for issue, user_name in result
    ]

    return IssuesListResponse(
        data=issues_list,
        message="Issues retrieved successfully",
        statusCode=status.HTTP_200_OK
    )
    

@router.put("/issues", response_model=UpdateIssueResponse)
async def update_issue_status(
    request: UpdateIssueRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify if the current user is a panchayat employee
    if not current_user.User_type == "PANCHAYAT_EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only panchayat employees can update issue status"
        )

    try:
        # Find the issue
        issue = db.query(Issue).filter(Issue.Issue_id == request.issue_id).first()
        
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {request.issue_id} not found"
            )

        # Update the issue status
        issue.status = request.status
        issue.updated_at = datetime.utcnow()

        db.commit()

        return UpdateIssueResponse(
            message=f"Issue status successfully updated to {request.status}",
            statusCode=status.HTTP_200_OK
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the issue status"
        )
        
@router.get("/documents/{user_name}", response_model=DocumentsListResponse)
async def get_documents(
    user_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # First verify if the requesting user has permission to access these documents
    # Only allow if it's the user's own documents or if the requester is an admin/panchayat employee
    if (current_user.User_name != user_name and 
        current_user.User_type not in ['ADMIN', 'PANCHAYAT_EMPLOYEE']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access these documents"
        )

    try:
        # Get the citizen ID for the requested user_name
        citizen = db.query(Citizen).join(User).filter(User.User_name == user_name).first()
        
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No citizen found for user {user_name}"
            )

        # Query to get all documents for the citizen
        documents = (
            db.query(Document)
            .filter(Document.Citizen_id == citizen.Citizen_id)
            .all()
        )

        # Format the response
        documents_list = [
            DocumentResponse(
                Doc_id=doc.Document_id,
                Type=doc.Type,
                Pdf_data=b64encode(doc.Pdf_data).decode('utf-8'),  # Convert BYTEA to base64
                Citizen_id=doc.Citizen_id,
                user_name=user_name
            )
            for doc in documents
        ]

        return DocumentsListResponse(
            data=documents_list,
            message="Documents retrieved successfully",
            statusCode=status.HTTP_200_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving documents: {str(e)}"
        )
        

@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    request: DocumentUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify if the current user has permission to upload documents
    if (current_user.User_name != request.user_name and 
        current_user.User_type not in [ 'PANCHAYAT_EMPLOYEE']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload documents for this user"
        )

    try:
        # Get the citizen ID for the user_name
        citizen = db.query(Citizen).join(User).filter(User.User_name == request.user_name).first()
        
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No citizen found for user {request.user_name}"
            )

        try:
            # Decode the base64 PDF data
            pdf_data =  b64decode(request.Pdf_data)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF data format. Please provide base64 encoded PDF data"
            )

        # Create new document
        new_document = Document(
            Citizen_id=citizen.Citizen_id,
            Type=request.Type,
            Pdf_data=pdf_data
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        return DocumentUploadResponse(
            data=[
                DocumentCreatedResponse(
                    Doc_id=new_document.Document_id,
                    Citizen_id=new_document.Citizen_id
                )
            ],
            message="Document uploaded successfully",
            statusCode=status.HTTP_201_CREATED
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading the document: {str(e)}"
        )
        

@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get the document
        document = db.query(Document).filter(Document.Document_id == doc_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {doc_id} not found"
            )

        # Get the citizen who owns this document
        citizen = db.query(Citizen).filter(Citizen.Citizen_id == document.Citizen_id).first()
        
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated citizen not found"
            )

        # Get the user associated with this citizen
        user = db.query(User).filter(User.User_name == citizen.User_name).first()

        # Check permissions
        # Allow deletion if:
        # 1. The user is deleting their own document
        # 2. The user is an Admin
        # 3. The user is a PanchayatEmployee
        if (current_user.User_name != user.User_name and 
            current_user.User_type not in ['ADMIN', 'PANCHAYAT_EMPLOYEE']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this document"
            )

        # Delete the document
        db.delete(document)
        db.commit()

        return DocumentDeleteResponse(
            message=f"Document with ID {doc_id} deleted successfully",
            statusCode=status.HTTP_200_OK
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the document: {str(e)}"
        )
        

############################################################################################

@router.post("/financial_data", response_model=FinancialCreateResponse)
async def create_financial_data(
    request: FinancialDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get current UTC timestamp
    current_time = datetime.utcnow()
    
    # Verify if the current user has permission
    if (current_user.User_name != request.user_name and 
        current_user.User_type not in ['PANCHAYAT_EMPLOYEE']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add financial data for this user"
        )

    try:
        # Get the citizen ID for the user_name
        citizen = db.query(Citizen).join(User).filter(User.User_name == request.user_name).first()
        
        if not citizen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No citizen found for user {request.user_name}"
            )

        # Check if financial data for this year already exists
        existing_data = db.query(FinancialData).filter(
            FinancialData.Citizen_id == citizen.Citizen_id,
            FinancialData.year == request.year
        ).first()

        if existing_data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Financial data for year {request.year} already exists for this user"
            )

        # Create new financial data entry
        new_financial_data = FinancialData(
            Citizen_id=citizen.Citizen_id,
            year=request.year,
            Annual_Income=request.Annual_Income,
            Income_source=request.Income_source,
            Tax_paid=request.Tax_paid,
            Tax_liability=request.Tax_liability,
            Debt_liability=request.Debt_liability,
            Credit_score=request.Credit_score,
            Last_updated=current_time
        )

        db.add(new_financial_data)
        db.commit()
        db.refresh(new_financial_data)

        return FinancialCreateResponse(
            data=[
                FinancialDataResponse(
                    Financial_id=new_financial_data.Financial_id,
                    Last_updated=new_financial_data.Last_updated,
                    Citizen_fk=new_financial_data.Citizen_id
                )
            ],
            message="Financial data added successfully",
            statusCode=status.HTTP_201_CREATED
        )

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding financial data: {str(e)}"
        )