#!/usr/bin/env python3
"""
Verification test to check exactly when user gets locked
"""
import requests

# Test configuration
BASE_URL = "http://127.0.0.1:8001/api"

def get_user_details(username):
    """Get user details using admin token"""
    # Login as admin
    admin_login = {"username": "admin", "password": "ThisIsAdmin"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get all users
            response = requests.get(f"{BASE_URL}/auth/", headers=headers)
            if response.status_code == 200:
                users = response.json()["data"]
                for user in users:
                    if user["username"] == username:
                        return {
                            "failed_attempts": user.get("failed_login_attempts", 0),
                            "is_locked": user.get("is_locked", False),
                            "user_id": user.get("_id")
                        }
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def test_exact_locking():
    print("🔍 Verification: Exact User Locking Point")
    print("=" * 50)
    
    # Test with the user we know exists 
    username = "admin"
    
    user_details = get_user_details(username)
    if user_details:
        print(f"Current user state:")
        print(f"  - Failed attempts: {user_details['failed_attempts']}")
        print(f"  - Is locked: {user_details['is_locked']}")
        print(f"  - User ID: {user_details['user_id']}")
        
        # If locked, unlock the user for testing
        if user_details['is_locked']:
            print(f"\n🔓 Unlocking user for fresh test...")
            admin_login = {"username": "admin", "password": "ThisIsAdmin"}
            response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
            if response.status_code == 200:
                token = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Unlock user
                response = requests.post(f"{BASE_URL}/auth/unlock/{user_details['user_id']}", headers=headers)
                if response.status_code == 200:
                    print("✅ User unlocked successfully")
                    
                    # Check state after unlock
                    user_details = get_user_details(username)
                    if user_details:
                        print(f"After unlock:")
                        print(f"  - Failed attempts: {user_details['failed_attempts']}")
                        print(f"  - Is locked: {user_details['is_locked']}")
                else:
                    print(f"❌ Failed to unlock: {response.status_code}")
                    return
        
        # Now test exact locking behavior
        print(f"\n🧪 Testing exact lock timing...")
        for i in range(1, 7):
            # Try wrong password
            wrong_login = {"username": username, "password": "wrongpassword"}
            response = requests.post(f"{BASE_URL}/auth/login", json=wrong_login)
            
            # Check state after each attempt
            user_details = get_user_details(username)
            
            print(f"Attempt {i}:")
            print(f"  - HTTP Status: {response.status_code}")
            print(f"  - Response: {response.json().get('detail', 'N/A')}")
            print(f"  - Failed attempts count: {user_details['failed_attempts'] if user_details else 'N/A'}")
            print(f"  - Is locked: {user_details['is_locked'] if user_details else 'N/A'}")
            
            if user_details and user_details['is_locked']:
                print(f"  🔒 LOCKED after {user_details['failed_attempts']} failed attempts!")
                break
            print()
        
    else:
        print(f"❌ User {username} not found")

if __name__ == "__main__":
    test_exact_locking()