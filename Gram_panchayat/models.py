from sqlalchemy import Column, Integer, String,ForeignKey,Text,Date,Boolean
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
    is_verified = Column(Boolean, nullable=False, default=False)
    citizen = relationship('Citizen', back_populates='user', uselist=False)
    admin = relationship('Admin', back_populates='user', uselist=False)
    government_agencies = relationship('GovernmentAgencies', back_populates='user', uselist=False)
    panchayat_employee = relationship('PanchayatEmployee', back_populates='user', uselist=False)


    
class Citizen(Base):
    __tablename__ = 'Citizen'
    Citizen_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    Date_of_birth = Column(Date, nullable=False)
    Date_of_death = Column(Date, nullable=True)
    Gender = Column(String(10), nullable=False)
    Address = Column(Text, nullable=False)
    Educational_qualification = Column(String(100), nullable=False)
    Occupation = Column(String(100), nullable=False)
    user = relationship('User', back_populates='citizen')
    
class GovernmentAgencies(Base):
    __tablename__ = 'Government_agencies'
    Agency_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    Role = Column(String(100), nullable=False)
    user = relationship('User', back_populates='government_agencies')
    
    
    
class Admin(Base):
    __tablename__ = 'Admin'
    Admin_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    Gender = Column(String(10), nullable=False)
    Date_of_birth = Column(Date, nullable=False)
    Address = Column(Text, nullable=False)
    user = relationship('User', back_populates='admin')
    
class PanchayatEmployee(Base):
    __tablename__ = 'Panchayat_employee'
    Member_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    Role = Column(String(100), nullable=False)
    user = relationship('User', back_populates='panchayat_employee')