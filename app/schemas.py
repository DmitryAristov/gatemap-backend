from pydantic import BaseModel

class CheckpointCreate(BaseModel):
    name: str
    latitude: float
    longitude: float

class CheckpointOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
