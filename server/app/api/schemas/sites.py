from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    name: str = Field(..., description="Display name for the site, e.g. the client's name.")
    wp_base_url: str = Field(
        ..., description="WordPress site base URL, e.g. https://client.example.com."
    )
    wp_username: str = Field(..., description="WordPress username for the application password.")
    wp_app_password: str = Field(
        ...,
        description="WordPress application password. Stored encrypted; never echoed back.",
    )


class SiteOut(BaseModel):
    id: str = Field(..., description="Site id.")
    name: str = Field(..., description="Display name.")
    wp_base_url: str = Field(..., description="WordPress site base URL.")


class SitesOut(BaseModel):
    sites: list[SiteOut] = Field(..., description="Every site the agency manages.")
