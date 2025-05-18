from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.database import get_collection
from app.models.entity import EntityModel, EntityCreate, EntityUpdate

# Service class สำหรับจัดการ Entity
class EntityService:
    def __init__(self):
        self.collection = get_collection("entities")
    
    # ดึงข้อมูล Entity ทั้งหมด พร้อม pagination
    async def get_entities(self, page: int = 1, limit: int = 10, search: str = None) -> Dict[str, Any]:
        skip = (page - 1) * limit
        
        # สร้างเงื่อนไขสำหรับการค้นหา
        query = {}
        if search:
            query = {
                "$or": [
                    {"Entity_LogicalId": {"$regex": search, "$options": "i"}},
                    {"Entity_EU_ReferenceNumber": {"$regex": search, "$options": "i"}},
                    {"NameAlias_WholeName": {"$regex": search, "$options": "i"}}
                ]
            }
        
        # นับจำนวนทั้งหมด
        total = await self.collection.count_documents(query)
        
        # ดึงข้อมูลตาม pagination
        cursor = self.collection.find(query).skip(skip).limit(limit)
        entities = await cursor.to_list(length=limit)
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": [EntityModel(**entity) for entity in entities]
        }
    
    # ดึงข้อมูล Entity ตาม ID
    async def get_entity_by_id(self, entity_id: str) -> Optional[EntityModel]:
        entity = await self.collection.find_one({"_id": ObjectId(entity_id)})
        if entity:
            return EntityModel(**entity)
        return None
    
    # ดึงข้อมูล Entity ตาม Logical ID
    async def get_entity_by_logical_id(self, logical_id: str) -> Optional[EntityModel]:
        entity = await self.collection.find_one({"Entity_LogicalId": logical_id})
        if entity:
            return EntityModel(**entity)
        return None
    
    # สร้าง Entity ใหม่
    async def create_entity(self, entity_data: EntityCreate) -> EntityModel:
        entity_dict = entity_data.dict()
        entity_dict["created_at"] = datetime.now()
        entity_dict["updated_at"] = datetime.now()
        
        result = await self.collection.insert_one(entity_dict)
        
        created_entity = await self.collection.find_one({"_id": result.inserted_id})
        return EntityModel(**created_entity)
    
    # อัพเดท Entity
    async def update_entity(self, entity_id: str, entity_data: EntityUpdate) -> Optional[EntityModel]:
        entity_dict = {k: v for k, v in entity_data.dict().items() if v is not None}
        entity_dict["updated_at"] = datetime.now()
        
        await self.collection.update_one(
            {"_id": ObjectId(entity_id)},
            {"$set": entity_dict}
        )
        
        updated_entity = await self.collection.find_one({"_id": ObjectId(entity_id)})
        if updated_entity:
            return EntityModel(**updated_entity)
        return None
    
    # ลบ Entity
    async def delete_entity(self, entity_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0