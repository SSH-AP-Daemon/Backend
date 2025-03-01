from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, Boolean, Float, DateTime
from .database import Base
from sqlalchemy.orm import relationship
import datetime

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
    
class Asset(Base):
    __tablename__ = 'Asset'
    
    Asset_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    Type = Column(String(50), nullable=False)
    Valuation = Column(String(50), nullable=False)
    
    # Relationships
    user = relationship('User', backref='assets')
    agricultural_land = relationship('AgriculturalLand', back_populates='asset', uselist=False)

class AgriculturalLand(Base):
    __tablename__ = 'Agricultural_land'
    
    Land_id = Column(Integer, primary_key=True, autoincrement=True)
    Asset_id = Column(Integer, ForeignKey('Asset.Asset_id'), nullable=False)
    Year = Column(Integer, nullable=False)
    Season = Column(String(20), nullable=False)
    Crop_type = Column(String(30), nullable=False)
    Area_cultivated = Column(Float, nullable=False)
    Yield = Column(Float, nullable=False)
    
    # Relationship
    asset = relationship('Asset', back_populates='agricultural_land')
    
class Family(Base):
    __tablename__ = 'Family'
    
    Family_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)  # Head of family
    Member_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)  # Family member
    Relationship = Column(String(30), nullable=False)
    
    # Relationships with User table
    family_head = relationship('User', foreign_keys=[User_name], backref='headed_families')
    family_member = relationship('User', foreign_keys=[Member_name], backref='member_of_families')
    
class Issue(Base):
    __tablename__ = 'Issue'
    
    Issue_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='PENDING')  # PENDING, IN_PROGRESS, RESOLVED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship('User', backref='issues')