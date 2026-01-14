"""
Admin Authentication Middleware
Protects admin routes with API Key + IP Whitelist
"""
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from loguru import logger
from app.core.config import admin_config

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

async def verify_admin_access(request: Request, api_key: str = None) -> bool:
    """
    Verify admin access using API key and IP whitelist
    Returns True if authorized, raises HTTPException otherwise
    """
    client_ip = request.client.host
    
    ip_whitelist = admin_config.get_ip_whitelist()
    
    if client_ip not in ip_whitelist:
        logger.warning(f"Admin access denied: IP {client_ip} not in whitelist")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: IP {client_ip} is not whitelisted"
        )
    
    if not api_key:
        api_key = request.headers.get("X-Admin-API-Key")
    
    if not api_key or api_key != admin_config.ADMIN_API_KEY:
        logger.warning(f"Admin access denied: Invalid API key from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    
    logger.info(f"Admin access granted: {client_ip}")
    return True


class AdminAuthMiddleware:
    """Middleware to protect all /admin routes"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/admin"):
            request = Request(scope, receive)
            client_ip = request.client.host
            api_key = request.headers.get("X-Admin-API-Key")
            
            ip_whitelist = admin_config.get_ip_whitelist()
            
            if client_ip not in ip_whitelist:
                logger.warning(f"Blocked admin access from {client_ip}")
                response = {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [[b"content-type", b"application/json"]],
                }
                await send(response)
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail":"Access denied: IP not whitelisted"}'
                })
                return
            
            if not api_key or api_key != admin_config.ADMIN_API_KEY:
                logger.warning(f"Invalid API key from {client_ip}")
                response = {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [[b"content-type", b"application/json"]],
                }
                await send(response)
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail":"Invalid or missing API key"}'
                })
                return
        
        await self.app(scope, receive, send)
