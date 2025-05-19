import time
import functools
import logging
from typing import Callable, Any

# สร้าง logger สำหรับบันทึกข้อมูล performance
logger = logging.getLogger("performance_tracker")

def setup_logger():
    """ตั้งค่า logger สำหรับ performance tracker"""
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def measure_time(func: Callable) -> Callable:
    """
    Decorator สำหรับวัดเวลาการทำงานของฟังก์ชัน
    
    ตัวอย่างการใช้งาน:
    @measure_time
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
        logger.info(f"Function '{func.__name__}' took {elapsed_time:.4f} seconds to execute")
        
        return result
    
    return wrapper

def measure_async_time(func: Callable) -> Callable:
    """
    Decorator สำหรับวัดเวลาการทำงานของฟังก์ชัน async
    
    ตัวอย่างการใช้งาน:
    @measure_async_time
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
        logger.info(f"Async function '{func.__name__}' took {elapsed_time:.4f} seconds to execute")
        
        return result
    
    return wrapper

# เตรียม logger เมื่อไฟล์ถูกนำเข้า
setup_logger()