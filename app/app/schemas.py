from pydantic import BaseModel

class InfoRequest(BaseModel):
    url: str
