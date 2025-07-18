from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_user_route_key(request: Request) -> str:
    """
    Generate a unique key for rate limiting based on user_id and route.
    Falls back to IP address for unauthenticated requests.
    """
    # Get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)
    route_path = request.url.path
    
    if user_id:
        # For authenticated users: use user_id + route for rate limiting
        return f"user:{user_id}:route:{route_path}"
    else:
        # For unauthenticated requests: use IP + route
        client_ip = get_remote_address(request)
        return f"ip:{client_ip}:route:{route_path}"

# Initialize rate limiter with in-memory storage (no Redis)
limiter = Limiter(key_func=get_user_route_key) 