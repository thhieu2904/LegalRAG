"""
Authentication Router - JWT Authentication with Database + ENV Fallback
Supports:
1. Database authentication (bcrypt hashed password)
2. Fallback to ENV credentials if database check fails
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import logging
import bcrypt
import psycopg2

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security config
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "legalrag-secret-key-change-in-production-123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

# HTTP Bearer for token validation
security = HTTPBearer()

# Fallback credentials from environment variables
FALLBACK_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
FALLBACK_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Database config
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "legalrag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "legalrag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "legalrag_password")

logger.info(f"🔐 Auth configured - DB: {POSTGRES_HOST}:{POSTGRES_PORT}, Fallback: {FALLBACK_USERNAME}")


# ============= MODELS =============

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str = None
    full_name: str = None


class TokenData(BaseModel):
    username: str
    user_id: str = None
    exp: datetime


# ============= DATABASE =============

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def get_admin_by_username(username: str) -> dict | None:
    """
    Get admin user from database by username
    Returns: {id, username, email, hashed_password, full_name, role, is_active, is_superuser}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, hashed_password, full_name, role, is_active, is_superuser
            FROM admin_users
            WHERE username = %s AND is_active = true
        """, (username,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return {
                "id": str(row[0]),
                "username": row[1],
                "email": row[2],
                "hashed_password": row[3],
                "full_name": row[4],
                "role": row[5],
                "is_active": row[6],
                "is_superuser": row[7]
            }
        return None
        
    except Exception as e:
        logger.warning(f"⚠️  Database query failed: {e}")
        return None


def update_login_stats(user_id: str):
    """Update last_login and login_count for user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admin_users 
            SET last_login = NOW(), login_count = login_count + 1
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to update login stats: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"❌ Password verification error: {e}")
        return False


# ============= HELPERS =============

def create_access_token(username: str, user_id: str = None) -> tuple[str, datetime]:
    """Create JWT token"""
    expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": username,
        "user_id": user_id,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return TokenData(username=username, user_id=user_id, exp=exp)
    except JWTError as e:
        logger.error(f"❌ JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ============= DEPENDENCIES =============

async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to verify JWT token in requests
    Usage: @app.get("/admin/endpoint", dependencies=[Depends(verify_admin_token)])
    """
    token = credentials.credentials
    return decode_token(token)


# ============= ENDPOINTS =============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Admin login endpoint
    
    Authentication order:
    1. Try database authentication (bcrypt)
    2. Fallback to ENV credentials if database fails
    
    Returns JWT token valid for 2 hours
    """
    user_id = None
    full_name = None
    authenticated = False
    
    # ===== TRY 1: Database Authentication =====
    admin_user = get_admin_by_username(request.username)
    
    if admin_user:
        # Found user in database, verify bcrypt password
        if verify_password(request.password, admin_user["hashed_password"]):
            authenticated = True
            user_id = admin_user["id"]
            full_name = admin_user["full_name"]
            
            # Update login stats
            update_login_stats(user_id)
            
            logger.info(f"✅ Admin logged in via DATABASE: {request.username} (ID: {user_id})")
        else:
            logger.warning(f"⚠️  Failed login - invalid password (DB): {request.username}")
    
    # ===== TRY 2: Fallback to ENV Credentials =====
    if not authenticated:
        if request.username == FALLBACK_USERNAME and request.password == FALLBACK_PASSWORD:
            authenticated = True
            user_id = "env-admin"
            full_name = "Environment Admin"
            logger.info(f"✅ Admin logged in via ENV FALLBACK: {request.username}")
        else:
            logger.warning(f"⚠️  Failed login attempt: {request.username}")
    
    # ===== REJECT IF NOT AUTHENTICATED =====
    if not authenticated:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create token
    token, expires = create_access_token(request.username, user_id)
    expires_in = int((expires - datetime.utcnow()).total_seconds())
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user_id=user_id,
        full_name=full_name
    )


@router.get("/verify")
async def verify_token(token_data: TokenData = Depends(verify_admin_token)):
    """
    Verify token is valid
    Frontend can use this to check if token is still valid
    """
    return {
        "valid": True,
        "username": token_data.username,
        "user_id": token_data.user_id,
        "expires_at": token_data.exp.isoformat()
    }


@router.post("/logout")
async def logout(token_data: TokenData = Depends(verify_admin_token)):
    """
    Logout endpoint (token invalidation handled by frontend)
    """
    logger.info(f"🚪 Admin logged out: {token_data.username}")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(token_data: TokenData = Depends(verify_admin_token)):
    """
    Get current authenticated user info
    """
    # Try to get full user info from database
    admin_user = get_admin_by_username(token_data.username)
    
    if admin_user:
        return {
            "id": admin_user["id"],
            "username": admin_user["username"],
            "email": admin_user["email"],
            "full_name": admin_user["full_name"],
            "role": admin_user["role"],
            "is_superuser": admin_user["is_superuser"]
        }
    
    # Fallback for ENV-based auth
    return {
        "id": token_data.user_id,
        "username": token_data.username,
        "email": None,
        "full_name": "Environment Admin",
        "role": "admin",
        "is_superuser": True
    }
