#!/usr/bin/env python3
"""
Test script to verify email verification functionality
"""
import requests
import json
import time

# Test configuration
BASE_URL = "http://127.0.0.1:8002/api"
TEST_USERNAME = "testemail_user"
TEST_PASSWORD = "testpassword123"
TEST_EMAIL = "test.verification@example.com"

def get_admin_token():
    """Get admin token for API calls"""
    admin_login = {
        "username": "admin",
        "password": "ThisIsAdmin"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_email_verification_flow():
    print("🧪 Testing Email Verification Flow")
    print("=" * 50)
    
    # Step 1: Get admin token
    print("1. Getting admin token...")
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Failed to get admin token")
        return
    print("✅ Admin token obtained")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 2: Create user (should send verification email)
    print("\n2. Creating test user...")
    user_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "email": TEST_EMAIL,
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user/", json=user_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            user_id = result.get("id")
            print("✅ Test user created successfully")
            print(f"   User ID: {user_id}")
            print("   📧 Verification email should be sent")
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            print(f"   Response: {response.text}")
            if "already exists" in response.text:
                print("   ⚠️  User already exists, continuing test...")
                # Get user ID from existing user
                response = requests.get(f"{BASE_URL}/user/", headers=headers)
                if response.status_code == 200:
                    users = response.json()["list"]
                    for user in users:
                        if user["username"] == TEST_USERNAME:
                            user_id = user["_id"]
                            break
            else:
                return
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Step 3: Try to login before verification (should fail)
    print("\n3. Testing login before email verification...")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 401:
            detail = response.json().get("detail", "")
            if "verify your email" in detail.lower():
                print("✅ Login correctly blocked - email not verified")
                print(f"   Message: {detail}")
            else:
                print(f"❌ Login blocked but wrong reason: {detail}")
        else:
            print(f"❌ Expected 401 error, got: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing login: {e}")
    
    # Step 4: Test verification with invalid token
    print("\n4. Testing verification with invalid token...")
    try:
        response = requests.post(f"{BASE_URL}/user/verify-email", params={"token": "invalid_token"})
        if response.status_code == 400:
            print("✅ Invalid token correctly rejected")
        else:
            print(f"❌ Expected 400 error, got: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing invalid token: {e}")
    
    # Step 5: Simulate email verification (we don't have the actual token from email)
    print("\n5. Testing resend verification email...")
    try:
        response = requests.post(f"{BASE_URL}/user/{user_id}/resend-verification", headers=headers)
        if response.status_code == 200:
            print("✅ Verification email resent successfully")
            print("   📧 New verification email should be sent")
        else:
            print(f"❌ Failed to resend verification: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error resending verification: {e}")
    
    # Step 6: Get user info to check verification status
    print("\n6. Checking user verification status...")
    try:
        response = requests.get(f"{BASE_URL}/user/{user_id}", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            is_verified = user_info.get("is_verify_email", False)
            has_token = bool(user_info.get("email_verification_token"))
            expires = user_info.get("email_verification_expires")
            
            print(f"   Email verified: {is_verified}")
            print(f"   Has verification token: {has_token}")
            print(f"   Token expires: {expires}")
            
            if not is_verified and has_token:
                print("✅ User correctly in unverified state with token")
            else:
                print("❌ Unexpected user state")
        else:
            print(f"❌ Failed to get user info: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
    
    print("\n🔚 Email verification test completed!")
    print("\nExpected behavior:")
    print("- User creation should send verification email")
    print("- Login should be blocked until email is verified")
    print("- Admin can resend verification emails")
    print("- Verification tokens should have expiration")
    print("\nTo complete testing:")
    print("1. Check email logs for sent verification emails")
    print("2. Use actual verification token to test verification endpoint")
    print("3. Test login after successful verification")

if __name__ == "__main__":
    test_email_verification_flow()