from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter instance using remote IP
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
