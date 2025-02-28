from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
from models import (
    User, Citizen, GovernmentAgency, Admin, PanchayatEmployee,
    Census, AgriculturalLand, FinancialData, Family, WelfareSchemes,
    Infrastructure, ActivityLog, Issues, Documents, Assets, WelfareEnrol
)
from models import (
    user_pydantic, user_pydantic_in, citizen_pydantic, citizen_pydantic_in,
    government_agency_pydantic, government_agency_pydantic_in, admin_pydantic, admin_pydantic_in,
    panchayat_employee_pydantic, panchayat_employee_pydantic_in, issues_pydantic, issues_pydantic_in,
    welfare_schemes_pydantic, welfare_schemes_pydantic_in, welfare_enrol_pydantic, welfare_enrol_pydantic_in
)
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Panchayat Management System API", 
              description="API for managing panchayat data and services",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SystemInfo(BaseModel):
    current_time: str
    current_user: str
    system_status: str

class LoginRequest(BaseModel):
    username: str
    password: str

class IssueCreate(BaseModel):
    description: str
    citizen_fk: int

class StatusUpdate(BaseModel):
    status: str

# Authentication middleware (simplified for demo purposes)
async def get_current_user(username: Optional[str] = Header(None)):
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await User.get_or_none(User_name=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.get('/')
def index():
    return {
        'Msg': "Welcome to Panchayat Management System API",
        'Version': "1.0.0",
        'Documentation': "/docs"
    }



@app.post('/auth/login')
async def login(login_data: LoginRequest):
    user = await User.get_or_none(User_name=login_data.username)
    if not user or hash_password(login_data.password) != user.Password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    await ActivityLog.create(
        Time=datetime.utcnow(),
        Affected_user_fk_id=user.User_name,  
        From_value="Login",
        New_val="Successful login",
        User_name_fk_id=user.User_name  
    )
    
    return {"status": "ok", "message": f"Welcome {user.Name}", "user_type": user.User_type}

@app.post('/user/register')
async def register(user_info: user_pydantic_in):
    existing_user = await User.get_or_none(User_name=user_info.User_name)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with username {user_info.User_name} already exists"
        )
        
    user_dict = user_info.dict(exclude_unset=True)
    user_dict["Password"] = hash_password(user_dict["Password"])
    
    user_obj = await User.create(**user_dict)
    
    user_type = user_dict.get("User_type", "").lower()
    
    if user_type == "citizen":
        await Citizen.create(User_name_id=user_obj.User_name)
        
    elif user_type == "panchayat_employee":
        citizen = await Citizen.create(User_name_id=user_obj.User_name)
        await PanchayatEmployee.create(
            User_name_id=user_obj.User_name,
            Citizen_fk_id=citizen.Citizen_Id,
            Role="General Staff"  
        )
        
    elif user_type == "government_agency":
        await GovernmentAgency.create(
            User_name_id=user_obj.User_name,
            Role="General Agency"  
        )
        
    elif user_type == "admin":
        await Admin.create(User_name_id=user_obj.User_name)
    else:
        await user_obj.delete()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user type: {user_type}. Must be one of: citizen, panchayat_employee, government_agency, admin"
        )
    
    await ActivityLog.create(
        Time=datetime.utcnow(),
        Affected_user_fk_id=user_obj.User_name,  
        From_value="Registration",
        New_val=f"Created new {user_type} user",
        User_name_fk_id=user_obj.User_name  
    )
    
    response = await user_pydantic.from_tortoise_orm(user_obj)
    return {"status": "ok", "data": response, "message": f"User registered as {user_type}"}

@app.get('/user/{user_name}')
async def get_user(user_name: str):
    user = await User.get_or_none(User_name=user_name)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_name} not found")
    
    response = await user_pydantic.from_tortoise_orm(user)
    
    additional_data = {}
    if user.User_type.lower() == "citizen":
        citizen = await Citizen.get_or_none(User_name_id=user_name)
        if citizen:
            additional_data["citizen_data"] = await citizen_pydantic.from_tortoise_orm(citizen)
    
    elif user.User_type.lower() == "admin":
        admin = await Admin.get_or_none(User_name_id=user_name)
        if admin:
            additional_data["admin_data"] = await admin_pydantic.from_tortoise_orm(admin)
    
    elif user.User_type.lower() == "government_agency":
        agency = await GovernmentAgency.get_or_none(User_name_id=user_name)
        if agency:
            additional_data["agency_data"] = await government_agency_pydantic.from_tortoise_orm(agency)
    
    elif user.User_type.lower() == "panchayat_employee":
        employee = await PanchayatEmployee.get_or_none(User_name_id=user_name)
        if employee:
            additional_data["employee_data"] = await panchayat_employee_pydantic.from_tortoise_orm(employee)
        
    return {
        "status": "ok", 
        "data": response, 
        "additional_profile_data": additional_data
    }

