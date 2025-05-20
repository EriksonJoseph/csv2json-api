"""
User Service

ดำเนินการเกี่ยวกับผู้ใช้งาน
"""
from fastapi import HTTPException
from app.repositories.user_repository import UserRepository
from app.api.schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from app.api.schemas.response_schemas import ResponseModel, PaginatedResponse
from app.models.user import User
from typing import Dict, List, Any

class UserService:
    """
    Service สำหรับจัดการผู้ใช้งาน
    """
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        สร้างผู้ใช้ใหม่
        """
        # ตรวจสอบว่า username ซ้ำหรือไม่
        existing_user = await self.repository.find_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="👎 Username นี้มีอยู่ในระบบแล้ว")
        
        # ตรวจสอบว่า email ซ้ำหรือไม่ (ถ้ามี)
        if user_data.email:
            existing_user = await self.repository.find_by_email(user_data.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="👎 Email นี้มีอยู่ในระบบแล้ว")
        
        # แปลงเป็น User model
        user = User(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            middle_name=user_data.middle_name
        )
        
        # บันทึกข้อมูลลงฐานข้อมูล
        created_user = await self.repository.create(user.to_dict(exclude_password=False))
        
        # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่ต้องการ
        user_dict = {**created_user}
        user_dict["id"] = str(user_dict.pop("_id"))
        
        return user_dict
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> ResponseModel:
        """
        อัปเดตข้อมูลผู้ใช้
        """
        # ตรวจสอบว่าผู้ใช้มีอยู่หรือไม่
        existing_user = await self.repository.find_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการอัปเดต")
        
        # สร้าง dict สำหรับเก็บข้อมูลที่จะอัปเดต
        update_data = {}
        
        # เพิ่มเฉพาะฟิลด์ที่ไม่ใช่ None ลงใน update_data
        user_dict = user_update.dict(exclude_unset=True)
        for field, value in user_dict.items():
            if value is not None:
                update_data[field] = value
        
        # ถ้ามีการอัปเดต email ให้ตรวจสอบว่าซ้ำหรือไม่
        if "email" in update_data and update_data["email"]:
            email_check = await self.repository.find_by_email(update_data["email"])
            if email_check and str(email_check["_id"]) != user_id:
                raise HTTPException(status_code=400, detail="👎 Email นี้มีอยู่ในระบบแล้ว")
        
        # ถ้าไม่มีข้อมูลที่จะอัปเดตให้แจ้งเตือน
        if not update_data:
            raise HTTPException(status_code=400, detail="⚠️ ไม่มีข้อมูลที่จะอัปเดต")
        
        # อัปเดตข้อมูลใน MongoDB
        updated_user = await self.repository.update(user_id, update_data)
        
        # ตรวจสอบว่าอัปเดตสำเร็จหรือไม่
        if updated_user is None:
            # ข้อมูลไม่มีการเปลี่ยนแปลง
            existing_user_dict = {**existing_user}
            existing_user_dict["id"] = str(existing_user_dict.pop("_id"))
            
            return ResponseModel(
                message="ℹ️ ไม่มีการเปลี่ยนแปลงข้อมูล",
                data=existing_user_dict
            )
        
        # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่ต้องการ
        updated_user_dict = {**updated_user}
        updated_user_dict["id"] = str(updated_user_dict.pop("_id"))
        
        return ResponseModel(
            message="✅ อัปเดตข้อมูลผู้ใช้สำเร็จ",
            data=updated_user_dict
        )
    
    async def get_all_users(self, page: int, limit: int) -> PaginatedResponse:
        """
        ดึงรายการผู้ใช้ทั้งหมด
        """
        # คำนวณ skip สำหรับ pagination
        skip = (page - 1) * limit
        
        # นับจำนวน users ทั้งหมด
        total_users = await self.repository.count()
        
        # ดึงข้อมูลโดยมีการทำ pagination
        users_list = await self.repository.find_all(skip, limit)
        
        # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่ต้องการ
        users = []
        for user in users_list:
            user_dict = {**user}
            user_dict["id"] = str(user_dict.pop("_id"))
            users.append(user_dict)
        
        return PaginatedResponse(
            message="👤 รายชื่อผู้ใช้ทั้งหมด",
            total=total_users,
            page=page,
            limit=limit,
            pages=(total_users + limit - 1) // limit,
            data=users
        )
    
    async def get_user(self, user_id: str) -> ResponseModel:
        """
        ดึงข้อมูลผู้ใช้ตาม ID
        """
        # ดึงข้อมูลผู้ใช้จาก MongoDB
        user = await self.repository.find_by_id(user_id)
        
        # ตรวจสอบว่าพบผู้ใช้หรือไม่
        if not user:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการ")
        
        # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่ต้องการ
        user_dict = {**user}
        user_dict["id"] = str(user_dict.pop("_id"))
        
        return ResponseModel(
            message="👤 ข้อมูลผู้ใช้",
            data=user_dict
        )
    
    async def delete_user(self, user_id: str) -> ResponseModel:
        """
        ลบผู้ใช้ตาม ID
        """
        # ลบข้อมูลผู้ใช้จาก MongoDB
        deleted_user = await self.repository.delete(user_id)
        
        # ตรวจสอบว่าลบสำเร็จหรือไม่
        if not deleted_user:
            raise HTTPException(status_code=404, detail="🔍 ไม่พบผู้ใช้ที่ต้องการลบ")
        
        # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่ต้องการ
        user_dict = {**deleted_user}
        user_dict["id"] = str(user_dict.pop("_id"))
        
        return ResponseModel(
            message="🗑️ ลบข้อมูลผู้ใช้สำเร็จ",
            data=user_dict
        )