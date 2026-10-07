from pydantic import BaseModel, Field


class SessionRequest(BaseModel):
    id_token: str = Field(
        ...,
        description="Firebase ID token from the client-side sign-in.",
        examples=["eyJhbGciOiJSUzI1NiIsImtpZCI6..."],
    )
