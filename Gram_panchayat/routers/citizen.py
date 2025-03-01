from fastapi import APIRouter, Depends, status, Response, HTTPException, Body, Header
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from typing import List, Optional, Dict, Any
from ..database import get_db
from .. import jwt_handler, models, schemas
from pydantic import BaseModel
import logging
from datetime import date, datetime

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

def get_citizen_record(user: models.User, db: Session):
    """Helper function to get the citizen record for a user"""
    citizen = db.query(models.Citizen).filter(
        models.Citizen.User_name == user.User_name
    ).first()
    
    if not citizen:
        logger.error(f"No citizen record found for user: {user.User_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen record not found"
        )
    return citizen

def check_column_exists(table_name, column_name, db: Session):
    """Helper function to check if a column exists in a table"""
    inspector = inspect(db.bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

@router.get('/assets', response_model=schemas.AssetsResponse)
def get_citizen_assets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_assets called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    assets = db.query(models.Asset).filter(models.Asset.User_name == current_user.User_name).all()
    logger.info(f"Found {len(assets)} assets for user: {current_user.User_name}")
    
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

@router.get('/family', response_model=schemas.FamilyResponse)
def get_citizen_family(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_family called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        if check_column_exists('Family', 'Head_citizen_id', db) and check_column_exists('Family', 'Member_citizen_id', db):
            family_members_as_head = db.query(models.Family).filter(
                models.Family.Head_citizen_id == citizen.Citizen_id
            ).all()
            
            families_as_member = db.query(models.Family).filter(
                models.Family.Member_citizen_id == citizen.Citizen_id
            ).all()
            
            family_data_list = []
            for family in family_members_as_head:
                member_citizen = db.query(models.Citizen).filter(
                    models.Citizen.Citizen_id == family.Member_citizen_id
                ).first()
                if member_citizen:
                    family_data_list.append(schemas.FamilyMemberData(
                        User_name=member_citizen.User_name
                    ))
            
            for family in families_as_member:
                head_citizen = db.query(models.Citizen).filter(
                    models.Citizen.Citizen_id == family.Head_citizen_id
                ).first()
                if head_citizen:
                    family_data_list.append(schemas.FamilyMemberData(
                        User_name=head_citizen.User_name
                    ))
                    
        elif check_column_exists('Family', 'User_name', db) and check_column_exists('Family', 'Member_name', db):
            family_query = text("""
                SELECT 
                    f.Family_id, 
                    CASE 
                        WHEN f.User_name = :username THEN f.Member_name 
                        ELSE f.User_name 
                    END as family_member
                FROM Family f
                WHERE f.User_name = :username OR f.Member_name = :username
            """)
            
            result = db.execute(family_query, {"username": current_user.User_name})
            
            family_data_list = []
            for row in result:
                family_member_username = row.family_member
                if family_member_username != current_user.User_name:
                    family_data_list.append(schemas.FamilyMemberData(
                        User_name=family_member_username
                    ))
        else:
            logger.error("Unknown Family table schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema error"
            )
        
        unique_members = {member.User_name: member for member in family_data_list}
        
        if current_user.User_name in unique_members:
            unique_members.pop(current_user.User_name)
        
        unique_member_list = list(unique_members.values())
        
        return schemas.FamilyResponse(
            data=unique_member_list,
            message="Family members retrieved successfully",
            statusCode=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in get_citizen_family: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving family data: {str(e)}"
        )

@router.get('/issues', response_model=schemas.IssuesResponse)
def get_citizen_issues(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_issues called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('Issue')]
        logger.info(f"Issue table columns: {columns}")
        
        if 'Citizen_id' in columns:
            # New schema
            issues_query = text("""
                SELECT Issue_id, description, status, created_at, updated_at
                FROM Issue 
                WHERE Citizen_id = :citizen_id
            """)
            result = db.execute(issues_query, {"citizen_id": citizen.Citizen_id})
        elif 'User_name' in columns:
            # Old schema
            issues_query = text("""
                SELECT Issue_id, description, status, created_at, updated_at
                FROM Issue 
                WHERE User_name = :username
            """)
            result = db.execute(issues_query, {"username": current_user.User_name})
        else:
            logger.error("Unknown Issue table schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema error"
            )
        
        # Process results
        issues = result.all()
        logger.info(f"Found {len(issues)} issues for user: {current_user.User_name}")
        
        # Format the response
        issue_data_list = []
        for issue in issues:
            issue_data = {
                "Issue_id": issue.Issue_id,
                "description": issue.description,
                "status": issue.status, 
                "created_at": issue.created_at,
                "updated_at": issue.updated_at,
            }
            issue_data_list.append(schemas.IssueData(**issue_data))
        
        return schemas.IssuesResponse(
            data=issue_data_list,
            message="Issues retrieved successfully",
            statusCode=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in get_citizen_issues: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving issues: {str(e)}"
        )

@router.post('/issues', response_model=schemas.IssueCreateResponse, status_code=status.HTTP_201_CREATED)
def create_citizen_issue(
    issue_data: schemas.IssueCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"create_citizen_issue called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('Issue')]
        logger.info(f"Issue table columns: {columns}")
        
        if 'Citizen_id' in columns:
            # New schema
            insert_query = text("""
                INSERT INTO Issue (Citizen_id, description, status, created_at, updated_at)
                VALUES (:citizen_id, :description, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING Issue_id
            """)
            result = db.execute(
                insert_query,
                {
                    "citizen_id": citizen.Citizen_id,
                    "description": issue_data.description,
                    "status": "PENDING"
                }
            )
        elif 'User_name' in columns:
            # Old schema
            insert_query = text("""
                INSERT INTO Issue (User_name, description, status, created_at, updated_at)
                VALUES (:username, :description, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING Issue_id
            """)
            result = db.execute(
                insert_query,
                {
                    "username": current_user.User_name,
                    "description": issue_data.description,
                    "status": "PENDING"
                }
            )
        else:
            logger.error("Unknown Issue table schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema error"
            )
        
        # Get the created issue ID
        new_issue_id = result.scalar()
        db.commit()
        
        logger.info(f"Created issue with ID: {new_issue_id}")
        
        return schemas.IssueCreateResponse(
            Issue_id=new_issue_id,
            message="Issue created successfully",
            statusCode=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error in create_citizen_issue: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating issue: {str(e)}"
        )
        
@router.delete('/issue', status_code=status.HTTP_200_OK)
def delete_citizen_issue(
    Issue_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"delete_citizen_issue called for issue ID: {Issue_id} by user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        issue_query = text("SELECT Issue_id, description, status FROM Issue WHERE Issue_id = :issue_id")
        issue = db.execute(issue_query, {"issue_id": Issue_id}).first()
        
        if not issue:
            logger.error(f"Issue with ID {Issue_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {Issue_id} not found"
            )
        
        # Check if issue belongs to the current citizen
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('Issue')]
        
        belongs_to_user = False
        if 'Citizen_id' in columns:
            # New schema
            owner_query = text("SELECT Citizen_id FROM Issue WHERE Issue_id = :issue_id")
            result = db.execute(owner_query, {"issue_id": Issue_id}).first()
            belongs_to_user = result.Citizen_id == citizen.Citizen_id
        elif 'User_name' in columns:
            # Old schema
            owner_query = text("SELECT User_name FROM Issue WHERE Issue_id = :issue_id")
            result = db.execute(owner_query, {"issue_id": Issue_id}).first()
            belongs_to_user = result.User_name == current_user.User_name
        
        if not belongs_to_user:
            logger.error(f"Issue {Issue_id} does not belong to user {current_user.User_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own issues"
            )
        
        # Check if issue is in 'OPEN' status
        if issue.status != 'PENDING':
            logger.error(f"Issue {Issue_id} is not in 'OPEN' status, current status: {issue.status}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete issues with 'OPEN' status"
            )
        
        # Delete the issue
        delete_query = text("DELETE FROM Issue WHERE Issue_id = :issue_id")
        db.execute(delete_query, {"issue_id": Issue_id})
        db.commit()
        
        logger.info(f"Issue {Issue_id} deleted successfully")
        
        return {
            "message": "Issue deleted successfully",
            "statusCode": status.HTTP_200_OK
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in delete_citizen_issue: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting issue: {str(e)}"
        )

@router.get('/document', response_model=schemas.DocumentResponse)
def get_citizen_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_documents called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        # Use raw SQL to be safe
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('Document')]
        
        if 'Citizen_id' in columns:
            # New schema
            documents_query = text("""
                SELECT Document_id, Type, Pdf_data 
                FROM Document 
                WHERE Citizen_id = :citizen_id
            """)
            result = db.execute(documents_query, {"citizen_id": citizen.Citizen_id})
        elif 'User_name' in columns:
            # Old schema
            documents_query = text("""
                SELECT Document_id, Type, Pdf_data 
                FROM Document 
                WHERE User_name = :username
            """)
            result = db.execute(documents_query, {"username": current_user.User_name})
        else:
            logger.error("Unknown Document table schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema error"
            )
        
        # Process results
        documents = result.all()
        logger.info(f"Found {len(documents)} documents for user: {current_user.User_name}")
        
        # Format the response
        document_data_list = []
        for document in documents:
            document_data = {
                "Type": document.Type,
                "Pdf_data": document.Pdf_data
            }
            document_data_list.append(schemas.DocumentData(**document_data))
        
        return schemas.DocumentResponse(
            data=document_data_list,
            message="Documents retrieved successfully",
            statusCode=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error in get_citizen_documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )

@router.get('/financial-data', response_model=schemas.FinancialDataResponse)
def get_citizen_financial_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_financial_data called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        # Use raw SQL to be safe
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('Financial_data')]
        
        if 'Citizen_id' in columns:
            # New schema
            financial_query = text("""
                SELECT year, Annual_Income, Income_source, Tax_paid, 
                       Tax_liability, Debt_liability, Credit_score, Last_updated 
                FROM Financial_data 
                WHERE Citizen_id = :citizen_id
            """)
            result = db.execute(financial_query, {"citizen_id": citizen.Citizen_id})
        elif 'User_name' in columns:
            # Old schema
            financial_query = text("""
                SELECT year, Annual_Income, Income_source, Tax_paid, 
                       Tax_liability, Debt_liability, Credit_score, Last_updated 
                FROM Financial_data 
                WHERE User_name = :username
            """)
            result = db.execute(financial_query, {"username": current_user.User_name})
        else:
            logger.error("Unknown Financial_data table schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema error"
            )
        
        # Process results
        financial_data = result.all()
        logger.info(f"Found {len(financial_data)} financial records for user: {current_user.User_name}")
        
        # Format the response
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
    except Exception as e:
        logger.error(f"Error in get_citizen_financial_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving financial data: {str(e)}"
        )
        
@router.get('/welfare-scheme', response_model=schemas.WelfareSchemeResponse)
def get_citizen_welfare_schemes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_citizen_welfare_schemes called for user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        schemes_query = text("""
            SELECT Scheme_id, Scheme_name, Description, Application_deadline
            FROM Welfare_scheme
        """)
        welfare_schemes = db.execute(schemes_query).all()
        
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('Welfare_enrol')]
        
        # Get all enrolled schemes for the current citizen
        if 'Citizen_id' in columns:
            # New schema
            enrollments_query = text("""
                SELECT Scheme_fk, status
                FROM Welfare_enrol
                WHERE Citizen_id = :citizen_id
            """)
            enrolled_schemes = db.execute(enrollments_query, {"citizen_id": citizen.Citizen_id}).all()
        elif 'User_name' in columns:
            # Old schema
            enrollments_query = text("""
                SELECT Scheme_fk, status
                FROM Welfare_enrol
                WHERE User_name = :username
            """)
            enrolled_schemes = db.execute(enrollments_query, {"username": current_user.User_name}).all()
        else:
            logger.error("Unknown Welfare_enrol table schema")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema error"
            )
        
        # Create a dictionary of enrolled schemes with their status
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
    except Exception as e:
        logger.error(f"Error in get_citizen_welfare_schemes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving welfare schemes: {str(e)}"
        )
        

