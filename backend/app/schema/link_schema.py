from pydantic import BaseModel

class Link(BaseModel):
    title: str
    note: str
    link: str
    

