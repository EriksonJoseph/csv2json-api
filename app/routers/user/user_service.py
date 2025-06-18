from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId # type: ignore
import secrets
from app.routers.user.user_repository import UserRepository
from app.routers.user.user_model import UserCreate, UserUpdate, ChangePasswordRequest
from app.exceptions import UserException
from app.routers.auth.auth_model import TokenData
from app.routers.email.email_service import EmailService
from app.config import get_settings

class UserService:
    def __init__(self) -> None:
        self.user_repository: UserRepository = UserRepository()
        self.email_service: EmailService = EmailService()
        self.settings = get_settings()

    async def create_user(self, user: UserCreate, user_id: str) -> Dict[str, Any]:
        """Create a new user"""
        # Check for duplicate username
        if await self.user_repository.find_by_username(user.username):
            raise UserException("Username already exists", status_code=400)
        
        # Check for duplicate email
        if await self.user_repository.find_by_email(user.email):
            raise UserException("Email already exists", status_code=400)

        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        
        # Prepare user data
        user_data = {
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "roles": user.roles if hasattr(user, 'roles') else ["user"],
            "is_verify_email": False,
            "email_verification_token": verification_token,
            "email_verification_expires": verification_expires,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Create user
        result = await self.user_repository.create(user_data, user_id)
        
        # Send verification email
        if result and user.email:
            await self.send_verification_email(user.email, verification_token, user.first_name or user.username)
        
        # Return user info with ID
        if result:
            return {
                "id": result["_id"],
                "username": result["username"],
                "email": result["email"],
                "message": "User created successfully. Please check your email to verify your account."
            }
        
        return result

    async def update_user(self, user_id: str, user_update: UserUpdate, acting_user_id: str) -> Optional[Dict[str, Any]]:
        """Update user information"""
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        # Get existing user
        existing_user = await self.user_repository.find_by_id(user_id)
        if not existing_user:
            raise UserException("User not found", status_code=404)

        # Prepare update data
        update_data = user_update.dict(exclude_unset=False)
        update_data["updated_at"] = datetime.utcnow()

        # Check for username update and validate uniqueness
        if "username" in update_data:
            if update_data["username"] != existing_user["username"]:
                existing_username = await self.user_repository.find_by_username(update_data["username"])
                if existing_username and str(existing_username["_id"]) != user_id:
                    raise UserException("Username already exists", status_code=400)

        # Update user
        result = await self.user_repository.update_user(user_id, {"$set": update_data}, acting_user_id)
        if not result:
            return None
        
        # Return the updated user data
        return await self.user_repository.find_by_id(user_id)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserException("User not found", status_code=404)
        return user

    async def get_all_users(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get all users with pagination"""
        return await self.user_repository.get_all_users(page, limit)

    async def change_password(self, user_id: str, password_request: ChangePasswordRequest, acting_user_id: str) -> Dict[str, Any]:
        """Change user password"""
        from app.routers.auth.auth_service import AuthService
        auth_service = AuthService()
        
        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise UserException("Invalid user_id format", status_code=400)

        # Get existing user with password
        existing_user = await self.user_repository.find_by_id(user_id, include_password=True)
        if not existing_user:
            raise UserException("User not found", status_code=404)

        # Verify new password and confirm password match
        if password_request.new_password != password_request.confirm_password:
            raise UserException("New password and confirm password do not match", status_code=400)

        # Verify old password
        if not auth_service.verify_password(password_request.current_password, existing_user["password"]):
            raise UserException("Current password is incorrect", status_code=400)

        # Hash new password
        new_password_hash = auth_service.get_password_hash(password_request.new_password)

        # Update password
        update_data = {
            "password": new_password_hash,
            "updated_at": datetime.utcnow()
        }

        result = await self.user_repository.update_user(user_id, {"$set": update_data}, acting_user_id)
        if not result:
            raise UserException("Failed to update password", status_code=500)

        return {"message": "Password changed successfully"}

    async def send_verification_email(self, email: str, token: str, user_name: str) -> bool:
        """Send email verification link to user"""
        try:
            # Create verification URL - you can customize this based on your frontend
            verification_url = f"{self.settings.FRONTEND_URL}/verify-email?token={token}" if hasattr(self.settings, 'FRONTEND_URL') else f"http://localhost:3000/verify-email?token={token}"
            
            subject = "Verify Your Email Address"
            
            # Plain text body
            body = f"""
Hello {user_name},

Thank you for registering! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
CSV2JSON Team
            """.strip()
            
            # HTML body
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Email Verification</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #333;">Welcome to CSV2JSON!</h2>
    
    <p>Hello {user_name},</p>
    
    <p>Thank you for registering! Please verify your email address by clicking the button below:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{verification_url}" 
           style="background-color: #007bff; color: white; padding: 12px 25px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Verify Email Address
        </a>
    </div>
    
    <p>Or copy and paste this link into your browser:</p>
    <p style="word-break: break-all; color: #666;">{verification_url}</p>
    
    <p><strong>This link will expire in 24 hours.</strong></p>
    
    <p>If you did not create an account, please ignore this email.</p>
    
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #888; font-size: 12px;">
        Best regards,<br>
        CSV2JSON Team
    </p>
</body>
</html>
            """.strip()
            
            # Send email using email service
            return await self.email_service.send_immediate_email(
                to_emails=[email],
                subject=subject,
                body=body,
                html_body=html_body,
                created_by="system"
            )
            
        except Exception as e:
            print(f"Error sending verification email: {str(e)}")
            return False
    
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify email using token"""
        try:
            # Find user by verification token
            user = await self.user_repository.find_by_verification_token(token)
            
            if not user:
                raise UserException("Invalid verification token", status_code=400)
            
            # Check if token is expired
            if user.get("email_verification_expires", datetime.utcnow()) < datetime.utcnow():
                raise UserException("Verification token has expired", status_code=400)
            
            # Check if already verified
            if user.get("is_verify_email", False):
                return {"message": "Email is already verified", "status": "already_verified"}
            
            # Update user as verified
            user_id = str(user["_id"])
            update_data = {
                "is_verify_email": True,
                "email_verification_token": None,
                "email_verification_expires": None,
                "updated_at": datetime.utcnow()
            }
            
            await self.user_repository.update_user(user_id, {"$set": update_data}, "system")
            
            return {"message": "Email verified successfully", "status": "verified"}
            
        except UserException:
            raise
        except Exception as e:
            raise UserException(f"Error verifying email: {str(e)}", status_code=500)
    
    async def resend_verification_email(self, user_id: str) -> Dict[str, Any]:
        """Resend verification email to user"""
        try:
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise UserException("User not found", status_code=404)
            
            # Check if already verified
            if user.get("is_verify_email", False):
                raise UserException("Email is already verified", status_code=400)
            
            # Generate new verification token
            verification_token = secrets.token_urlsafe(32)
            verification_expires = datetime.utcnow() + timedelta(hours=24)
            
            # Update user with new token
            update_data = {
                "email_verification_token": verification_token,
                "email_verification_expires": verification_expires,
                "updated_at": datetime.utcnow()
            }
            
            await self.user_repository.update_user(user_id, {"$set": update_data}, "system")
            
            # Send new verification email
            success = await self.send_verification_email(
                user["email"], 
                verification_token, 
                user.get("first_name") or user["username"]
            )
            
            if success:
                return {"message": "Verification email sent successfully"}
            else:
                raise UserException("Failed to send verification email", status_code=500)
                
        except UserException:
            raise
        except Exception as e:
            raise UserException(f"Error resending verification email: {str(e)}", status_code=500)
