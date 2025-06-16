#!/usr/bin/env python3
"""
Test script to verify the new user locking mechanism
"""
import asyncio
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:8001/api"
TEST_USERNAME = "testlock_user"
TEST_PASSWORD = "testpassword123"
WRONG_PASSWORD = "wrongpassword"

async def test_user_locking():
    print("🧪 Testing User Locking Mechanism")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("1. Creating test user...")
    register_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "email": "testlock@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ Test user created successfully")
        else:
            print(f"⚠️  User might already exist: {response.status_code}")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Step 2: Test successful login first
    print("\n2. Testing successful login...")
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
    
    # Step 3: Test failed login attempts (should fail 5 times before locking)
    print("\n3. Testing failed login attempts...")
    for attempt in range(1, 7):  # Try 6 times to see locking at 5th attempt
        print(f"   Attempt {attempt}: ", end="")
        
        wrong_login_data = {
            "username": TEST_USERNAME,
            "password": WRONG_PASSWORD
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=wrong_login_data)
            
            if response.status_code == 401:
                response_data = response.json()
                if "locked" in response_data.get("detail", "").lower():
                    print(f"🔒 User is now LOCKED (attempt {attempt})")
                    locked_at_attempt = attempt
                    break
                else:
                    print(f"❌ Failed (expected - attempt {attempt})")
            else:
                print(f"❓ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Step 4: Try to login with correct password while locked
    print("\n4. Testing login with correct password while locked...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 401 and "locked" in response.json().get("detail", "").lower():
            print("✅ Correct password rejected - user is locked")
        else:
            print(f"❌ Expected locked error, got: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🔚 Test completed!")
    print("Expected behavior:")
    print("- User should be locked after 5 failed attempts")
    print("- Even correct password should be rejected when locked")
    print("- Admin can unlock using /auth/unlock/{user_id} endpoint")

if __name__ == "__main__":
    asyncio.run(test_user_locking())