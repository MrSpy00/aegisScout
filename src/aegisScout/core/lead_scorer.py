"""
Lead Scoring Engine V2 for aegisScout (N2).
Evaluates business leads across multi-criteria weights to generate a composite quality score (0-100).
"""
from dataclasses import dataclass
from typing import Dict, Any
from aegisScout.core.models import Lead

@dataclass
class LeadScore:
    total: float
    components: Dict[str, float]
    label: str  # "Hot Lead", "Warm Lead", "Cold Lead"
    reasoning: str

def score_lead(lead: Lead) -> LeadScore:
    """Calculate multi-criteria V2 score for a given lead."""
    components = {}
    
    # 1. Has Email (15%)
    has_email_score = 15.0 if (lead.email and "@" in lead.email) else 0.0
    components["has_email"] = has_email_score

    # 2. Has Instagram (15%)
    has_ig_score = 15.0 if (lead.instagram_handle and len(lead.instagram_handle) > 1) else 0.0
    components["has_instagram"] = has_ig_score

    # 3. Website Quality (20%)
    web_score = 0.0
    if lead.website_url or lead.has_website:
        web_score += 10.0  # website exists
        if getattr(lead, "website_title", None):
            web_score += 5.0
        if getattr(lead, "technologies", None):
            web_score += 5.0
    components["website_quality"] = web_score

    # 4. Review Count (10%)
    review_score = 0.0
    if lead.review_count:
        if lead.review_count >= 50:
            review_score = 10.0
        elif lead.review_count >= 10:
            review_score = 7.0
        elif lead.review_count > 0:
            review_score = 4.0
    components["review_count"] = review_score

    # 5. Rating Score (10%)
    rating_score = 0.0
    if lead.rating:
        if lead.rating >= 4.5:
            rating_score = 10.0
        elif lead.rating >= 4.0:
            rating_score = 8.0
        elif lead.rating >= 3.0:
            rating_score = 5.0
    components["rating_score"] = rating_score

    # 6. Tech Opportunities (15%)
    tech_score = 0.0
    if lead.has_website:
        # If website has missing tech (opportunity for sales), give higher score
        opps = getattr(lead, "opportunities", None)
        if opps or "SEO" in str(opps or ""):
            tech_score = 15.0
        else:
            tech_score = 10.0
    else:
        # No website is a high web design sales opportunity
        tech_score = 15.0
    components["tech_opportunity"] = tech_score

    # 7. Phone / Reachability (15%)
    phone_score = 15.0 if lead.phone else 0.0
    components["reachability"] = phone_score

    total = sum(components.values())
    total = min(100.0, max(0.0, total))

    if total >= 75.0:
        label = "Hot Lead"
        reasoning = "Yüksek ulaşılabilirlik ve dijital dönüşüm ihtiyacı."
    elif total >= 50.0:
        label = "Warm Lead"
        reasoning = "Makul iletişim bilgileri ve dijital varlık."
    else:
        label = "Cold Lead"
        reasoning = "Eksik iletişim kanalları veya düşük sosyal varlık."

    return LeadScore(
        total=round(total, 1),
        components=components,
        label=label,
        reasoning=reasoning
    )
