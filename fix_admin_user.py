#!/usr/bin/env python3
"""
Fix admin user for testing - set as verified and unlocked
"""
import asyncio
from app.database import get_collection
from bson import ObjectId

async def fix_admin_user():
    print("🔧 Fixing admin user...")
    
    try:
        # Get users collection
        users_collection = await get_collection("users")
        
        # Find admin user
        admin_user = await users_collection.find_one({"username": "admin"})
        
        if not admin_user:
            print("❌ Admin user not found")
            return
            
        print(f"📋 Found admin user: {admin_user['username']}")
        print(f"   Current status:")
        print(f"   - is_verify_email: {admin_user.get('is_verify_email', False)}")
        print(f"   - is_locked: {admin_user.get('is_locked', False)}")
        print(f"   - failed_login_attempts: {admin_user.get('failed_login_attempts', 0)}")
        
        # Update admin user
        update_data = {
            "$set": {
                "is_verify_email": True,
                "is_locked": False,
                "failed_login_attempts": 0,
                "email_verification_token": None,
                "email_verification_expires": None
            }
        }
        
        result = await users_collection.update_one(
            {"_id": admin_user["_id"]},
            update_data
        )
        
        if result.modified_count > 0:
            print("✅ Admin user fixed successfully")
            print("   - Email verified: True")
            print("   - Account unlocked: True")
            print("   - Failed attempts reset: 0")
        else:
            print("❌ Failed to update admin user")
            
    except Exception as e:
        print(f"❌ Error fixing admin user: {e}")

if __name__ == "__main__":
    asyncio.run(fix_admin_user())