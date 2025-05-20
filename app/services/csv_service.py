"""
CSV Service

ดำเนินการเกี่ยวกับไฟล์ CSV
"""
import os
import csv
from typing import Dict, List, Any
from app.repositories.csv_repository import CSVRepository
from app.utils.advanced_performance import tracker, TimedBlock
import pprint

class CSVService:
    """
    Service สำหรับจัดการ CSV
    """
    def __init__(self, repository: CSVRepository):
        self.repository = repository
    
    @tracker.measure_async_time
    async def read_and_save_csv_to_mongodb(self, file_path: str = "data/sample_100_rows.csv", batch_size: int = 1000) -> Dict[str, Any]:
        """
        อ่านไฟล์ CSV และบันทึกข้อมูลลงใน MongoDB collection "csv" แบบแบ่งชุด
        """
        try:
            # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"❌ ไม่พบไฟล์ CSV ที่ {file_path}"
                }
            
            with TimedBlock("Process CSV in Batches"):
                # ล้างข้อมูลเดิมใน collection ก่อนการบันทึกข้อมูลใหม่
                await self.repository.delete_all()
                
                # ใช้ csv.DictReader อ่านไฟล์แบบ streaming
                total_inserted = 0
                columns = []
                
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    # อ่านหัวข้อคอลัมน์
                    reader = csv.DictReader(csvfile)
                    columns = reader.fieldnames
                    
                    batch = []
                    
                    # อ่านและประมวลผลข้อมูลทีละแถว
                    for row in reader:
                        batch.append(row)
                        
                        # เมื่อครบตามขนาด batch ให้บันทึกลง MongoDB
                        if len(batch) >= batch_size:
                            if batch:
                                pprint.pp(batch[0])
                                inserted_count = await self.repository.insert_many(batch)
                                total_inserted += inserted_count
                            batch = []
                    
                    # บันทึก batch สุดท้ายที่อาจมีขนาดไม่เต็ม batch_size
                    if batch:
                        pprint.pp(batch[0])
                        inserted_count = await self.repository.insert_many(batch)
                        total_inserted += inserted_count
                        print(f"Inserted final batch: {total_inserted} total records")
            
            return {
                "success": True,
                "message": f"✅ บันทึกข้อมูล CSV ลง MongoDB สำเร็จ จำนวน {total_inserted} รายการ",
                "columns": columns,
                "total_rows": total_inserted
            }
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "message": f"❌ เกิดข้อผิดพลาดในการอ่านหรือบันทึกข้อมูล: {str(e)}"
            }
    
    @tracker.measure_async_time
    async def clear_csv_collection(self) -> Dict[str, Any]:
        """
        ล้างข้อมูลทั้งหมดใน collection "csv"
        """
        try:
            with TimedBlock("Clear CSV Collection"):
                # ดึงจำนวนเอกสารก่อนที่จะลบ
                count_before = await self.repository.count()
                
                # ล้างข้อมูลทั้งหมดใน collection
                deleted_count = await self.repository.delete_all()
            
            return {
                "success": True,
                "message": f"✅ ล้างข้อมูลใน collection csv สำเร็จ จำนวน {deleted_count} รายการ",
                "deleted_count": deleted_count,
                "previous_count": count_before
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ เกิดข้อผิดพลาดในการล้างข้อมูล: {str(e)}"
            }