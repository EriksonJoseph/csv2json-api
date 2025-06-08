# CSV2JSON Application

## Overview

CSV2JSON is a REST API application that allows users to upload CSV files, process them to JSON format, and perform sophisticated fuzzy matching searches on the data. The application includes user authentication, file management, task processing, and a powerful matching system.

## Features

- **User Authentication**: Secure JWT-based authentication with access and refresh tokens
- **File Management**: Upload, download, and manage CSV files
- **Task Processing**: Create and monitor tasks for CSV-to-JSON conversion
- **Fuzzy Matching**: Search for names and other data using fuzzy matching algorithms
- **Background Processing**: Asynchronous task processing with background workers
- **Performance Tracking**: Detailed performance metrics for all API operations
- **Search History**: Track and review previous search operations
- **Watchlists**: Create and manage watchlists for commonly searched items

## System Flow

1. **Upload Files**: Users upload CSV files through the `/files/upload` endpoint
2. **Create Tasks**: Users create a task linked to a file using the `/task` endpoint
3. **Process Tasks**: The background worker processes the task, converting CSV to JSON
4. **Search Data**: Users can search through the processed data using single search or bulk search endpoints

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login, returns access and refresh tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout, revokes refresh tokens

### File Management
- `POST /api/files/upload` - Upload a CSV file
- `GET /api/files` - Get list of all files
- `GET /api/files/{file_id}` - Get file details
- `DELETE /api/files/{file_id}` - Delete a file
- `GET /api/files/download/{file_id}` - Download a file

### Task Management
- `POST /api/task` - Create a new task
- `GET /api/task` - Get list of all tasks
- `GET /api/task/{task_id}` - Get task details
- `PUT /api/task/{task_id}` - Update a task
- `DELETE /api/task/{task_id}` - Delete a task
- `GET /api/task/current-processing` - View currently processing task

### Matching & Search
- `GET /api/matching/columns/{task_id}` - Get available columns for matching
- `POST /api/matching/search` - Search for a single name
- `POST /api/matching/bulk-search` - Search for multiple names
- `GET /api/matching/history` - Get search history
- `GET /api/matching/stats/{task_id}` - Get statistics for a task

### Watchlists
- Endpoints for creating and managing watchlists for frequent searches

## Technical Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT-based with refresh tokens
- **Processing**: Asynchronous background workers
- **Performance**: Custom performance tracking middleware

## Installation & Setup

### 1. สร้าง Virtual environment
```zsh
python -m venv venv
```

### 2. เปิดใช้งาน Virtual environment
**Windows**
```shell
venv\Scripts\activate
```

**Mac/Linux**
```zsh
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies
```zsh
pip install -r requirements.txt
```

### 4. สร้างไฟล์ Environment
```zsh
cp .env.example .env
```

### 5. แก้ไขการตั้งค่าใน `.env` file
อัพเดทการตั้งค่าต่าง ๆ เช่น MongoDB connection string และคีย์ JWT ให้เหมาะสม

### 6. รันแอปพลิเคชัน
```zsh
uvicorn app.main:app --reload
```

## API Documentation

API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Authentication

The system uses JWT-based authentication with two types of tokens:
- **Access Token**: Short-lived (default 30 minutes)
- **Refresh Token**: Longer-lived (default 24 hours)

Refresh tokens include context like IP address and user agent for added security.

## Development

### Configuration

Configuration settings are stored in `app/config.py` and loaded from environment variables. Key settings include:
- JWT secret keys and expiration times
- MongoDB connection details
- Application settings

### Project Structure

```
csv2json-api/
├── app/
│   ├── dependencies/    # Authentication and other dependencies
│   ├── exceptions/      # Custom exception classes
│   ├── models/          # Data models
│   ├── routers/         # API endpoints organized by feature
│   ├── services/        # Business logic
│   ├── utils/           # Helper utilities
│   ├── workers/         # Background processing
│   ├── config.py        # Application configuration
│   ├── database.py      # Database connection
│   └── main.py          # Application entry point
├── data/                # Data storage
├── logs/                # Application logs
├── temp/                # Temporary file storage
├── tests/               # Test cases
├── .env                 # Environment variables
├── .env.example         # Example environment file
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Performance Tracking

The application includes performance tracking middleware that measures the execution time of all API operations. Statistics can be viewed at the `/api/performance` endpoint.

## Testing

Run tests with pytest:
```
python run_tests.py
```

## Future Improvements

- Replace in-memory refresh token storage with database storage
- Add more sophisticated matching algorithms
- Implement batch processing for large files
- Add user management features