@router.post('/welfare-enrol', response_model=schemas.WelfareEnrolResponse)
def enrol_in_welfare_scheme(
    Scheme_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"enrol_in_welfare_scheme called for scheme ID: {Scheme_id} by user: {current_user.User_name}")
    
    is_citizen(current_user)
    citizen = get_citizen_record(current_user, db)
    
    try:
        # Check if scheme exists
        scheme_query = text("""
            SELECT Scheme_id, Scheme_name, Description, Application_deadline
            FROM Welfare_scheme
            WHERE Scheme_id = :scheme_id
        """)
        scheme = db.execute(scheme_query, {"scheme_id": Scheme_id}).first()
        
        if not scheme:
            logger.error(f"Welfare scheme with ID {Scheme_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Welfare scheme with ID {Scheme_id} not found"
            )
        
        # Check if application deadline has passed
        if scheme.Application_deadline and scheme.Application_deadline < (date.today()):
            logger.error(f"Application deadline for scheme {Scheme_id} has passed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Application deadline for this scheme has passed"
            )
        
        # Check if already enrolled - using raw SQL to handle schema differences
        existing_enrol_query = text("""
            SELECT Enrol_id, status 
            FROM Welfare_enrol 
            WHERE User_name = :username AND Scheme_fk = :scheme_id
        """)
        
        existing_enrolment = db.execute(
            existing_enrol_query, 
            {"username": current_user.User_name, "scheme_id": Scheme_id}
        ).first()
        
        if existing_enrolment:
            logger.error(f"User {current_user.User_name} already enrolled in scheme {Scheme_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already enrolled in this scheme"
            )
        
        # Create new enrollment using raw SQL
        insert_query = text("""
            INSERT INTO Welfare_enrol (User_name, Scheme_fk, status)
            VALUES (:username, :scheme_id, :status)
            RETURNING Enrol_id, status
        """)
        
        new_enrolment = db.execute(
            insert_query,
            {
                "username": current_user.User_name,
                "scheme_id": Scheme_id,
                "status": "PENDING"
            }
        ).first()
        
        db.commit()
        
        logger.info(f"User {current_user.User_name} successfully enrolled in scheme {Scheme_id}")
        
        return schemas.WelfareEnrolResponse(
            data="PENDING",
            message="Successfully applied for welfare scheme",
            statusCode=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enrol_in_welfare_scheme: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enrolling in welfare scheme: {str(e)}"
        )

@router.get('/infrastructure', response_model=schemas.InfrastructureResponse)
def get_infrastructure_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_infrastructure_projects called by user: {current_user.User_name}")
    
    is_citizen(current_user)
    
    citizen = get_citizen_record(current_user, db)
    
    try:
        infra_query = text("""
            SELECT Description, Location, Funding, Actual_cost
            FROM Infrastructure
        """)
        
        infrastructure_projects = db.execute(infra_query).all()
        
        logger.info(f"Found {len(infrastructure_projects)} infrastructure projects")
        
        # Format the response
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
        
    except Exception as e:
        logger.error(f"Error in get_infrastructure_projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving infrastructure projects: {str(e)}"
        )