from typing import List, Dict, Any
from bson import ObjectId
import json
from datetime import datetime

def list_serial(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert list of MongoDB documents to serializable format
    """
    serialized_list = []
    for item in data:
        serialized_item = item.copy()
        # Convert ObjectId to string
        if "_id" in serialized_item:
            serialized_item["_id"] = str(serialized_item["_id"])
        # Convert datetime to string
        for key, value in serialized_item.items():
            if isinstance(value, datetime):
                serialized_item[key] = value.isoformat()
        serialized_list.append(serialized_item)
    return serialized_list

def individual_serial(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert single MongoDB document to serializable format
    """
    if not data:
        return None
    
    serialized_data = data.copy()
    # Convert ObjectId to string
    if "_id" in serialized_data:
        serialized_data["_id"] = str(serialized_data["_id"])
    # Convert datetime to string
    for key, value in serialized_data.items():
        if isinstance(value, datetime):
            serialized_data[key] = value.isoformat()
    return serialized_data

class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles MongoDB ObjectId and datetime
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
