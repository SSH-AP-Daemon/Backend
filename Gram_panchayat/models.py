from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, Boolean, Float, DateTime
from sqlalchemy import func  
from sqlalchemy.orm import relationship
from sqlalchemy.types import LargeBinary  
from .database import Base  

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
    
    assets = relationship('Asset', back_populates='user', cascade="all, delete-orphan")

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
    
    documents = relationship("Document", back_populates="citizen", cascade="all, delete-orphan")
    issues = relationship('Issue', back_populates='citizen', cascade="all, delete-orphan")
    financial_data = relationship("FinancialData", back_populates="citizen", cascade="all, delete-orphan")
    welfare_enrollments = relationship("WelfareEnrol", back_populates="citizen", cascade="all, delete-orphan")
    
    headed_families = relationship('Family', foreign_keys='Family.Head_citizen_id', back_populates='family_head', cascade="all, delete-orphan")
    member_of_families = relationship('Family', foreign_keys='Family.Member_citizen_id', back_populates='family_member', cascade="all, delete-orphan")
    
class GovernmentAgencies(Base):
    __tablename__ = 'Government_agencies'
    
    Agency_id = Column(Integer, primary_key=True, autoincrement=True)
    User_name = Column(String(20), ForeignKey('User.User_name'), nullable=False)
    Role = Column(String(100), nullable=False)
    
    user = relationship('User', back_populates='government_agencies')
    schemes = relationship('WelfareScheme', back_populates='agency', cascade="all, delete-orphan")
    infrastructures = relationship('Infrastructure', back_populates='agency', cascade="all, delete-orphan")
    
    
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
    
    user = relationship('User', back_populates='assets')
    agricultural_land = relationship('AgriculturalLand', back_populates='asset', uselist=False, cascade="all, delete-orphan")

class AgriculturalLand(Base):
    __tablename__ = 'Agricultural_land'
    
    Land_id = Column(Integer, primary_key=True, autoincrement=True)
    Asset_id = Column(Integer, ForeignKey('Asset.Asset_id'), nullable=False)
    Year = Column(Integer, nullable=False)
    Season = Column(String(20), nullable=False)
    Crop_type = Column(String(30), nullable=False)
    Area_cultivated = Column(Float, nullable=False)
    Yield = Column(Float, nullable=False)
    
    asset = relationship('Asset', back_populates='agricultural_land')
    
class Family(Base):
    __tablename__ = 'Family'
    
    Head_citizen_id = Column(Integer, ForeignKey('Citizen.Citizen_id'), primary_key=True)  
    Member_citizen_id = Column(Integer, ForeignKey('Citizen.Citizen_id'), primary_key=True)  
    Family_id = Column(Integer)
    Relationship = Column(String(30), nullable=False)
    
    family_head = relationship('Citizen', foreign_keys=[Head_citizen_id], back_populates='headed_families')
    family_member = relationship('Citizen', foreign_keys=[Member_citizen_id], back_populates='member_of_families')
    
class Issue(Base):
    __tablename__ = 'Issue'
    
    Issue_id = Column(Integer, primary_key=True, autoincrement=True)
    Citizen_id = Column(Integer, ForeignKey('Citizen.Citizen_id'), nullable=False)  # Changed from User_name
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='PENDING')  # PENDING, IN_PROGRESS, RESOLVED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    citizen = relationship('Citizen', back_populates='issues')  

class Document(Base):
    __tablename__ = "Document"
    
    Document_id = Column(Integer, primary_key=True, autoincrement=True)
    Citizen_id = Column(Integer, ForeignKey('Citizen.Citizen_id'), nullable=False)  # Changed from User_name
    Type = Column(String(100), nullable=False)
    Pdf_data = Column(LargeBinary, nullable=False)
    
    # Updated relationship
    citizen = relationship("Citizen", back_populates="documents")  # Changed from user

class FinancialData(Base):
    __tablename__ = "Financial_data"
    
    Financial_id = Column(Integer, primary_key=True, autoincrement=True)
    Citizen_id = Column(Integer, ForeignKey('Citizen.Citizen_id'), nullable=False)
    year = Column(Integer, nullable=False)
    Annual_Income = Column(Float, nullable=False)
    Income_source = Column(String(100), nullable=False)
    Tax_paid = Column(Float, nullable=False)
    Tax_liability = Column(Float, nullable=False)
    Debt_liability = Column(Float, nullable=False)
    Credit_score = Column(Integer)
    Last_updated = Column(DateTime, nullable=False, default=func.now())
    
    citizen = relationship("Citizen", back_populates="financial_data")

class WelfareScheme(Base):
    __tablename__ = "Welfare_scheme"
    
    Scheme_id = Column(Integer, primary_key=True, autoincrement=True)
    Scheme_name = Column(String(100), nullable=False)
    Description = Column(Text)
    Application_deadline = Column(Date)
    Agency_id = Column(Integer, ForeignKey('Government_agencies.Agency_id'), nullable=False)
    # enrollments = relationship("WelfareEnrol", back_populates="scheme", cascade="all, delete-orphan")
    
    enrollments = relationship("WelfareEnrol", back_populates="scheme", cascade="all, delete-orphan")
    agency = relationship("GovernmentAgencies", back_populates="schemes")

class WelfareEnrol(Base):
    __tablename__ = "Welfare_enrol"
    
    Enrol_id = Column(Integer, primary_key=True, autoincrement=True)
    Citizen_id = Column(Integer, ForeignKey('Citizen.Citizen_id'), nullable=False)
    Scheme_fk = Column(Integer, ForeignKey('Welfare_scheme.Scheme_id'), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    
    citizen = relationship("Citizen", back_populates="welfare_enrollments")
    scheme = relationship("WelfareScheme", back_populates="enrollments")

class Infrastructure(Base):
    __tablename__ = "Infrastructure"
    
    Infra_id = Column(Integer, primary_key=True, autoincrement=True)
    Description = Column(Text)
    Location = Column(Text)
    Funding = Column(Float, nullable=False)
    Actual_cost = Column(Float, nullable=False, default=0)
    Agency_id = Column(Integer, ForeignKey('Government_agencies.Agency_id'), nullable=False)
    agency = relationship("GovernmentAgencies", back_populates="infrastructures")
