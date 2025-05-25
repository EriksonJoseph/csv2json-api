from datetime import datetime
from typing import Optional, Dict
from app.models.auth import TokenData
from app.exceptions import UserException

class BaseService:
    def __init__(self, repository):
        self.repository = repository

    async def add_audit_fields(self, data: Dict, current_user: Optional[TokenData] = None, is_update: bool = False) -> Dict:
        """
        Add audit fields to the data
        """
        audit_fields = {}
        
        # Get user ID or set as worker
        user_id = "worker" if current_user is None else current_user.user_id
        
        # Add created_by and created_at for new records
        if not is_update:
            audit_fields["created_by"] = user_id
            audit_fields["created_at"] = datetime.utcnow()
        
        # Add updated_by and updated_at for all records
        audit_fields["updated_by"] = user_id
        audit_fields["updated_at"] = datetime.utcnow()
        
        return {**data, **audit_fields}

    async def create(self, data: Dict, current_user: Optional[TokenData] = None) -> Dict:
        """
        Create a new record with audit fields
        """
        data_with_audit = await self.add_audit_fields(data, current_user)
        return await self.repository.create(data_with_audit)

    async def update(self, id: str, data: Dict, current_user: Optional[TokenData] = None) -> Dict:
        """
        Update a record with audit fields
        """
        data_with_audit = await self.add_audit_fields(data, current_user, is_update=True)
        return await self.repository.update(id, data_with_audit)
