from pydantic import BaseModel
from typing import Optional

class NoteSchema(BaseModel):
    title: str
    note: str
    space: Optional[str] = None 