from pydantic import BaseModel, Field


class ProfileAnalysis(BaseModel):
    """Result of analysing an Instagram creator."""

    score: int = Field(
        ge=1,
        le=10,
        description="Profile quality score from 1 to 10."
    )

    follow: bool

    reason: str

    comment: str