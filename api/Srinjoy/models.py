from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from datetime import date, datetime

class User(Model):
    User_name = fields.CharField(max_length=255, pk=True)
    Name = fields.CharField(max_length=255)
    Password = fields.CharField(max_length=255)
    Email = fields.CharField(max_length=255, null=True)
    Contact_number = fields.CharField(max_length=20)
    User_type = fields.CharField(max_length=50)
    
    class Meta:
        table = "user"

class Family(Model):
    Family_Id = fields.IntField(pk=True)
    Address = fields.TextField(null=True)
    
    class Meta:
        table = "family"

class Citizen(Model):
    Citizen_Id = fields.IntField(pk=True)
    User_name = fields.OneToOneField('models.User', related_name='citizen', on_delete=fields.CASCADE)
    Date_of_birth = fields.DateField(null=True)
    Date_of_death = fields.DateField(null=True)
    Gender = fields.CharField(max_length=10, null=True)
    Address = fields.TextField(null=True)
    Educational_qualification = fields.CharField(max_length=50, null=True)
    Occupation = fields.CharField(max_length=255, null=True)
    Family_fk = fields.ForeignKeyField('models.Family', related_name='citizens', on_delete=fields.SET_NULL, null=True)
    
    class Meta:
        table = "citizen"

# Family.add_field('Family_head', fields.ForeignKeyField('models.Citizen', related_name='head_of_family', null=True, on_delete=fields.SET_NULL))

class GovernmentAgency(Model):
    Agency_Id = fields.IntField(pk=True)
    User_name = fields.OneToOneField('models.User', related_name='government_agency', on_delete=fields.CASCADE)
    Role = fields.CharField(max_length=255, null=True)
    
    class Meta:
        table = "government_agencies"

class Admin(Model):
    Admin_id = fields.IntField(pk=True)
    User_name = fields.OneToOneField('models.User', related_name='admin', on_delete=fields.CASCADE)
    Gender = fields.CharField(max_length=10, null=True)
    Date_of_birth = fields.DateField(null=True)
    Address = fields.CharField(max_length=255, null=True)
    
    class Meta:
        table = "admin"

class PanchayatEmployee(Model):
    Member_Id = fields.IntField(pk=True)
    Role = fields.CharField(max_length=255, null=True)
    User_name = fields.OneToOneField('models.User', related_name='panchayat_employee', on_delete=fields.CASCADE)
    Citizen_fk = fields.ForeignKeyField('models.Citizen', related_name='employee_info', on_delete=fields.CASCADE, null=True)
    
    class Meta:
        table = "panchayat_employee"

class Assets(Model):
    Asset_Id = fields.IntField(pk=True)
    Citizen_fk = fields.ForeignKeyField('models.Citizen', related_name='assets', on_delete=fields.CASCADE, null=True)
    Type = fields.CharField(max_length=255, null=True)
    Valuation = fields.FloatField(null=True)
    Is_deleted = fields.BooleanField(null=True)
    
    class Meta:
        table = "assets"

class AgriculturalLand(Model):
    Agri_land_Id = fields.IntField(pk=True)
    Year = fields.IntField(null=True)
    Crop_type = fields.CharField(max_length=255, null=True)
    Area_cultivated = fields.FloatField(null=True)
    Yield = fields.FloatField(null=True)
    Season = fields.CharField(max_length=50, null=True)
    Asset_fk = fields.ForeignKeyField('models.Assets', related_name='agricultural_lands', on_delete=fields.CASCADE, null=True)
    
    class Meta:
        table = "agricultural_land"

class Census(Model):
    Census_id = fields.IntField(pk=True)
    Year = fields.IntField(null=True)
    Total_population = fields.IntField(null=True)
    Male_population = fields.IntField(null=True)
    Female_population = fields.IntField(null=True)
    Literacy_Rate = fields.FloatField(null=True)
    
    class Meta:
        table = "census"

class FinancialData(Model):
    Financial_Id = fields.IntField(pk=True)
    Annual_Income = fields.FloatField(null=True)
    Income_source = fields.CharField(max_length=255, null=True)
    Tax_paid = fields.FloatField(null=True)
    Tax_liability = fields.FloatField(null=True)
    Debt_liability = fields.FloatField(null=True)
    Credit_score = fields.IntField(null=True)
    Last_updated = fields.DatetimeField(null=True)
    Citizen_fk = fields.ForeignKeyField('models.Citizen', related_name='financial_data', on_delete=fields.CASCADE, null=True)
    
    class Meta:
        table = "financial_data"

class EnvironmentalData(Model):
    Year = fields.IntField(pk=True)
    Aqi = fields.FloatField(null=True)
    Forest_cover = fields.FloatField(null=True)
    Odf = fields.FloatField(null=True)
    Afforestation_data = fields.FloatField(null=True)
    Precipitation = fields.FloatField(null=True)
    Water_quality = fields.FloatField(null=True)
    
    class Meta:
        table = "environmental_data"

class WelfareSchemes(Model):
    Scheme_Id = fields.IntField(pk=True)
    Scheme_name = fields.CharField(max_length=255, null=True)
    Description = fields.TextField(null=True)
    Application_deadline = fields.DateField(null=True)
    
    class Meta:
        table = "welfare_schemes"

class Infrastructure(Model):
    Infra_Id = fields.IntField(pk=True)
    Description = fields.TextField(null=True)
    Location = fields.TextField(null=True)
    Funding = fields.FloatField(null=True)
    Actual_cost = fields.FloatField(null=True)
    
    class Meta:
        table = "infrastructure"

