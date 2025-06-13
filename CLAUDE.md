# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

**CSV2JSON-API** is a FastAPI application that converts CSV files to JSON and provides fuzzy matching/search capabilities. The system processes uploaded CSV files into searchable data with sophisticated matching algorithms using RapidFuzz.

## Architecture Pattern

The codebase follows a **Router-Repository-Service** pattern with clear separation of concerns:

- **Routers** (`app/routers/*/`): Handle HTTP requests/responses and validation
- **Services** (`app/routers/*/`): Contain business logic and orchestration  
- **Repositories** (`app/routers/*/`): Handle database operations and data access
- **Models** (`app/routers/*/`): Define Pydantic data models for validation

Each feature module (auth, file, task, matching, user, watchlist) contains its own router, service, repository, and model files.

## Key Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies  
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development/testing
```

### Running the Application
```bash
# Development server with hot reload
uvicorn app.main:app --reload

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --unit          # Unit tests only
python run_tests.py --integration   # Integration tests only
python run_tests.py --auth          # Auth tests only
python run_tests.py --cov           # With coverage report
python run_tests.py --file tests/unit/test_auth.py  # Specific file
```

### API Documentation
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- Performance metrics: `http://localhost:8000/api/performance`

## Database Architecture

**MongoDB** with async Motor driver. Key collections:
- `users` - User accounts (unique username/email indexes)
- `files` - Uploaded CSV metadata (unique filename per user)
- `tasks` - Processing tasks linked to files
- `login_history` - Authentication tracking
- `login_attempts` - Failed login attempts for security
- Additional collections for watchlists, matching history

**Auto-initialization**: Creates admin user on startup (username: `admin`, password: `ThisIsAdmin`)

## Authentication System

**Dual JWT Token System**:
- **Access Token**: 30 minutes (for API calls)
- **Refresh Token**: 24 hours (stored in-memory, includes IP/user-agent tracking)

**Role-based Access**: `USER`, `MODERATOR`, `ADMIN` with dependency injection via `require_roles()`

## Core Processing Flow

1. **File Upload** → Temporary storage in `/temp` with metadata in `files` collection
2. **Task Creation** → Links file to processing task in `tasks` collection  
3. **Background Processing** → Worker converts CSV→JSON, updates task status
4. **Search Operations** → Fuzzy matching against processed JSON data

## Background Worker System

Async task processing in `app/workers/background_worker.py`:
- Monitors `tasks` collection for pending work
- Processes CSV files using pandas/numpy
- Updates task status and stores results
- Handles chunked file uploads for large files (>4.5MB for Vercel limits)

## Performance Tracking

Built-in performance monitoring via `app/utils/advanced_performance.py`:
- Measures execution time for all API operations
- Tracks database query performance  
- Exports metrics to JSON logs
- View stats at `/api/performance` endpoint

## Configuration Management

**Environment-based config** in `app/config.py` using Pydantic BaseSettings:
- MongoDB connection (`MONGODB_URI`, `MONGODB_DB`)
- JWT secrets and expiration times
- CORS settings (`ALLOW_ORIGIN`)
- Application settings (`APP_NAME`, `APP_ENV`, `APP_DEBUG`)

Settings are cached with `@lru_cache()` and support `.env` file loading.

## Type Safety

The codebase uses comprehensive type hints throughout:
- Function parameters and return types
- Pydantic models for request/response validation
- Async function annotations
- Database operation types using Motor's async types

## Key Dependencies

- **FastAPI 0.95.1** - Web framework
- **Motor 3.1.2** - Async MongoDB driver  
- **RapidFuzz 3.2.0** - Fuzzy string matching
- **Pandas 2.0.3** - CSV processing
- **PyMongo 4.3.3** - MongoDB operations
- **Python-jose 3.3.0** - JWT handling
- **BCrypt 4.0.1** - Password hashing

## Deployment

**Vercel Configuration** (`vercel.json`):
- Python 3.9 runtime
- 50MB Lambda size limit  
- Routes all requests to `app/main.py`

**Docker Support**: Standard Python web app containerization

## Development Notes

- API routes are prefixed with `/api`
- All database operations are async
- File uploads support both standard and chunked modes
- Search operations support single and bulk modes
- Performance tracking is enabled by default
- CORS is configured for cross-origin requests
- Request logging includes origin, user-agent, and timing data