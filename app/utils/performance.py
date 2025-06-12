import time
import functools
import logging
from typing import Callable, Any, TypeVar
import asyncio

F = TypeVar('F', bound=Callable[..., Any])

# สร้าง logger สำหรับบันทึกข้อมูล performance
logger: logging.Logger = logging.getLogger("performance_tracker")

def setup_logger() -> None:
    """ตั้งค่า logger สำหรับ performance tracker"""
    handler: logging.StreamHandler = logging.StreamHandler()
    formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def measure_time(func: F) -> F:
    """
    Decorator สำหรับวัดเวลาการทำงานของฟังก์ชัน
    
    ตัวอย่างการใช้งาน:
    @measure_time
    def my_function():
        # โค้ดของฟังก์ชัน
        pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time: float = time.time()
        result: Any = func(*args, **kwargs)
        end_time: float = time.time()
        
        elapsed_time: float = end_time - start_time
        logger.info(f"Function '{func.__name__}' took {elapsed_time:.4f} seconds to execute")
        
        return result
    
    return wrapper

def measure_async_time(func: F) -> F:
    """
    Decorator สำหรับวัดเวลาการทำงานของฟังก์ชัน async
    
    ตัวอย่างการใช้งาน:
    @measure_async_time
    async def my_async_function():
        # โค้ดของฟังก์ชัน async
        pass
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time: float = time.time()
        result: Any = await func(*args, **kwargs)
        end_time: float = time.time()
        
        elapsed_time: float = end_time - start_time
        logger.info(f"Async function '{func.__name__}' took {elapsed_time:.4f} seconds to execute")
        
        return result
    
    return wrapper

# เตรียม logger เมื่อไฟล์ถูกนำเข้า
setup_logger()