class ActivityLog(Model):
    Log_Id = fields.IntField(pk=True)
    Time = fields.DatetimeField(null=True)
    Affected_user_fk = fields.ForeignKeyField('models.User', related_name='affected_activities', on_delete=fields.CASCADE, null=True)
    From_value = fields.TextField(null=True)
    New_val = fields.TextField(null=True)
    Old_val = fields.TextField(null=True)
    User_name_fk = fields.ForeignKeyField('models.User', related_name='initiated_activities', on_delete=fields.CASCADE, null=True)
    
    class Meta:
        table = "activity_log"

class Issues(Model):
    Issue_Id = fields.IntField(pk=True)
    Citizen_fk = fields.ForeignKeyField('models.Citizen', related_name='issues', on_delete=fields.CASCADE, null=True)
    Description = fields.TextField(null=True)
    status = fields.CharField(max_length=50, null=True)
    
    class Meta:
        table = "issues"

class Documents(Model):
    Doc_Id = fields.IntField(pk=True)
    Citizen_fk = fields.ForeignKeyField('models.Citizen', related_name='documents', on_delete=fields.CASCADE, null=True)
    Type = fields.CharField(max_length=255, null=True)
    Pdf_data = fields.CharField(max_length=255)
    
    class Meta:
        table = "documents"

class WelfareEnrol(Model):
    id = fields.IntField(pk=True, generated=True)
    Citizen_fk = fields.ForeignKeyField('models.Citizen', related_name='welfare_enrolments', on_delete=fields.CASCADE)
    Scheme_fk = fields.ForeignKeyField('models.WelfareSchemes', related_name='enrolled_citizens', on_delete=fields.CASCADE)
    status = fields.CharField(max_length=50, null=True)
    
    class Meta:
        table = "welfare_enrol"
        unique_together = (("Citizen_fk", "Scheme_fk"),)

user_pydantic = pydantic_model_creator(User, name="User")
user_pydantic_in = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)

family_pydantic = pydantic_model_creator(Family, name="Family")
family_pydantic_in = pydantic_model_creator(Family, name="FamilyIn", exclude_readonly=True)

citizen_pydantic = pydantic_model_creator(Citizen, name="Citizen")
citizen_pydantic_in = pydantic_model_creator(Citizen, name="CitizenIn", exclude_readonly=True)

government_agency_pydantic = pydantic_model_creator(GovernmentAgency, name="GovernmentAgency")
government_agency_pydantic_in = pydantic_model_creator(GovernmentAgency, name="GovernmentAgencyIn", exclude_readonly=True)

admin_pydantic = pydantic_model_creator(Admin, name="Admin")
admin_pydantic_in = pydantic_model_creator(Admin, name="AdminIn", exclude_readonly=True)

panchayat_employee_pydantic = pydantic_model_creator(PanchayatEmployee, name="PanchayatEmployee")
panchayat_employee_pydantic_in = pydantic_model_creator(PanchayatEmployee, name="PanchayatEmployeeIn", exclude_readonly=True)

census_pydantic = pydantic_model_creator(Census, name="Census")
census_pydantic_in = pydantic_model_creator(Census, name="CensusIn", exclude_readonly=True)

agricultural_land_pydantic = pydantic_model_creator(AgriculturalLand, name="AgriculturalLand")
agricultural_land_pydantic_in = pydantic_model_creator(AgriculturalLand, name="AgriculturalLandIn", exclude_readonly=True)

financial_data_pydantic = pydantic_model_creator(FinancialData, name="FinancialData")
financial_data_pydantic_in = pydantic_model_creator(FinancialData, name="FinancialDataIn", exclude_readonly=True)

environmental_data_pydantic = pydantic_model_creator(EnvironmentalData, name="EnvironmentalData")
environmental_data_pydantic_in = pydantic_model_creator(EnvironmentalData, name="EnvironmentalDataIn", exclude_readonly=True)

welfare_schemes_pydantic = pydantic_model_creator(WelfareSchemes, name="WelfareSchemes")
welfare_schemes_pydantic_in = pydantic_model_creator(WelfareSchemes, name="WelfareSchemesIn", exclude_readonly=True)

infrastructure_pydantic = pydantic_model_creator(Infrastructure, name="Infrastructure")
infrastructure_pydantic_in = pydantic_model_creator(Infrastructure, name="InfrastructureIn", exclude_readonly=True)

activity_log_pydantic = pydantic_model_creator(ActivityLog, name="ActivityLog")
activity_log_pydantic_in = pydantic_model_creator(ActivityLog, name="ActivityLogIn", exclude_readonly=True)

issues_pydantic = pydantic_model_creator(Issues, name="Issues")
issues_pydantic_in = pydantic_model_creator(Issues, name="IssuesIn", exclude_readonly=True)

documents_pydantic = pydantic_model_creator(Documents, name="Documents")
documents_pydantic_in = pydantic_model_creator(Documents, name="DocumentsIn", exclude_readonly=True)

assets_pydantic = pydantic_model_creator(Assets, name="Assets")
assets_pydantic_in = pydantic_model_creator(Assets, name="AssetsIn", exclude_readonly=True)

welfare_enrol_pydantic = pydantic_model_creator(WelfareEnrol, name="WelfareEnrol")
welfare_enrol_pydantic_in = pydantic_model_creator(WelfareEnrol, name="WelfareEnrolIn", exclude_readonly=True)