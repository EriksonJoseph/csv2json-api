#!/usr/bin/env python3
"""
Detailed test script to verify the new user locking mechanism
"""
import asyncio
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:8001/api"
TEST_USERNAME = "testlock_user2"
TEST_PASSWORD = "testpassword123"
WRONG_PASSWORD = "wrongpassword"

async def get_user_info(username):
    """Get user info via admin login"""
    # Login as admin first
    admin_login = {
        "username": "admin",
        "password": "ThisIsAdmin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Get all users
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/auth/", headers=headers)
            if response.status_code == 200:
                users = response.json()["data"]
                for user in users:
                    if user["username"] == username:
                        return user
    except Exception as e:
        print(f"Error getting user info: {e}")
    
    return None

async def test_user_locking_detailed():
    print("🧪 Detailed Testing User Locking Mechanism")
    print("=" * 60)
    
    # Step 1: Clean up - delete any existing test user
    print("1. Cleaning up existing test user...")
    user_info = await get_user_info(TEST_USERNAME)
    if user_info:
        print(f"   Found existing user with failed_attempts: {user_info.get('failed_login_attempts', 0)}, locked: {user_info.get('is_locked', False)}")
    
    # Step 2: Register a test user
    print("\n2. Creating test user...")
    register_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "email": "testlock2@example.com",
        "first_name": "Test2",
        "last_name": "User2"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ Test user created successfully")
        else:
            print(f"⚠️  User might already exist: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Step 3: Test successful login first
    print("\n3. Testing successful login...")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Successful login works")
        else:
            print(f"❌ Successful login failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Error with successful login: {e}")
        return
    
    # Step 4: Test failed login attempts with detailed tracking
    print("\n4. Testing failed login attempts with detailed tracking...")
    for attempt in range(1, 8):  # Try up to 7 times
        print(f"\n   --- Attempt {attempt} ---")
        
        # Check user state before attempt
        user_info = await get_user_info(TEST_USERNAME)
        if user_info:
            print(f"   Before: failed_attempts={user_info.get('failed_login_attempts', 0)}, locked={user_info.get('is_locked', False)}")
        
        wrong_login_data = {
            "username": TEST_USERNAME,
            "password": WRONG_PASSWORD
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=wrong_login_data)
            
            print(f"   Response: {response.status_code}")
            if response.status_code == 401:
                response_data = response.json()
                detail = response_data.get("detail", "")
                print(f"   Detail: {detail}")
                
                if "locked" in detail.lower():
                    print(f"   🔒 User is now LOCKED at attempt {attempt}")
                    
                    # Check user state after locking
                    user_info = await get_user_info(TEST_USERNAME)
                    if user_info:
                        print(f"   After lock: failed_attempts={user_info.get('failed_login_attempts', 0)}, locked={user_info.get('is_locked', False)}")
                    break
            else:
                print(f"   ❓ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Check user state after attempt
        user_info = await get_user_info(TEST_USERNAME)
        if user_info:
            print(f"   After: failed_attempts={user_info.get('failed_login_attempts', 0)}, locked={user_info.get('is_locked', False)}")
    
    # Step 5: Try to login with correct password while locked
    print("\n5. Testing login with correct password while locked...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Response: {response.status_code}")
        if response.status_code == 401:
            detail = response.json().get("detail", "")
            print(f"   Detail: {detail}")
            if "locked" in detail.lower():
                print("   ✅ Correct password rejected - user is locked")
            else:
                print("   ❌ Expected locked error but got different error")
        else:
            print(f"   ❌ Expected 401 error, got: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🔚 Detailed test completed!")

if __name__ == "__main__":
    asyncio.run(test_user_locking_detailed())