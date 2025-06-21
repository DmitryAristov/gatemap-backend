from pydantic import BaseModel, Field

class LocationData(BaseModel):
    device_id: str = Field(..., max_length=64)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
