import os
import json
import pandas as pd
import logging
from typing import List, Dict, Any, Optional

logger: logging.Logger = logging.getLogger(__name__)

async def process_csv_to_json(input_path: str, output_path: str) -> bool:
    """
    Process a CSV file and convert it to JSON.
    
    Args:
        input_path: Path to the input CSV file
        output_path: Path to the output JSON file
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read CSV file
        df: pd.DataFrame = pd.read_csv(input_path)
        
        # Convert to JSON
        result: List[Dict[str, Any]] = df.to_dict(orient='records')
        
        # Ensure output directory exists
        output_dir: str = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully converted {input_path} to {output_path} with {len(result)} records")
        return True
    
    except Exception as e:
        logger.error(f"Error processing CSV to JSON: {str(e)}")
        raise
        
def validate_csv_headers(csv_content: str, expected_headers: List[str]) -> bool:
    """
    Validate that a CSV file contains the expected headers.
    
    Args:
        csv_content: The content of the CSV file as a string
        expected_headers: List of header names that should be in the CSV
        
    Returns:
        bool: True if all expected headers are present, False otherwise
    """
    try:
        # Get the first line (headers)
        lines = csv_content.strip().split('\n')
        if not lines:
            return False
            
        headers = lines[0].split(',')
        headers = [h.strip() for h in headers]
        
        # Check if all expected headers are present
        return all(header in headers for header in expected_headers)
    
    except Exception as e:
        logger.error(f"Error validating CSV headers: {str(e)}")
        return False
