from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "user"
    User_name = Column(String(255), primary_key=True)
    Name = Column(String(255), nullable=False)
    Password = Column(String(255), nullable=False)
    Email = Column(String(255))
    Contact_number = Column(String(20), nullable=False)
    User_type = Column(String(50), nullable=False)
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'))
    Government_agencies_fk = Column(Integer, ForeignKey('government_agencies.Agency_Id'))
    Admin_fk = Column(Integer, ForeignKey('admin.Admin_id'))
    Panchayat_employee_fk = Column(Integer, ForeignKey('panchayat_employee.Member_Id'))

    # Relationships
    citizen = relationship("Citizen", back_populates="user")
    government_agency = relationship("GovernmentAgency", back_populates="user")
    admin = relationship("Admin", back_populates="user")
    panchayat_employee = relationship("PanchayatEmployee", back_populates="user")

class Citizen(Base):
    __tablename__ = "citizen"
    Citizen_Id = Column(Integer, primary_key=True)
    User_name = Column(String(255), ForeignKey('user.User_name'), unique=True)
    Date_of_birth = Column(Date)
    Date_of_death = Column(Date)
    Gender = Column(String(10))
    Address = Column(Text)
    Educational_qualification = Column(String(50))
    Occupation = Column(String(255))
    Family_fk = Column(Integer, ForeignKey('family.Family_Id'))

    # Relationships
    family = relationship("Family", back_populates="citizens")
    user = relationship("User", back_populates="citizen")

class GovernmentAgency(Base):
    __tablename__ = "government_agencies"
    Agency_Id = Column(Integer, primary_key=True)
    User_name = Column(String(255), ForeignKey('user.User_name'), unique=True)
    Role = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="government_agency")

class Admin(Base):
    __tablename__ = "admin"
    Admin_id = Column(Integer, primary_key=True)
    User_name = Column(String(255), ForeignKey('user.User_name'), unique=True)
    Gender = Column(String(10))
    Date_of_birth = Column(Date)
    Address = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="admin")

class PanchayatEmployee(Base):
    __tablename__ = "panchayat_employee"
    Member_Id = Column(Integer, primary_key=True)
    Role = Column(String(255))
    User_name = Column(String(255), ForeignKey('user.User_name'), unique=True)
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'), unique=True)

    # Relationships
    user = relationship("User", back_populates="panchayat_employee")
    citizen = relationship("Citizen")

class Census(Base):
    __tablename__ = "census"
    Census_id = Column(Integer, primary_key=True)
    Year = Column(Integer)
    Total_population = Column(Integer)
    Male_population = Column(Integer)
    Female_population = Column(Integer)
    Literacy_Rate = Column(Float)

class AgriculturalLand(Base):
    __tablename__ = "agricultural_land"
    Agri_land_Id = Column(Integer, primary_key=True)
    Year = Column(Integer)
    Crop_type = Column(String(255))
    Area_cultivated = Column(Float)
    Yield = Column(Float)
    Season = Column(String(50))
    Asset_fk = Column(Integer, ForeignKey('assets.Asset_Id'))

class FinancialData(Base):
    __tablename__ = "financial_data"
    Financial_Id = Column(Integer, primary_key=True)
    Annual_Income = Column(Float)
    Income_source = Column(String(255))
    Tax_paid = Column(Float)
    Tax_liability = Column(Float)
    Debt_liability = Column(Float)
    Credit_score = Column(Integer)
    Last_updated = Column(TIMESTAMP)
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'))

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"
    Year = Column(Integer, primary_key=True)
    Aqi = Column(Float)
    Forest_cover = Column(Float)
    Odf = Column(Float)
    Afforestation_data = Column(Float)
    Precipitation = Column(Float)
    Water_quality = Column(Float)

class Family(Base):
    __tablename__ = "family"
    Family_Id = Column(Integer, primary_key=True)
    Address = Column(Text)
    Family_head = Column(Integer, ForeignKey('citizen.Citizen_Id'))

    # Relationships
    citizens = relationship("Citizen", back_populates="family")

class WelfareSchemes(Base):
    __tablename__ = "welfare_schemes"
    Scheme_Id = Column(Integer, primary_key=True)
    Scheme_name = Column(String(255))
    Description = Column(Text)
    Application_deadline = Column(Date)

class Infrastructure(Base):
    __tablename__ = "infrastructure"
    Infra_Id = Column(Integer, primary_key=True)
    Description = Column(Text)
    Location = Column(Text)
    Funding = Column(Float)
    Actual_cost = Column(Float)

class ActivityLog(Base):
    __tablename__ = "activity_log"
    Log_Id = Column(Integer, primary_key=True)
    Time = Column(TIMESTAMP)
    Affected_user_fk = Column(Integer, ForeignKey('user.User_name'))
    From_value = Column(Text)
    New_val = Column(Text)
    Old_val = Column(Text)
    User_name_fk = Column(Integer, ForeignKey('user.User_name'))

class Issues(Base):
    __tablename__ = "issues"
    Issue_Id = Column(Integer, primary_key=True)
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'))
    Description = Column(Text)
    status = Column(String(50))

class Documents(Base):
    __tablename__ = "documents"
    Doc_Id = Column(Integer, primary_key=True)
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'))
    Type = Column(String(255))
    Pdf_data = Column(String, nullable=False)

class Assets(Base):
    __tablename__ = "assets"
    Asset_Id = Column(Integer, primary_key=True)
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'))
    Type = Column(String(255))
    Valuation = Column(Float)
    Is_deleted = Column(Boolean)

class WelfareEnrol(Base):
    __tablename__ = "welfare_enrol"
    Citizen_fk = Column(Integer, ForeignKey('citizen.Citizen_Id'), primary_key=True)
    Scheme_fk = Column(Integer, ForeignKey('welfare_schemes.Scheme_Id'), primary_key=True)
    status = Column(String(50))
