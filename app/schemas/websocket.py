from pydantic import BaseModel
from typing import Optional

# WebSocket Message Schemas
class WSMessage(BaseModel):
    type: str
    text: Optional[str] = None
    is_typing: Optional[bool] = None