
import pandas as pd
import logging
from app.utils.advanced_performance import tracker, TimedBlock
from typing import Dict, Any, List
import pprint
import os
from app.database import get_collection
import csv

logger: logging.Logger = logging.getLogger("file")

def read_csv_file(file_path: str) -> pd.DataFrame:
    """
    Read a CSV file and return a pandas DataFrame with automatic delimiter detection
    """
    encoding = 'utf-8-sig'
    
    try:
        # ใช้ csv.Sniffer เพื่อตรวจหา delimiter
        with open(file_path, 'r', encoding=encoding) as file:
            # อ่าน sample ข้อมูลเพื่อตรวจสอบ
            sample = file.read(1024)
            file.seek(0)  # reset file pointer
            
            # ใช้ Sniffer ตรวจหา delimiter
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
        logger.info(f"Detected delimiter: '{delimiter}'")
        
        # อ่านไฟล์ด้วย delimiter ที่ตรวจพบ
        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
        
        # ตรวจสอบผลลัพธ์
        logger.info(f"Successfully read CSV with {len(df.columns)} columns and {len(df)} rows")
        
        return df
        
    except Exception as e:
        logger.error(f"Sniffer failed, trying manual detection: {str(e)}")
        
        # ถ้า Sniffer ล้มเหลว ให้ลองทุก delimiter
        delimiters = [',', ';', '\t', '|']
        best_df = None
        max_columns = 1
        
        for delimiter in delimiters:
            try:
                df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
                
                # เลือก delimiter ที่ให้ column มากที่สุด
                if len(df.columns) > max_columns:
                    max_columns = len(df.columns)
                    best_df = df
                    logger.info(f"Better result with '{delimiter}': {len(df.columns)} columns")
                    
            except Exception:
                continue
        
        if best_df is not None:
            return best_df
        else:
            raise Exception(f"Failed to read CSV file {file_path} with any delimiter")

@tracker.measure_async_time
async def read_and_save_csv_to_mongodb(file_path: str = "data/sample_100_rows.csv", batch_size: int = 1000) -> Dict[str, Any]:
    print(f"file_path: {file_path}")
    """
    อ่านไฟล์ CSV และบันทึกข้อมูลลงใน MongoDB collection "csv" แบบแบ่งชุด
    
    Args:
        file_path: ที่อยู่ของไฟล์ CSV ที่ต้องการอ่าน
        batch_size: จำนวนแถวต่อการบันทึกหนึ่งครั้ง
        
    Returns:
        Dictionary ที่ประกอบด้วยผลลัพธ์ของการทำงาน
    """
    try:
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"❌ ไม่พบไฟล์ CSV ที่ {file_path}"
            }
        
        
        with TimedBlock("Process CSV in Batches"):
            # เชื่อมต่อกับ collection csv
            csv_collection = await get_collection("csv")
            
            # ล้างข้อมูลเดิมใน collection ก่อนการบันทึกข้อมูลใหม่
            await csv_collection.delete_many({})
            
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
                            result = await csv_collection.insert_many(batch)
                            total_inserted += len(result.inserted_ids)
                        batch = []
                
                # บันทึก batch สุดท้ายที่อาจมีขนาดไม่เต็ม batch_size
                if batch:
                    pprint.pp(batch[0])
                    result = await csv_collection.insert_many(batch)
                    total_inserted += len(result.inserted_ids)
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