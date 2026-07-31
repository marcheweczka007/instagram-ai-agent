from pydantic import BaseModel, Field


class ProfileAnalysis(BaseModel):
    """Result of analysing an Instagram creator."""

    score: int = Field(ge=1, le=10, description="Profile quality score from 1 to 10.")

    follow: bool

    reason: str

    comment: str


class InstagramProfile(BaseModel):
    name: str
    profile_url: str
    bio: str
    followers: int
    following: int
    recent_posts: list[str]


class AnalysisResult(BaseModel):
    """Complete result of analysing a single Instagram profile.

    Bundles the scraped profile data with its scored analysis so callers
    receive both outputs from one pipeline step without pairing them manually.
    """

    profile: InstagramProfile
    analysis: ProfileAnalysis
