from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)



conf = ConnectionConfig(
    MAIL_USERNAME="sagnibharoy@kgpian.iitkgp.ac.in",  
    MAIL_PASSWORD="wfiy vwwe mqiz eqjo",               
    MAIL_FROM="sagnibharoy@kgpian.iitkgp.ac.in",     
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Admin",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)



@router.get('/users', status_code=status.HTTP_200_OK)
def get_users_not_verified(db: Session = Depends(get_db)):
    unverified_users = db.query(models.User).filter(models.User.is_verified == 0).all()
    if not unverified_users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unverified users found")
    return unverified_users


async def send_verification_email(email: EmailStr, name: str):
    fm = FastMail(conf)
    
    html = f"""
        <h3>Hi {name},</h3>
        <p>Your account has been successfully verified. You can now log in and access all features.</p>
        <p>Thank you for joining us!</p>
        <p>Best regards,<br>Admin Team</p>
    """
    
    message = MessageSchema(
        subject="Account Verified",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    try:
        await fm.send_message(message)
        print(f"Email sent successfully to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email to {email}")
    
    
    
    
    
@router.put('/verify/{user_name}', status_code=status.HTTP_200_OK)
async def verify_user(user_name: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter(models.User.User_name == user_name).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_name}' not found")
    
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User '{user_name}' is already verified")
    

    user.is_verified = 1
    db.commit()
    
    
    background_tasks.add_task(send_verification_email, user.Email, user.Name)
    
    return {"message": f"User '{user_name}' has been verified successfully"}



@router.delete('/delete/{user_name}', status_code=status.HTTP_200_OK)
def delete_user(user_name: str, db: Session = Depends(get_db)):

    # Fetch the user by User_name
    user = db.query(models.User).filter(models.User.User_name == user_name).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_name}' not found")

    # Fetch and delete the related Citizen record if it exists
    citizen = db.query(models.Citizen).filter(models.Citizen.User_name == user_name).first()
    admin = db.query(models.Admin).filter(models.Admin.User_name == user_name).first()
    panchayat_employee = db.query(models.PanchayatEmployee).filter(models.PanchayatEmployee.User_name == user_name).first()
    governmentagency = db.query(models.GovernmentAgencies).filter(models.GovernmentAgencies.User_name == user_name).first()
    if citizen:
        db.delete(citizen)
    elif admin:
        db.delete(admin)
    elif panchayat_employee:
        db.delete(panchayat_employee)
    elif governmentagency:
        db.delete(governmentagency)
        
    

    # Delete the user record
    db.delete(user)
    db.commit()

    return {"message": f"User '{user_name}' and their corresponding citizen data have been deleted successfully"}

