from sqlalchemy import Column, Integer, String,ForeignKey,Text,Date
from .database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'User'
    
    User_name = Column(String(20), primary_key=True)
    Password = Column(String(128), nullable=False)
    Name = Column(String(60), nullable=False)
    Email = Column(String(128), nullable=True)
    Contact_number = Column(String(20), nullable=False)
    User_type = Column(String(30), nullable=False, default='Citizen')

    
class Citizen(Base):
    __tablename__ = 'Citizen'
    Citizen_id = Column(Integer, primary_key=True, autoincrement=True)
    Date_of_birth = Column(Date, nullable=False)
    Date_of_death = Column(Date, nullable=True)
    Gender = Column(String(10), nullable=False)
    Address = Column(Text, nullable=False)  
    Educational_qualification = Column(String(20), nullable=False, default='Illiterate')
    Occupation = Column(String(100), nullable=False)  
    
class GovernmentAgencies(Base):
    __tablename__ = 'Government_agencies'
    Agency_id = Column(Integer, primary_key=True, autoincrement=True)
    Role = Column(String(100), nullable=False)
    
    
class Admin(Base):
    __tablename__ = 'Admin'
    Admin_id = Column(Integer, primary_key=True, autoincrement=True)
    Gender = Column(String(10), nullable=False)
    Date_of_birth = Column(Date, nullable=False)
    Address = Column(Text, nullable=False)
    
class PanchayatEmployee(Base):
    __tablename__ = 'Panchayat_employee'
    Member_id = Column(Integer, primary_key=True, autoincrement=True)
    Role = Column(String(100), nullable=False)