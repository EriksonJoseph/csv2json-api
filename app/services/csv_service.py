import pandas as pd
import os
from typing import Dict, List, Any
from app.database import get_collection
from app.utils.advanced_performance import tracker, TimedBlock

@tracker.measure_async_time
async def read_and_save_csv_to_mongodb(file_path: str = "data/sample_100_rows.csv") -> Dict[str, Any]:
    print(f"file_path: {file_path}")
    """
    อ่านไฟล์ CSV และบันทึกข้อมูลลงใน MongoDB collection "csv"
    
    Args:
        file_path: ที่อยู่ของไฟล์ CSV ที่ต้องการอ่าน
        
    Returns:
        Dictionary ที่ประกอบด้วยผลลัพธ์ของการทำงาน
    """
    try:
        print(">>>>>>>>>>>>>>>>>> 1")
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"❌ ไม่พบไฟล์ CSV ที่ {file_path}"
            }
        
        print(">>>>>>>>>>>>>>>>>> 2")
        with TimedBlock("Read CSV File"):
            # อ่านไฟล์ CSV ด้วย pandas
            print(">>>>>>>>>>>>>>>>> 2.1")
            df = pd.read_csv(file_path)
            
            print(">>>>>>>>>>>>>>>>> 2.2")
            # แปลงข้อมูลให้อยู่ในรูปแบบ list of dictionaries
            records = df.to_dict(orient='records')
            print(">>>>>>>>>>>>>>>>> 2.3")
        
        print(">>>>>>>>>>>>>>>>>> 3")
        with TimedBlock("Save to MongoDB"):
            # เชื่อมต่อกับ collection csv
            csv_collection = await get_collection("csv")
            
            # ล้างข้อมูลเดิมใน collection ก่อนการบันทึกข้อมูลใหม่
            await csv_collection.delete_many({})
            
            # บันทึกข้อมูลลงใน MongoDB
            result = await csv_collection.insert_many(records)
        
        print(">>>>>>>>>>>>>>>>>> 4")
        return {
            "success": True,
            "message": f"✅ บันทึกข้อมูล CSV ลง MongoDB สำเร็จ จำนวน {len(result.inserted_ids)} รายการ",
            "columns": df.columns.tolist(),
            "total_rows": len(records)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ เกิดข้อผิดพลาดในการอ่านหรือบันทึกข้อมูล: {str(e)}"
        }
    
@tracker.measure_async_time
async def clear_csv_collection() -> Dict[str, Any]:
    """
    ล้างข้อมูลทั้งหมดใน collection "csv"
    
    Returns:
        Dictionary ที่ประกอบด้วยผลลัพธ์ของการทำงาน
    """
    try:
        with TimedBlock("Clear CSV Collection"):
            # เชื่อมต่อกับ collection csv
            csv_collection = await get_collection("csv")
            
            # ดึงจำนวนเอกสารก่อนที่จะลบ
            count_before = await csv_collection.count_documents({})
            
            # ล้างข้อมูลทั้งหมดใน collection
            result = await csv_collection.delete_many({})
        
        return {
            "success": True,
            "message": f"✅ ล้างข้อมูลใน collection csv สำเร็จ จำนวน {result.deleted_count} รายการ",
            "deleted_count": result.deleted_count,
            "previous_count": count_before
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ เกิดข้อผิดพลาดในการล้างข้อมูล: {str(e)}"
        }