@app.put('/user/{user_name}')
async def update_user(user_name: str, user_update: user_pydantic_in):
    user = await User.get_or_none(User_name=user_name)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_name} not found")
    
    old_values = {
        "Name": user.Name,
        "Email": user.Email,
        "Contact_number": user.Contact_number
    }
    
    update_data = user_update.dict(exclude_unset=True)
    
    if "Password" in update_data:
        update_data["Password"] = hash_password(update_data["Password"])
    
    await user.update_from_dict(update_data).save()
    
    changes = []
    for key, old_value in old_values.items():
        if key in update_data and update_data[key] != old_value:
            changes.append(f"{key}: {old_value} -> {update_data[key]}")
    
    if changes:
        await ActivityLog.create(
            Time=datetime.utcnow(),
            Affected_user_fk_id=user.User_name,  
            From_value="User Update",
            Old_val=", ".join(changes),
            New_val="User profile updated",
            User_name_fk_id=user.User_name  
        )
    
    response = await user_pydantic.from_tortoise_orm(user)
    return {"status": "ok", "data": response, "message": "User updated successfully"}

@app.delete('/user/{user_name}')
async def delete_user(user_name: str):
    user = await User.get_or_none(User_name=user_name)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_name} not found")
    
    user_type = user.User_type
    
    await user.delete()
    
    return {"status": "ok", "message": f"{user_type} user {user_name} deleted successfully"}

@app.put('/citizen/{citizen_id}')
async def update_citizen(citizen_id: int, citizen_data: citizen_pydantic_in, current_user: User = Depends(get_current_user)):
    citizen = await Citizen.get_or_none(Citizen_Id=citizen_id)
    if not citizen:
        raise HTTPException(status_code=404, detail=f"Citizen with ID {citizen_id} not found")
    
    update_data = citizen_data.dict(exclude_unset=True, exclude={"User_name"})
    await citizen.update_from_dict(update_data).save()
    
    
    await ActivityLog.create(
        Time=datetime.utcnow(),
        Affected_user_fk_id=citizen.User_name_id,  
        From_value="Citizen Profile Update",
        New_val="Citizen profile updated",
        User_name_fk_id=current_user.User_name  
    )
    
    response = await citizen_pydantic.from_tortoise_orm(citizen)
    return {"status": "ok", "data": response}

@app.get('/citizen/family/{family_id}')
async def get_family_members(family_id: int):
    family = await Family.get_or_none(Family_Id=family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Family with ID {family_id} not found")
    
    family_members = await Citizen.filter(Family_fk_id=family_id).all()
    
    members_data = []
    for member in family_members:
        member_data = await citizen_pydantic.from_tortoise_orm(member)
        user = await User.get_or_none(User_name=member.User_name_id)
        if user:
            member_dict = dict(member_data)
            member_dict.update({
                "Name": user.Name,
                "Contact": user.Contact_number,
                "Email": user.Email
            })
            members_data.append(member_dict)
    
    return {
        "status": "ok", 
        "family_id": family_id,
        "address": family.Address,
        "total_members": len(members_data),
        "members": members_data
    }

@app.post('/issues/create')
async def create_issue(issue_data: IssueCreate, current_user: User = Depends(get_current_user)):
    citizen = await Citizen.get_or_none(Citizen_Id=issue_data.citizen_fk)
    if not citizen:
        raise HTTPException(status_code=404, detail=f"Citizen with ID {issue_data.citizen_fk} not found")
    

    new_issue = await Issues.create(
        Citizen_fk_id=citizen.Citizen_Id, 
        Description=issue_data.description,
        status="Open"  
    )
    
    await ActivityLog.create(
        Time=datetime.utcnow(),
        Affected_user_fk_id=citizen.User_name_id,  
        From_value="Issue Creation",
        New_val=f"New issue created: {issue_data.description[:50]}...",
        User_name_fk_id=current_user.User_name  
    )
    
    response = await issues_pydantic.from_tortoise_orm(new_issue)
    return {"status": "ok", "data": response, "message": "Issue created successfully"}

@app.get('/issues/list')
async def list_issues(status: Optional[str] = None, citizen_id: Optional[int] = None):
    filters = {}
    if status:
        filters["status"] = status
    if citizen_id:
        filters["Citizen_fk_id"] = citizen_id
    
    if filters:
        issues = await Issues.filter(**filters).all()
    else:
        issues = await Issues.all()
    
    issues_data = []
    for issue in issues:
        issue_data = await issues_pydantic.from_tortoise_orm(issue)
        issues_data.append(issue_data)
    
    return {
        "status": "ok",
        "count": len(issues_data),
        "data": issues_data
    }
    
@app.put('/issues/{issue_id}/status', response_model=dict)
async def update_issue_status(issue_id: int, status: str, username: str = Depends(get_current_user)):
    valid_statuses = ["Open", "In Progress", "Resolved", "Closed", "Rejected"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    issue = await Issues.get_or_none(Issue_Id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue with ID {issue_id} not found")
    
    old_status = issue.status
    issue.status = status
    await issue.save()
    
    await ActivityLog.create(
        Time=datetime.utcnow(),
        Affected_user_fk=username,
        From_value=f"Issue Status Change",
        Old_val=old_status,
        New_val=status,
        User_name_fk=username
    )
    
    return {"status": "ok", "message": f"Issue status updated from {old_status} to {status}"}


register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True
)