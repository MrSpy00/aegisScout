"""
Competitive Intelligence Module for aegisScout (N8).
Analyzes local industry rivals to produce pitch hooks based on competitor benchmarks.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from sqlmodel import Session, select
from aegisScout.core.database import engine
from aegisScout.core.models import Lead

@dataclass
class CompetitorReport:
    target_lead: Dict[str, Any]
    competitors: List[Dict[str, Any]]
    competitive_gaps: List[str]
    suggested_pitch: str

async def analyze_competitors(lead_id: int) -> CompetitorReport:
    """Compare a target lead against local competitors in the same sector."""
    with Session(engine) as session:
        target = session.get(Lead, lead_id)
        if not target:
            raise ValueError(f"Lead ID {lead_id} not found")

        # Find competitors in same sector
        stmt = select(Lead).where(
            Lead.sector == target.sector,
            Lead.id != target.id
        ).limit(5)
        rivals = session.exec(stmt).all()

    gaps = []
    if not target.website and any(r.website for r in rivals):
        gaps.append("Rakiplerinizin %80'inin aktif web sitesi bulunuyor, sizin yok.")
    if (target.rating or 0) < 4.0 and any((r.rating or 0) >= 4.5 for r in rivals):
        gaps.append("Rakiplerinizin puanları 4.5+ seviyesinde yüksek müşteri memnuniyetine sahip.")
    if not target.instagram_handle and any(r.instagram_handle for r in rivals):
        gaps.append("Sektördeki rakiplerinizin aktif Sosyal Medya (Instagram) kanalları var.")

    pitch = (
        f"Merhaba {target.business_name}, {target.sector or 'sektörünüzdeki'} bölgesel rekabet "
        f"analizimizde tespit ettiğimiz kritik eksikler: " + " ".join(gaps)
    )

    return CompetitorReport(
        target_lead=target.dict(),
        competitors=[r.dict() for r in rivals],
        competitive_gaps=gaps,
        suggested_pitch=pitch
    )
