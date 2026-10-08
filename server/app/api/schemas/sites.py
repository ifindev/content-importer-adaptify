from datetime import datetime

from pydantic import BaseModel, Field


class SiteConnectionTest(BaseModel):
    wp_base_url: str = Field(
        ..., description="WordPress site base URL, e.g. https://client.example.com."
    )
    wp_username: str = Field(..., description="WordPress username for the application password.")
    wp_app_password: str = Field(
        ...,
        description="WordPress application password. Stored encrypted; never echoed back.",
    )


class SiteCreate(SiteConnectionTest):
    name: str = Field(..., description="Display name for the site, e.g. the client's name.")


class SiteUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, description="New display name.")
    wp_base_url: str | None = Field(None, description="New WordPress site base URL.")
    wp_username: str | None = Field(None, min_length=1, description="New WordPress username.")
    wp_app_password: str | None = Field(
        None, description="New application password. Omitted or empty keeps the stored one."
    )


class SiteOut(BaseModel):
    id: str = Field(..., description="Site id.")
    name: str = Field(..., description="Display name.")
    wp_base_url: str = Field(..., description="WordPress site base URL.")
    wp_username: str = Field(..., description="WordPress username the app password belongs to.")
    connection_ok: bool = Field(..., description="Whether the last WordPress check passed.")
    connection_checked_at: datetime | None = Field(
        None, description="When WordPress was last checked, UTC."
    )


class SiteSummary(SiteOut):
    article_count: int = Field(..., description="Articles in this site.")
    needs_attention_count: int = Field(
        ..., description="Articles that are Failed or carry a sync warning."
    )


class SitesOut(BaseModel):
    sites: list[SiteSummary] = Field(..., description="Every site the agency manages.")
