from pydantic import BaseModel, Field

from app.api.schemas.articles import ArticleSummary


class ArticlePaste(BaseModel):
    html: str = Field(..., description="Pasted article HTML, raw body capped at 2 MB.")


class UploadFileResult(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file.")
    ok: bool = Field(..., description="Whether this file was imported successfully.")
    article: ArticleSummary | None = Field(
        None, description="The created article, if import succeeded."
    )
    code: str | None = Field(None, description="Error code, if import failed.")
    warnings: list[str] = Field(
        [], description="Import warnings for the created article, e.g. dropped images."
    )


class UploadResponse(BaseModel):
    results: list[UploadFileResult] = Field(
        ..., description="One result per uploaded file, in request order."
    )
