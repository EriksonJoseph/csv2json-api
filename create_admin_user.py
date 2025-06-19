#!/usr/bin/env python3
"""
Create or update admin user for testing
"""
import asyncio
from app.database import get_collection
from passlib.context import CryptContext
from datetime import datetime

async def create_admin_user():
    print("🔧 Creating/updating admin user...")
    
    try:
        # Password context
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Get users collection
        users_collection = await get_collection("users")
        
        # Check if admin user exists
        admin_user = await users_collection.find_one({"username": "admin"})
        
        # Admin user data
        admin_data = {
            "username": "admin",
            "password": pwd_context.hash("@AdminPassw0rd"),
            "email": "admin@csv2json.com",
            "first_name": "Admin",
            "last_name": "User",
            "middle_name": "",
            "roles": ["admin"],
            "is_active": True,
            "is_locked": False,
            "is_verify_email": True,  # Admin is pre-verified
            "email_verification_token": None,
            "email_verification_expires": None,
            "failed_login_attempts": 0,
            "email_verification_token": None,
            "email_verification_expires": None,
            "failed_login_attempts": 0,
            "created_at": datetime.utcnow(),
            "created_by": "Root",
            "updated_at": datetime.utcnow(),
            "updated_by": "Root",
            "last_login_ip": None
        }
        
        
        if admin_user:
            # Update existing admin user
            result = await users_collection.update_one(
                {"_id": admin_user["_id"]},
                {"$set": admin_data}
            )
            
            if result.modified_count > 0:
                print("✅ Admin user updated successfully")
            else:
                print("⚠️  Admin user data unchanged")
        else:
            # Create new admin user
            result = await users_collection.insert_one(admin_data)
            if result.inserted_id:
                print("✅ Admin user created successfully")
            else:
                print("❌ Failed to create admin user")
        
        print("📋 Admin user details:")
        print("   - Username: admin")
        print("   - Password: ThisIsAdmin")
        print("   - Email verified: True")
        print("   - Account unlocked: True")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())