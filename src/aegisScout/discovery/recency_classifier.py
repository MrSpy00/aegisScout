"""
Multi-Signal Recency Classifier for Instagram Profiles & Posts.
Evaluates account activity recency across Turkish and English signals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RecencyResult:
    """Standardized recency classification result."""
    status_enum: str  # ACTIVE_RECENT (<=30d), ACTIVE_MODERATE (31-90d), INACTIVE (>90d or 0 posts), UNKNOWN
    human_text: str  # e.g., "Son 5 Gün İçinde Aktif"
    raw_score: int  # 0 to 100 integer score for sorting/ranking
    estimated_days: float  # Estimated days since last post
    last_post_timestamp: Optional[int]  # Unix timestamp if computable
    is_zero_post: bool  # True if 0 posts


TURKISH_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}

ENGLISH_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


class RecencyClassifier:
    """
    Parses activity signals from raw HTML, text snippets, and timestamp numbers.
    """

    @classmethod
    def classify(
        cls,
        text_or_html: str = "",
        post_count: int = -1,
        latest_timestamp: Optional[int] = None,
        reference_year: int = 2026,
    ) -> RecencyResult:
        text_or_html = str(text_or_html or "")
        now_ts = int(datetime.now(timezone.utc).timestamp())

        # Signal 0: Explicit Unix Timestamp provided
        if latest_timestamp and latest_timestamp > 0:
            diff_seconds = max(0, now_ts - latest_timestamp)
            days_ago = diff_seconds / 86400.0
            if days_ago <= 30:
                return RecencyResult(
                    status_enum="ACTIVE_RECENT",
                    human_text=f"Son {max(1, int(days_ago))} Gün İçinde Aktif",
                    raw_score=max(85, 100 - int(days_ago)),
                    estimated_days=round(days_ago, 1),
                    last_post_timestamp=latest_timestamp,
                    is_zero_post=False,
                )
            elif days_ago <= 90:
                return RecencyResult(
                    status_enum="ACTIVE_MODERATE",
                    human_text=f"Son {int(days_ago)} Gün İçinde Aktif",
                    raw_score=max(60, 84 - int((days_ago - 30) * 0.4)),
                    estimated_days=round(days_ago, 1),
                    last_post_timestamp=latest_timestamp,
                    is_zero_post=False,
                )
            else:
                return RecencyResult(
                    status_enum="INACTIVE",
                    human_text=f"{int(days_ago)} Gün Önce Aktif (Geçmiş İçerik)",
                    raw_score=max(10, 59 - int((days_ago - 90) * 0.1)),
                    estimated_days=round(days_ago, 1),
                    last_post_timestamp=latest_timestamp,
                    is_zero_post=False,
                )

        # Signal 1: Zero Post Detection
        zero_post_patterns = [
            r"gönderi\s*yok", r"0\s*gönderi", r"gönderisiz\s*hesap",
            r"no\s*posts\s*yet", r"0\s*posts", r"no\s*posts"
        ]
        is_zero = (post_count == 0) or any(re.search(pat, text_or_html, re.I) for pat in zero_post_patterns)
        if is_zero:
            return RecencyResult(
                status_enum="INACTIVE",
                human_text="Gönderisiz Hesap",
                raw_score=15,
                estimated_days=999.0,
                last_post_timestamp=None,
                is_zero_post=True,
            )

        # Signal 2: Hours / Minutes Ago (e.g. "3 saat önce", "3 hours ago", "5h")
        hours_match = re.search(r"\b(\d+)\s*(?:saat|hour|h)\s*(?:önce|ago)?\b", text_or_html, re.I)
        if hours_match:
            hours = int(hours_match.group(1))
            days_est = hours / 24.0
            return RecencyResult(
                status_enum="ACTIVE_RECENT",
                human_text=f"Son {hours} Saat İçinde Aktif",
                raw_score=99,
                estimated_days=round(days_est, 2),
                last_post_timestamp=now_ts - (hours * 3600),
                is_zero_post=False,
            )

        # Signal 3: Relative Days (e.g. "Son 5 Gün", "2 gün önce", "5 days ago", "3d")
        days_match = re.search(r"(?:son\s*)?\b(\d+)\s*(?:gün|day|d)\s*(?:içinde|içinde aktif|önce|ago)?\b", text_or_html, re.I)
        if days_match:
            days = int(days_match.group(1))
            if days <= 30:
                enum_val = "ACTIVE_RECENT"
                score = max(85, 98 - days)
            elif days <= 90:
                enum_val = "ACTIVE_MODERATE"
                score = max(60, 84 - int((days - 30) * 0.4))
            else:
                enum_val = "INACTIVE"
                score = max(20, 59 - int((days - 90) * 0.2))

            return RecencyResult(
                status_enum=enum_val,
                human_text=f"Son {days} Gün İçinde Aktif",
                raw_score=score,
                estimated_days=float(days),
                last_post_timestamp=now_ts - (days * 86400),
                is_zero_post=False,
            )

        # Signal 4: Relative Weeks (e.g. "2 hafta önce", "3 weeks ago")
        weeks_match = re.search(r"\b(\d+)\s*(?:hafta|week|w)\s*(?:önce|ago)?\b", text_or_html, re.I)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            days = weeks * 7
            enum_val = "ACTIVE_RECENT" if days <= 30 else "ACTIVE_MODERATE"
            score = max(65, 90 - (weeks * 5))
            return RecencyResult(
                status_enum=enum_val,
                human_text=f"Son {weeks} Hafta İçinde Aktif",
                raw_score=score,
                estimated_days=float(days),
                last_post_timestamp=now_ts - (days * 86400),
                is_zero_post=False,
            )

        # Signal 5: Month-Year Format (e.g. "Son İçerik: Mart 2026", "Ocak 2025", "15 March 2026")
        month_year_match = re.search(
            r"(?:son\s*içerik:\s*)?(\d{1,2})?\s*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\s*(202[4-6])",
            text_or_html, re.I
        )
        if month_year_match:
            day_str, m_str, y_str = month_year_match.groups()
            month_num = TURKISH_MONTHS.get(m_str.lower()) or ENGLISH_MONTHS.get(m_str.lower())
            if month_num:
                year_num = int(y_str)
                day_num = int(day_str) if day_str else 15
                try:
                    dt = datetime(year_num, month_num, day_num, tzinfo=timezone.utc)
                    ts = int(dt.timestamp())
                    days_ago = max(0.0, (now_ts - ts) / 86400.0)
                    if year_num == reference_year or days_ago <= 30:
                        enum_val = "ACTIVE_RECENT"
                        score = max(80, 95 - int(days_ago * 0.1))
                    elif year_num == reference_year - 1 or days_ago <= 365:
                        enum_val = "ACTIVE_MODERATE"
                        score = max(60, 80 - int(days_ago * 0.05))
                    else:
                        enum_val = "INACTIVE"
                        score = max(20, 50 - int(days_ago * 0.02))

                    return RecencyResult(
                        status_enum=enum_val,
                        human_text=f"Son İçerik: {m_str.title()} {y_str}",
                        raw_score=score,
                        estimated_days=round(days_ago, 1),
                        last_post_timestamp=ts,
                        is_zero_post=False,
                    )
                except Exception:
                    pass

        # Signal 6: Year-Only Detection
        if re.search(r"\b2026\b", text_or_html):
            return RecencyResult(
                status_enum="ACTIVE_RECENT",
                human_text="Güncel Aktif Profil (2026)",
                raw_score=90,
                estimated_days=30.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )
        elif re.search(r"\b2025\b", text_or_html):
            return RecencyResult(
                status_enum="ACTIVE_MODERATE",
                human_text="Aktif Profil (2025)",
                raw_score=80,
                estimated_days=180.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )
        elif re.search(r"\b2024\b", text_or_html):
            return RecencyResult(
                status_enum="INACTIVE",
                human_text="Geçmiş İçerikli Hesap (2024)",
                raw_score=60,
                estimated_days=500.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )

        # Default fallback
        if post_count > 0:
            return RecencyResult(
                status_enum="ACTIVE_MODERATE",
                human_text="İçerik Mevcut",
                raw_score=65,
                estimated_days=60.0,
                last_post_timestamp=None,
                is_zero_post=False,
            )

        return RecencyResult(
            status_enum="UNKNOWN",
            human_text="Profil Mevcut",
            raw_score=50,
            estimated_days=90.0,
            last_post_timestamp=None,
            is_zero_post=False,
        )
