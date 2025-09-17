# schemas.py

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional

class QRCodeRequest(BaseModel):
    """
    Defines the shape of the incoming request payload for QR code generation.
    """
    # --- Existing fields ---
    shape_url: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    qr_data: str

    # --- ADD THE NEW DUMMY FIELDS HERE ---
    dotType: Optional[str] = None
    backgroundColor: Optional[str] = None
    qrColor: Optional[str] = None
    textColor: Optional[str] = None
    borderColor: Optional[str] = None
    qrVersion: Optional[int] = None
    # -------------------------------------

    @field_validator('shape_url', 'logo_url', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Converts an empty string to None before URL validation."""
        if v == "":
            return None
        return v

    class Config:
        # I've also updated the example to include the new fields
        json_schema_extra = {
            "example": {
                "shape_url": "https://res.cloudinary.com/dgmqnqthu/image/upload/v1756984795/QR_Codes-17_t4ui7d.png",
                "logo_url": "https://res.cloudinary.com/dgmqnqthu/image/upload/v1756984795/QR_Codes-21_ss1w11.png",
                "qr_data": "https://github.com/kaif-s",
                "dotType": "rounded",
                "backgroundColor": "#F5F5F5",
                "qrColor": "#292929",
                "textColor": "#1A1A1A",
                "borderColor": "#E18430",
                "qrVersion": 5
            }
        }