from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

# สร้าง custom field สำหรับ ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, ObjectId):
            if not isinstance(v, str):
                raise TypeError('ObjectId required')
            try:
                return ObjectId(v)
            except:
                raise ValueError('Invalid ObjectId')
        return v

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Model สำหรับ Entity ที่จะเก็บใน MongoDB
class EntityModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    fileGenerationDate: Optional[str] = None
    Entity_LogicalId: Optional[str] = None
    Entity_EU_ReferenceNumber: Optional[str] = None
    Entity_UnitedNationId: Optional[str] = None
    Entity_DesignationDate: Optional[str] = None
    Entity_DesignationDetails: Optional[str] = None
    Entity_Remark: Optional[str] = None
    Entity_SubjectType: Optional[str] = None
    Entity_SubjectType_ClassificationCode: Optional[str] = None
    
    # สามารถเพิ่ม field อื่นๆ ตามต้องการ
    # คุณสามารถเพิ่ม field ทุกตัวจาก CSV หรือเลือกเฉพาะ field ที่สำคัญ
    
    # ข้อมูลเกี่ยวกับชื่อและนามสกุล
    NameAlias_FirstName: Optional[str] = None
    NameAlias_LastName: Optional[str] = None
    NameAlias_WholeName: Optional[str] = None
    NameAlias_Gender: Optional[str] = None
    NameAlias_Title: Optional[str] = None
    NameAlias_Function: Optional[str] = None
    
    # ข้อมูลเกี่ยวกับสถานที่เกิด
    BirthDate_BirthDate: Optional[str] = None
    BirthDate_Year: Optional[str] = None
    BirthDate_Place: Optional[str] = None
    BirthDate_CountryDescription: Optional[str] = None
    
    # ข้อมูลเกี่ยวกับสัญชาติ
    Citizenship_CountryDescription: Optional[str] = None
    
    # เพิ่ม timestamp เมื่อสร้างและอัพเดท
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: lambda oid: str(oid),
            datetime: lambda dt: dt.isoformat()
        }

# Model สำหรับสร้าง Entity ใหม่
class EntityCreate(BaseModel):
    Entity_LogicalId: str
    Entity_EU_ReferenceNumber: Optional[str] = None
    Entity_SubjectType: Optional[str] = None
    NameAlias_WholeName: Optional[str] = None
    # เพิ่ม field อื่นๆ ตามต้องการ

# Model สำหรับอัพเดท Entity
class EntityUpdate(BaseModel):
    Entity_LogicalId: Optional[str] = None
    Entity_EU_ReferenceNumber: Optional[str] = None
    Entity_SubjectType: Optional[str] = None
    NameAlias_WholeName: Optional[str] = None
    # เพิ่ม field อื่นๆ ตามต้องการ

# Model สำหรับการตอบกลับหลายรายการ
class EntityList(BaseModel):
    total: int
    page: int
    limit: int
    data: List[EntityModel]