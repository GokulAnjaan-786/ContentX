import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    details: Optional[str] = None
