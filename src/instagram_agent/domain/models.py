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


class DiscoveryResult(BaseModel):
    """Structured output from Instagram profile discovery."""

    profile_urls: list[str] = Field(
        default_factory=list,
        description="Instagram profile URLs discovered for the search query.",
    )


class BrandProfile(BaseModel):
    """Brand context used to evaluate creator collaboration fit.

    Platform-agnostic: the same brand definition can score creators from
    Instagram today and TikTok / YouTube / etc. later.
    """

    name: str
    description: str
    target_audience: list[str]
    values: list[str]
    products: list[str]
    tone_of_voice: str


class ResearchAnalysis(BaseModel):
    """Brand-specific collaboration research for one creator."""

    brand_fit: int = Field(
        ge=1, le=10, description="How well the creator fits the brand."
    )
    confidence: int = Field(ge=1, le=10, description="Confidence in the assessment.")
    audience_match: str
    aesthetic_match: str
    value_alignment: str
    collaboration_potential: str
    overall_summary: str
    strengths: list[str]
    weaknesses: list[str]
    collaboration_ideas: list[str]
    first_outreach_angle: str


class BrandResearchResult(BaseModel):
    """Creator analysis plus brand-fit research for one profile."""

    profile: InstagramProfile
    analysis: ProfileAnalysis
    research: ResearchAnalysis
