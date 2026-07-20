from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint


def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware). Replaces deprecated utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)  # Store as naive UTC for SQLite compat


class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)


class Lead(SQLModel, table=True):
    __tablename__ = "leads"

    __table_args__ = (
        UniqueConstraint("business_name", "address", name="uq_lead_name_address"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    business_name: str = Field(index=True)
    sector: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    website_url: Optional[str] = Field(default=None)
    has_website: bool = Field(default=False)
    website_quality_score: Optional[int] = Field(default=None, ge=0, le=100)
    instagram_handle: Optional[str] = Field(default=None)
    instagram_url: Optional[str] = Field(default=None)
    instagram_bio: Optional[str] = Field(default=None)
    youtube_url: Optional[str] = Field(default=None)
    linkedin_url: Optional[str] = Field(default=None)
    tiktok_url: Optional[str] = Field(default=None)
    facebook_url: Optional[str] = Field(default=None)
    telegram_url: Optional[str] = Field(default=None)
    twitter_url: Optional[str] = Field(default=None)
    rating: Optional[float] = Field(default=None)
    review_count: Optional[int] = Field(default=None)
    source: Optional[str] = Field(default=None)  # 'osm', 'google_places', 'manual'
    status: str = Field(
        default="new", index=True
    )  # new | researched | drafted | contacted | replied | converted | rejected | do_not_contact
    discovered_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    notes: Optional[str] = Field(default=None)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id", index=True)
    session_id: Optional[int] = Field(default=1, foreign_key="user_sessions.id", index=True)

    # Technical audit / Deep Web details
    email: Optional[str] = Field(default=None)
    kvkk_compliant: Optional[bool] = Field(default=None)
    has_broken_links: Optional[bool] = Field(default=None)
    broken_links_details: Optional[str] = Field(default=None)
    page_speed_desktop: Optional[int] = Field(default=None)
    page_speed_mobile: Optional[int] = Field(default=None)
    technologies: Optional[str] = Field(default=None)

    # Lead Scoring / Prioritization
    priority_score: Optional[float] = Field(default=None)
    priority_label: Optional[str] = Field(default=None)

    # Visual Audit & Email Verification V2
    screenshot_path: Optional[str] = Field(default=None)
    visual_audit_notes: Optional[str] = Field(default=None)
    outreach_hook: Optional[str] = Field(default=None)
    email_verification_status: Optional[str] = Field(default=None)
    email_verification_details: Optional[str] = Field(default=None)

    # Relationships
    research_notes: List["ResearchNote"] = Relationship(back_populates="lead", cascade_delete=True)
    messages: List["Message"] = Relationship(back_populates="lead", cascade_delete=True)
    campaign: Optional["Campaign"] = Relationship(back_populates="leads")
    crm_logs: List["CrmLog"] = Relationship(back_populates="lead", cascade_delete=True)


class ResearchNote(SQLModel, table=True):
    __tablename__ = "research_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id", index=True)
    source: str  # 'website', 'instagram_bio', 'google_reviews', 'google_custom_search'
    content: str
    scraped_at: datetime = Field(default_factory=_utcnow)

    # Relationships
    lead: Lead = Relationship(back_populates="research_notes")


class SmtpAccount(SQLModel, table=True):
    __tablename__ = "smtp_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    smtp_host: str
    smtp_port: int = Field(default=587)
    smtp_user: str
    smtp_pass: str
    imap_host: Optional[str] = Field(default=None)
    imap_port: int = Field(default=993)
    imap_user: Optional[str] = Field(default=None)
    imap_pass: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
    last_used_at: Optional[datetime] = Field(default=None)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id", index=True)
    direction: str  # 'outbound', 'inbound'
    channel: str  # 'instagram_manual', 'instagram_auto'
    content: str
    ai_generated: bool = Field(default=False)
    status: str = Field(default="draft")  # draft, approved, sent, failed
    sent_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    smtp_account_id: Optional[int] = Field(default=None, foreign_key="smtp_accounts.id", index=True)
    message_type: str = Field(default="initial")  # initial | followup_1 | followup_2

    # Relationships
    lead: Lead = Relationship(back_populates="messages")


class Campaign(SQLModel, table=True):
    __tablename__ = "campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sector_filter: Optional[str] = Field(default=None)
    location_filter: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    session_id: Optional[int] = Field(default=1, foreign_key="user_sessions.id", index=True)

    # Follow-up sequence settings
    followup_delay_1_days: int = Field(default=3)
    followup_subject_1: Optional[str] = Field(default=None)
    followup_body_1: Optional[str] = Field(default=None)
    followup_delay_2_days: int = Field(default=7)
    followup_subject_2: Optional[str] = Field(default=None)
    followup_body_2: Optional[str] = Field(default=None)

    # Relationships
    leads: List[Lead] = Relationship(back_populates="campaign", cascade_delete=True)


class SearchPreset(SQLModel, table=True):
    __tablename__ = "search_presets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sector_query: str
    location_query: str
    radius_km: int = Field(default=10)
    provider_name: str = Field(default="all")
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    session_id: Optional[int] = Field(default=1, foreign_key="user_sessions.id", index=True)


class DiscoveryDraft(SQLModel, table=True):
    __tablename__ = "discovery_drafts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sector_query: str
    location_query: str
    radius_km: int = Field(default=10)
    provider_name: str = Field(default="all")
    country_query: Optional[str] = Field(default=None)
    city_query: Optional[str] = Field(default=None)
    region_query: Optional[str] = Field(default=None)
    keyword_query: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    session_id: Optional[int] = Field(default=1, foreign_key="user_sessions.id", index=True)


class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=_utcnow)
    action: str
    details: Optional[str] = Field(default=None)
    session_id: Optional[int] = Field(default=1, foreign_key="user_sessions.id", index=True)


class CrmLog(SQLModel, table=True):
    __tablename__ = "crm_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="leads.id", index=True)
    note: str
    created_at: datetime = Field(default_factory=_utcnow)

    # Relationships
    lead: Optional[Lead] = Relationship(back_populates="crm_logs")
