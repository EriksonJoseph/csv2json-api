"""
Dependencies สำหรับ FastAPI routes
"""
from fastapi import Depends, HTTPException, status
from app.repositories.user_repository import UserRepository
from app.repositories.file_repository import FileRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.csv_repository import CSVRepository

def get_user_repository():
    """
    Returns a UserRepository instance
    """
    return UserRepository()

def get_file_repository():
    """
    Returns a FileRepository instance
    """
    return FileRepository()

def get_task_repository():
    """
    Returns a TaskRepository instance
    """
    return TaskRepository()

def get_csv_repository():
    """
    Returns a CSVRepository instance
    """
    return CSVRepository()