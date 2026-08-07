"""Shared sample brand fixtures for demos and tests."""

from __future__ import annotations

from instagram_agent.domain.models import BrandProfile


def build_jollyzu_brand() -> BrandProfile:
    """Return the sample JollyZu brand profile used in demos."""
    return BrandProfile(
        name="JollyZu",
        description=(
            "Handmade colourful upcycled bags crafted for eco-conscious "
            "creative women who love slow fashion."
        ),
        target_audience=[
            "Women 25-40",
            "Eco-conscious shoppers",
            "Creative makers and designers",
            "Slow fashion community",
        ],
        values=[
            "Sustainability",
            "Craftsmanship",
            "Circular economy",
            "Colour",
            "Creativity",
        ],
        products=[
            "Handmade colourful upcycled bags",
        ],
        tone_of_voice="Friendly, creative, and authentic",
    )
