import pandas as pd
import os
import json
from typing import Dict, List, Any
from datetime import datetime
from app.database import get_collection
from app.config import get_settings

settings = get_settings()

class ImportService:
    def __init__(self):
        self.collection = get_collection("entities")
    
    # นำเข้าข้อมูล CSV เข้าสู่ MongoDB
    async def import_csv(self, file_path: str) -> Dict[str, Any]:
        try:
            # อ่านไฟล์ CSV ด้วย pandas
            df = pd.read_csv(file_path)
            
            # แปลง DataFrame เป็น List ของ Dict
            records = df.to_dict('records')
            
            # เพิ่ม timestamp เข้าไปในแต่ละ record
            now = datetime.now()
            for record in records:
                record['created_at'] = now
                record['updated_at'] = now
            
            # นำเข้าข้อมูลเข้า MongoDB
            if records:
                # ใช้ upsert เพื่อป้องกันข้อมูลซ้ำ
                bulk_operations = []
                
                for record in records:
                    # ใช้ Entity_LogicalId เป็น key หลักในการ upsert
                    if 'Entity_LogicalId' in record and record['Entity_LogicalId']:
                        filter_query = {"Entity_LogicalId": record['Entity_LogicalId']}
                        update_query = {"$set": record}
                        
                        bulk_operations.append({
                            'filter': filter_query,
                            'update': update_query,
                            'upsert': True
                        })
                
                # Execute bulk operation
                if bulk_operations:
                    result = await self.collection.bulk_write([
                        {
                            'updateOne': op
                        } for op in bulk_operations
                    ])
                    
                    return {
                        "success": True,
                        "message": f"นำเข้าข้อมูลสำเร็จ: {result.upserted_count} รายการถูกเพิ่ม, {result.modified_count} รายการถูกอัพเดท",
                        "total_records": len(records),
                        "inserted": result.upserted_count,
                        "updated": result.modified_count
                    }
                
                return {
                    "success": False,
                    "message": "ไม่มีข้อมูลที่จะนำเข้า"
                }
            
            return {
                "success": False,
                "message": "ไม่พบข้อมูลในไฟล์ CSV"
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"เกิดข้อผิดพลาดในการนำเข้าข้อมูล: {str(e)}"
            }
    
    # นำเข้าข้อมูล CSV จากไฟล์ที่ส่งมาผ่าน API
    async def import_csv_file(self, file_path: str) -> Dict[str, Any]:
        return await self.import_csv(file_path)
    
    # นำเข้าข้อมูล CSV จากโฟลเดอร์ data/
    async def import_sample_data(self) -> Dict[str, Any]:
        file_path = os.path.join(os.getcwd(), "data", "sample_100_rows.csv")
        if os.path.exists(file_path):
            return await self.import_csv(file_path)
        else:
            return {
                "success": False,
                "message": f"ไม่พบไฟล์ตัวอย่างที่ {file_path}"
            }