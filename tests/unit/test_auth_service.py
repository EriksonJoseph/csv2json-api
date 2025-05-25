import pytest
import pytest_asyncio
from datetime import datetime, timedelta
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.user import UserCreate
from app.models.auth import UserLogin

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

@pytest.mark.asyncio
async def test_password_hashing(auth_service):
    """Test that password hashing works correctly."""
    password = "securepassword123"
    hashed = auth_service.get_password_hash(password)
    
    # Verify the hash is different from the original password
    assert hashed != password
    
    # Verify the password can be verified against the hash
    assert auth_service.verify_password(password, hashed) is True
    
    # Verify incorrect password fails
    assert auth_service.verify_password("wrongpassword", hashed) is False

@pytest.mark.asyncio
async def test_user_registration(auth_service):
    """Test user registration process."""
    user = UserCreate(
        username="newuser",
        password="password123",
        email="new@example.com",
        full_name="New User"
    )
    
    result = await auth_service.register(user)
    
    # Check that registration returns expected data
    assert "_id" in result  # MongoDB uses _id as the primary key
    assert result.get("username") == "newuser"
    assert result.get("email") == "new@example.com"
    assert "password" in result  # The actual password hash should be in the result

@pytest.mark.asyncio
async def test_user_login(auth_service, test_user):
    """Test successful user login."""
    # test_user is already awaited in the fixture
    user_data = test_user
    
    # Create login data
    login_data = UserLogin(username=user_data["username"], password="password123")
    ip_address = "127.0.0.1"
    
    # Execute login
    token = await auth_service.login(login_data, ip_address)
    
    # Check token response
    assert token.access_token is not None
    assert token.token_type == "bearer"
    assert token.expires_in == auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60

@pytest.mark.asyncio
async def test_failed_login(auth_service, test_user):
    """Test failed login with incorrect password."""
    # test_user is already awaited in the fixture
    user_data = test_user
    
    # Create login data with incorrect password
    login_data = UserLogin(username=user_data["username"], password="wrongpassword")
    ip_address = "127.0.0.1"
    
    # Attempt login with incorrect password
    from app.exceptions import UserException
    with pytest.raises(UserException) as exc_info:
        await auth_service.login(login_data, ip_address)
    
    # Check error message
    assert "Invalid username or password" in str(exc_info.value)

@pytest.mark.asyncio
async def test_login_history(auth_service, test_user, login_repository):
    """Test that login history is recorded correctly."""
    # test_user is already awaited in the fixture
    user_data = test_user
    user_id = str(user_data["_id"])
    
    # Attempt successful login
    login_data = UserLogin(username=user_data["username"], password="password123")
    ip_address = "127.0.0.1"
    token = await auth_service.login(login_data, ip_address)
    
    # Get login history from the user document
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_user_by_id(user_id)
    
    # Check that the login was recorded in the user's login_history
    assert "login_history" in user
    login_history = user["login_history"]
    
    # Get the count of successful logins (should be at least 1)
    successful_logins = [h for h in login_history if h.get("status") == "success"]
    assert len(successful_logins) >= 1
    
    # Check the most recent login
    latest_login = successful_logins[0]
    assert latest_login["ip_address"] == ip_address
    assert "login_at" in latest_login
    
    # Attempt failed login
    from app.exceptions import UserException
    with pytest.raises(UserException):
        await auth_service.login(
            UserLogin(username=user_data["username"], password="wrong"),
            ip_address
        )
    
    # Get updated user data
    user = await user_repo.get_user_by_id(user_id)
    
    # Check that both attempts are recorded in the login history
    login_history = user.get("login_history", [])
    assert len(login_history) == 2
    assert any(entry["success"] is False for entry in login_history)

@pytest.mark.asyncio
async def test_unlock_user(auth_service, test_user, login_repository):
    """Test unlocking a user account."""
    # test_user is already awaited in the fixture
    user_data = test_user
    user_id = str(user_data["_id"])
    
    # Get the user repository to check the locked status
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    
    # First, ensure the user is not locked and reset failed attempts
    await user_repo.update_user(user_id, {"$set": {
        "is_locked": False,
        "failed_login_attempts": 0,
        "locked_until": None
    }})
    
    # Lock the user by simulating failed login attempts
    for _ in range(5):  # Assuming 5 failed attempts will lock the account
        try:
            await auth_service.login(
                UserLogin(username=user_data["username"], password="wrongpassword"),
                "127.0.0.1"
            )
        except Exception:
            pass
    
    # Verify the user is locked by checking the database
    user = await user_repo.get_user_by_id(user_id)
    assert user.get("is_locked") is True
    assert user.get("failed_login_attempts", 0) >= 5  # Assuming 5 failed attempts lock the account
    
    # Unlock the user
    result = await auth_service.unlock_user(user_id)
    assert result is True
    
    # Verify the user is no longer locked
    user = await user_repo.get_user_by_id(user_id)
    assert user.get("is_locked") is False
    assert user.get("failed_login_attempts") == 0
    assert user.get("locked_until") is None
    
    # Verify the user can login again
    token = await auth_service.login(
        UserLogin(username=user_data["username"], password="password123"),
        "127.0.0.1"
    )
    assert token is not None
