from typing import Literal

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
    query_sources: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Map of profile URL → search queries that found it.",
    )
    search_plan: "SearchPlan | None" = None
    queries_run: list[str] = Field(default_factory=list)
    queries_skipped: list[str] = Field(
        default_factory=list,
        description="Queries skipped because recent cached results exist.",
    )


class SearchPlan(BaseModel):
    """AI-generated multi-angle search plan for creator discovery.

    Channel-agnostic: the same plan can feed Google, Instagram, TikTok, etc.
    """

    core_themes: list[str] = Field(default_factory=list)
    adjacent_themes: list[str] = Field(default_factory=list)
    search_keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    creator_archetypes: list[str] = Field(default_factory=list)
    brand_archetypes: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(
        default_factory=list,
        description="At least 30 diverse search queries for discovery channels.",
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


class OpportunityScoreBreakdown(BaseModel):
    """Explainable components that form the Opportunity Score (0–100)."""

    brand_fit: float = Field(ge=0, le=35)
    post_freshness: float = Field(ge=0, le=20)
    comment_room: float = Field(
        ge=0,
        le=15,
        description="Higher when the post likely has fewer existing comments.",
    )
    brand_similarity: float = Field(ge=0, le=15)
    visibility_potential: float = Field(ge=0, le=15)

    @property
    def total(self) -> float:
        return round(
            self.brand_fit
            + self.post_freshness
            + self.comment_room
            + self.brand_similarity
            + self.visibility_potential,
            1,
        )


OpportunityStatus = Literal["active", "done", "skipped"]
OpportunityPriority = Literal["High", "Medium", "Low"]
MarketingImpact = Literal["Low", "Medium", "High", "Very High"]


class OpportunityTimeBreakdown(BaseModel):
    """Seconds estimated for each user action in one opportunity."""

    read_post: int = 20
    read_comments: int = 40
    choose_suggestion: int = 10
    copy_comment: int = 5
    open_instagram: int = 15
    paste_and_publish: int = 30

    @property
    def total_seconds(self) -> int:
        return (
            self.read_post
            + self.read_comments
            + self.choose_suggestion
            + self.copy_comment
            + self.open_instagram
            + self.paste_and_publish
        )


class CommentOpportunity(BaseModel):
    """One actionable comment opportunity: one creator + one post."""

    id: str
    creator_name: str
    creator_url: str
    profile_picture_url: str
    brand_fit: int = Field(ge=1, le=10)
    opportunity_score: float = Field(ge=0, le=100)
    priority: OpportunityPriority
    marketing_impact: MarketingImpact = "Medium"
    estimated_time_seconds: int = 120
    estimated_time_label: str = "~2 min"
    time_breakdown: OpportunityTimeBreakdown = Field(
        default_factory=OpportunityTimeBreakdown
    )
    post_preview: str
    post_url: str
    post_index: int = 0
    why_now: str
    score_breakdown: OpportunityScoreBreakdown
    score_explanation: str
    latest_comments: list[str] = Field(default_factory=list)
    comment_suggestions: list[str] = Field(min_length=3, max_length=3)
    estimated_existing_comments: int = 0
    status: OpportunityStatus = "active"
