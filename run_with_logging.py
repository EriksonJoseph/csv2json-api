#!/usr/bin/env python3
"""
Run server with specific logging configuration
"""
import os
import sys
import argparse
from app.logging.logging_config import LOGGER_PRESETS

def main():
    parser = argparse.ArgumentParser(description="Run CSV2JSON API with specific logging")
    
    parser.add_argument(
        "--logs", 
        type=str, 
        default="minimal",
        help="Logging preset or comma-separated logger names"
    )
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host to run on"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to run on"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload"
    )
    
    parser.add_argument(
        "--list-presets", 
        action="store_true",
        help="List available logging presets"
    )
    
    args = parser.parse_args()
    
    if args.list_presets:
        print("📋 Available logging presets:")
        for preset, loggers in LOGGER_PRESETS.items():
            print(f"  {preset}: {', '.join(loggers)}")
        return
    
    # Set environment variables for logging
    if args.logs in LOGGER_PRESETS:
        os.environ["LOG_PRESET"] = args.logs
        print(f"🔍 Using preset: {args.logs} -> {LOGGER_PRESETS[args.logs]}")
    else:
        os.environ["LOG_ONLY"] = args.logs
        print(f"🔍 Using custom loggers: {args.logs}")
    
    # Import and run uvicorn
    import uvicorn
    
    print(f"🚀 Starting server on {args.host}:{args.port}")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="warning"  # Suppress uvicorn's default logging
    )

if __name__ == "__main__":
    main()