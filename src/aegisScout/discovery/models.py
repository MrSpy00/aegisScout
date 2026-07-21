from typing import Optional
from pydantic import BaseModel

class LeadCandidate(BaseModel):
    business_name: str
    sector: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website_url: Optional[str] = None
    has_website: bool = False
    website_quality_score: Optional[int] = None
    instagram_handle: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_bio: Optional[str] = None
    youtube_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    facebook_url: Optional[str] = None
    telegram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    profile_image_url: Optional[str] = None
    outreach_hook: Optional[str] = None
    source: str
