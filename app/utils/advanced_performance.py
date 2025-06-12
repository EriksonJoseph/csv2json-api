import time
import functools
import logging
import json
import os
from typing import Callable, Any, Dict, List, Optional
from datetime import datetime

class PerformanceTracker:
    """
    Class สำหรับติดตามประสิทธิภาพการทำงานของฟังก์ชัน
    สามารถบันทึกข้อมูลลงไฟล์ และคำนวณสถิติต่างๆ ได้
    """
    
    def __init__(self, log_file: Optional[str] = None, console_log: bool = True, 
                 alert_threshold: float = 1.0) -> None:
        """
        ตั้งค่า Performance Tracker
        
        Args:
            log_file: ชื่อไฟล์ที่ใช้บันทึกข้อมูล performance (None = ไม่บันทึกลงไฟล์)
            console_log: บันทึกข้อมูลลงใน console หรือไม่
            alert_threshold: เกณฑ์เวลาที่ใช้ (วินาที) สำหรับแจ้งเตือนว่าฟังก์ชันทำงานช้าเกินไป
        """
        self.log_file = log_file
        self.console_log = console_log
        self.alert_threshold = alert_threshold
        self.records: Dict[str, List[Dict[str, Any]]] = {}
        
        # ตั้งค่า logger
        self.logger: logging.Logger = logging.getLogger("performance_tracker")
        self.logger.setLevel(logging.INFO)
        
        # เพิ่ม console handler ถ้าต้องการ
        if console_log:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '⏱️ %(asctime)s - PERF - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # เพิ่ม file handler ถ้ากำหนดชื่อไฟล์
        if log_file:
            # สร้างโฟลเดอร์ logs ถ้ายังไม่มี
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - PERF - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def track_time(self, func_name: str, elapsed_time: float, *args, **kwargs) -> None:
        """
        บันทึกข้อมูลเวลาที่ใช้ในการทำงานของฟังก์ชัน
        
        Args:
            func_name: ชื่อฟังก์ชัน
            elapsed_time: เวลาที่ใช้ในการทำงาน (วินาที)
            args: arguments ที่ส่งให้ฟังก์ชัน
            kwargs: keyword arguments ที่ส่งให้ฟังก์ชัน
        """
        timestamp = datetime.now().isoformat()
        
        # สร้าง record ใหม่
        record = {
            "timestamp": timestamp,
            "elapsed_time": elapsed_time,
            "args": str(args)[:100] if args else None,  # ตัดให้สั้นลงเพื่อไม่ให้ log ใหญ่เกินไป
            "kwargs": str(kwargs)[:100] if kwargs else None
        }
        
        # เพิ่ม record ลงใน records
        if func_name not in self.records:
            self.records[func_name] = []
        self.records[func_name].append(record)
        
        # บันทึกข้อมูลลง log
        if elapsed_time >= self.alert_threshold:
            log_message = f"⚠️ SLOW: Function '{func_name}' took {elapsed_time:.4f} seconds to execute"
            self.logger.warning(log_message)
        else:
            log_message = f"Function '{func_name}' took {elapsed_time:.4f} seconds to execute"
            self.logger.info(log_message)
    
    def get_stats(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """
        คำนวณสถิติการทำงานของฟังก์ชัน
        
        Args:
            func_name: ชื่อฟังก์ชันที่ต้องการดูสถิติ (None = ดูทั้งหมด)
        
        Returns:
            Dict ที่มีสถิติต่างๆ
        """
        if func_name:
            if func_name not in self.records:
                return {"error": f"No records found for function '{func_name}'"}
            
            times = [record["elapsed_time"] for record in self.records[func_name]]
            return {
                "function": func_name,
                "call_count": len(times),
                "total_time": sum(times),
                "avg_time": sum(times) / len(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0
            }
        else:
            result = {}
            for func in self.records:
                times = [record["elapsed_time"] for record in self.records[func]]
                result[func] = {
                    "call_count": len(times),
                    "total_time": sum(times),
                    "avg_time": sum(times) / len(times) if times else 0,
                    "min_time": min(times) if times else 0,
                    "max_time": max(times) if times else 0
                }
            return result
    
    def export_to_json(self, output_file: str) -> None:
        """
        ส่งออกข้อมูลทั้งหมดเป็นไฟล์ JSON
        
        Args:
            output_file: ชื่อไฟล์ที่ต้องการส่งออก
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)
    
    def measure_time(self, func: Callable) -> Callable:
        """
        Decorator สำหรับวัดเวลาการทำงานของฟังก์ชัน
        
        ตัวอย่างการใช้งาน:
        @tracker.measure_time
        def my_function():
            # โค้ดของฟังก์ชัน
            pass
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            self.track_time(func.__name__, elapsed_time, *args, **kwargs)
            
            return result
        
        return wrapper
    
    def measure_async_time(self, func: Callable) -> Callable:
        """
        Decorator สำหรับวัดเวลาการทำงานของฟังก์ชัน async
        
        ตัวอย่างการใช้งาน:
        @tracker.measure_async_time
        async def my_async_function():
            # โค้ดของฟังก์ชัน async
            pass
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            self.track_time(func.__name__, elapsed_time, *args, **kwargs)
            
            return result
        
        return wrapper

# สร้าง tracker ที่ใช้งานทั่วไป
# บันทึกลงไฟล์ logs/performance.log และแสดงผลใน console
# ตั้งเกณฑ์เตือนที่ 0.5 วินาที
tracker = PerformanceTracker(
    log_file="logs/performance.log",
    console_log=True,
    alert_threshold=0.5
)

# ฟังก์ชันสำหรับวัด performance ของ code block
class TimedBlock:
    def __init__(self, name: str, tracker: PerformanceTracker = tracker) -> None:
        self.name: str = name
        self.tracker: PerformanceTracker = tracker
        self.start_time: float = 0.0  # เริ่มต้นด้วย float แทน None
    
    def __enter__(self) -> 'TimedBlock':
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # ตรวจสอบว่า start_time ถูกตั้งค่าแล้วเพื่อความปลอดภัย
        if self.start_time > 0:
            elapsed_time = time.time() - self.start_time
            self.tracker.track_time(self.name, elapsed_time)
        else:
            # กรณีไม่มีการตั้งค่า start_time (ไม่ควรเกิดขึ้น แต่ป้องกันไว้)
            self.tracker.logger.warning(f"TimedBlock '{self.name}' has invalid start_time")