"""
Authentication dependencies for admin endpoints
"""
from fastapi import HTTPException, Header
from .config import settings


def verify_admin_key(x_api_key: str = Header(..., description="Admin API key")):
    """
    Verify admin API key for protected endpoints
    
    Usage:
        @app.post("/admin-endpoint", dependencies=[Depends(verify_admin_key)])
    """
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Admin access required."
        )
    return True
