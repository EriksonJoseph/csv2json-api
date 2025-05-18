from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from app.models.entity import EntityModel, EntityCreate, EntityUpdate, EntityList
from app.services.entity_service import EntityService

router = APIRouter(
    prefix="/api/entities",
    tags=["entities"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=EntityList)
async def get_entities(
    page: int = Query(1, ge=1, description="หน้าที่ต้องการ"),
    limit: int = Query(10, ge=1, le=100, description="จำนวนรายการต่อหน้า"),
    search: Optional[str] = Query(None, description="คำค้นหา"),
    service: EntityService = Depends()
):
    """
    ดึงข้อมูล Entity ทั้งหมด พร้อม pagination และค้นหา
    """
    return await service.get_entities(page, limit, search)

@router.get("/{entity_id}", response_model=EntityModel)
async def get_entity(
    entity_id: str = Path(..., description="ID ของ entity"),
    service: EntityService = Depends()
):
    """
    ดึงข้อมูล Entity ตาม ID
    """
    entity = await service.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="ไม่พบ Entity")
    return entity

@router.get("/logical-id/{logical_id}", response_model=EntityModel)
async def get_entity_by_logical_id(
    logical_id: str = Path(..., description="Logical ID ของ entity"),
    service: EntityService = Depends()
):
    """
    ดึงข้อมูล Entity ตาม Logical ID
    """
    entity = await service.get_entity_by_logical_id(logical_id)
    if not entity:
        raise HTTPException(status_code=404, detail="ไม่พบ Entity")
    return entity

@router.post("/", response_model=EntityModel)
async def create_entity(
    entity: EntityCreate,
    service: EntityService = Depends()
):
    """
    สร้าง Entity ใหม่
    """
    # ตรวจสอบว่ามี logical_id ซ้ำหรือไม่
    existing_entity = await service.get_entity_by_logical_id(entity.Entity_LogicalId)
    if existing_entity:
        raise HTTPException(status_code=400, detail="Entity_LogicalId นี้มีอยู่แล้ว")
    
    return await service.create_entity(entity)

@router.put("/{entity_id}", response_model=EntityModel)
async def update_entity(
    entity_id: str,
    entity: EntityUpdate,
    service: EntityService = Depends()
):
    """
    อัพเดท Entity
    """
    # ตรวจสอบว่ามี entity_id นี้หรือไม่
    existing_entity = await service.get_entity_by_id(entity_id)
    if not existing_entity:
        raise HTTPException(status_code=404, detail="ไม่พบ Entity")
    
    # ตรวจสอบว่าถ้ามีการอัพเดท logical_id ต้องไม่ซ้ำกับที่มีอยู่แล้ว
    if entity.Entity_LogicalId and entity.Entity_LogicalId != existing_entity.Entity_LogicalId:
        entity_with_same_logical_id = await service.get_entity_by_logical_id(entity.Entity_LogicalId)
        if entity_with_same_logical_id:
            raise HTTPException(status_code=400, detail="Entity_LogicalId นี้มีอยู่แล้ว")
    
    updated_entity = await service.update_entity(entity_id, entity)
    if not updated_entity:
        raise HTTPException(status_code=404, detail="ไม่พบ Entity")
    
    return updated_entity

@router.delete("/{entity_id}", response_model=dict)
async def delete_entity(
    entity_id: str,
    service: EntityService = Depends()
):
    """
    ลบ Entity
    """
    # ตรวจสอบว่ามี entity_id นี้หรือไม่
    existing_entity = await service.get_entity_by_id(entity_id)
    if not existing_entity:
        raise HTTPException(status_code=404, detail="ไม่พบ Entity")
    
    success = await service.delete_entity(entity_id)
    if not success:
        raise HTTPException(status_code=500, detail="ไม่สามารถลบ Entity ได้")
    
    return {"message": "ลบ Entity สำเร็จ"}