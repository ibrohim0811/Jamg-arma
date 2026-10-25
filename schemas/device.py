from pydantic import BaseModel, Field
from typing import Literal

class DeviceTokenCreate(BaseModel):
    token: str = Field(..., description="Firebase yoki APNs tokeni")
    device_type: Literal["ios", "android", "web"] = Field(..., description="Qurilma turi")

class DeviceTokenDelete(BaseModel):
    token: str