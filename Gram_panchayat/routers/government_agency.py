from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from .. import models, schemas, jwt_handler
from ..database import get_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/government-agency",
    tags=['Government Agency']
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
            if scheme.lower() == "bearer":
                jwt_token = token
        except Exception as e:
            logger.error(f"Failed to process authorization header: {str(e)}")
    
    if not jwt_token and JWT:
        jwt_token = JWT
        
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
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.User_name == token_data.User_name).first()
    if user is None:
        logger.error(f"No user found for username: {token_data.User_name}")
        raise credentials_exception
    return user

def is_government_agency(user: models.User):
    if user.User_type != "GOVERNMENT_AGENCY":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only government agencies can access this resource"
        )
    return user

@router.get('/welfare-scheme', response_model=schemas.WelfareSchemeListResponse)
def get_agency_welfare_schemes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"get_agency_welfare_schemes called for user: {current_user.User_name}")
    
    is_government_agency(current_user)
    
    try:
        agency_query = text("""
            SELECT Agency_id 
            FROM Government_agencies 
            WHERE User_name = :username
        """)
        agency = db.execute(agency_query, {"username": current_user.User_name}).first()
        
        if not agency:
            logger.error(f"No government agency record found for user: {current_user.User_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Government agency record not found"
            )
        
        schemes_query = text("""
            SELECT 
                Scheme_id,
                Scheme_name,
                Description,
                Application_deadline
            FROM Welfare_scheme
            WHERE Agency_id = :agency_id
            ORDER BY Application_deadline DESC
        """)
        
        schemes = db.execute(schemes_query, {"agency_id": agency.Agency_id}).all()
        logger.info(f"Found {len(schemes)} welfare schemes for agency: {current_user.User_name}")
        
        schemes_data = [
            schemas.WelfareSchemeAgencyData(
                Scheme_id=scheme.Scheme_id,
                Scheme_name=scheme.Scheme_name,
                Description=scheme.Description,
                Application_deadline=scheme.Application_deadline
            )
            for scheme in schemes
        ]
        
        return schemas.WelfareSchemeListResponse(
            data=schemes_data,
            message="Welfare schemes retrieved successfully",
            statusCode=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_agency_welfare_schemes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving welfare schemes: {str(e)}"
        )
        
@router.post('/welfare-scheme', response_model=schemas.WelfareSchemeCreateResponse)
def create_welfare_scheme(
    scheme_data: schemas.WelfareSchemeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"create_welfare_scheme called for user: {current_user.User_name}")
    
    # Verify user is a government agency
    is_government_agency(current_user)
    
    try:
        # Get the government agency ID
        agency_query = text("""
            SELECT Agency_id 
            FROM Government_agencies 
            WHERE User_name = :username
        """)
        agency = db.execute(agency_query, {"username": current_user.User_name}).first()
        
        if not agency:
            logger.error(f"No government agency record found for user: {current_user.User_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Government agency record not found"
            )
        
        # Insert new welfare scheme
        insert_query = text("""
            INSERT INTO Welfare_scheme (
                Agency_id,
                Scheme_name,
                Description,
                Application_deadline
            )
            VALUES (
                :agency_id,
                :scheme_name,
                :description,
                :application_deadline
            )
            RETURNING Scheme_id
        """)
        
        result = db.execute(
            insert_query,
            {
                "agency_id": agency.Agency_id,
                "scheme_name": scheme_data.Scheme_name,
                "description": scheme_data.Description,
                "application_deadline": scheme_data.Application_deadline
            }
        ).first()
        
        db.commit()
        
        scheme_id = result.Scheme_id
        logger.info(f"Created welfare scheme with ID: {scheme_id}")
        
        return schemas.WelfareSchemeCreateResponse(
            Scheme_id=scheme_id,
            message="Welfare scheme created successfully",
            statusCode=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_welfare_scheme: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating welfare scheme: {str(e)}"
        )
        
@router.delete('/welfare-scheme/{scheme_id}', response_model=schemas.ResponseModel)
def delete_welfare_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"delete_welfare_scheme called for scheme ID: {scheme_id} by user: {current_user.User_name}")
    
    is_government_agency(current_user)
    
    try:
        verification_query = text("""
            SELECT ws.Scheme_id 
            FROM Welfare_scheme ws
            JOIN Government_agencies ga ON ws.Agency_id = ga.Agency_id
            WHERE ws.Scheme_id = :scheme_id 
            AND ga.User_name = :username
        """)
        
        scheme = db.execute(
            verification_query, 
            {
                "scheme_id": scheme_id,
                "username": current_user.User_name
            }
        ).first()
        
        if not scheme:
            logger.error(f"Scheme {scheme_id} not found or does not belong to agency: {current_user.User_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found or you don't have permission to delete it"
            )
        
        enrollment_check_query = text("""
            SELECT COUNT(*) as enroll_count
            FROM Welfare_enrol
            WHERE Scheme_fk = :scheme_id
        """)
        
        enrollment_count = db.execute(
            enrollment_check_query,
            {"scheme_id": scheme_id}
        ).scalar()
        
        if enrollment_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete scheme with existing enrollments"
            )
        
        delete_query = text("""
            DELETE FROM Welfare_scheme
            WHERE Scheme_id = :scheme_id
            AND Agency_id IN (
                SELECT Agency_id 
                FROM Government_agencies 
                WHERE User_name = :username
            )
        """)
        
        result = db.execute(
            delete_query,
            {
                "scheme_id": scheme_id,
                "username": current_user.User_name
            }
        )
        
        if result.rowcount == 0:
            logger.error(f"Failed to delete scheme {scheme_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete scheme"
            )
            
        db.commit()
        logger.info(f"Successfully deleted scheme {scheme_id}")
        
        return schemas.ResponseModel(
            message="Welfare scheme deleted successfully",
            statusCode=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_welfare_scheme: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting welfare scheme: {str(e)}"
        )
        
        