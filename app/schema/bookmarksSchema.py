from pydantic import BaseModel

class Memory_Schema(BaseModel):
    title: str
    user_id: str
    doc_id: str
    note: str
    site_name: str
    date: str
    source_url: str
    type: str 


