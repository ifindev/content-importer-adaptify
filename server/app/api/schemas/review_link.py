from datetime import datetime

from pydantic import BaseModel, Field


class ReviewLinkOut(BaseModel):
    url: str = Field(..., description="Full review link URL, built from the plaintext token.")
    created_at: datetime = Field(..., description="When this token was generated, UTC.")
