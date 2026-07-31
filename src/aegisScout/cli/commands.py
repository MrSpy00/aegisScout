import re
import json
import time
import asyncio
import httpx
from datetime import datetime, timezone
from sqlmodel import Session, select, col
from typing import List, Optional, Callable, Dict, Tuple

from aegisScout.core.database import engine
from aegisScout.core.models import Lead, ResearchNote, Message, ActivityLog
from aegisScout.core.toml_config import config_data
from aegisScout.discovery.osm_provider import OSMDiscoveryProvider
from aegisScout.discovery.google_places_provider import GooglePlacesDiscoveryProvider
from aegisScout.discovery.web_search_provider import WebSearchDiscoveryProvider
from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.web_scraper import WebScraper
from aegisScout.discovery.instagram_finder import InstagramFinder
from aegisScout.discovery.social_discovery import SocialDiscovery
from aegisScout.discovery.google_maps_scraper_provider import GoogleMapsScraperDiscoveryProvider
from aegisScout.discovery.yelp_tripadvisor_provider import YelpTripAdvisorDiscoveryProvider
from aegisScout.discovery.sahibinden_sarisayfalar_provider import SahibindenSariSayfalarDiscoveryProvider
from aegisScout.discovery.linkedin_company_provider import LinkedinCompanyDiscoveryProvider
try:
    from aegisScout.discovery.bing_search_provider import BingSearchDiscoveryProvider  # type: ignore[assignment]
    _BING_AVAILABLE = True
except ImportError:  # pragma: no cover
    BingSearchDiscoveryProvider = None  # type: ignore
    _BING_AVAILABLE = False
# (1) Register DoktorTakvimi provider — opt-in import so the file may not
# exist on older installs. The class is appended to BASE_DISCOVERY_PROVIDERS
# below and participates in the "all" / "doktortakvimi" provider_name modes.
try:
    from aegisScout.discovery.doktortakvimi_provider import DoktorTakvimiDiscoveryProvider  # type: ignore[assignment]
    _DOKTORTAKVIMI_AVAILABLE = True
except ImportError:  # pragma: no cover — optional module
    DoktorTakvimiDiscoveryProvider = None  # type: ignore
    _DOKTORTAKVIMI_AVAILABLE = False

from aegisScout.ai.provider_router import ProviderRouter
from aegisScout.ai.prompts.outreach_message import build_prompt
from aegisScout.utils.logger import get_logger
from aegisScout.utils.json_helper import extract_json

logger = get_logger("cli.commands")

# ---------------------------------------------------------------------------
# Singletons — avoid re-instantiating on every call
# ---------------------------------------------------------------------------
_ai_router: Optional[ProviderRouter] = None
_scraper: Optional[WebScraper] = None
_insta_finder: Optional[InstagramFinder] = None
_social_discovery: Optional[SocialDiscovery] = None


def _get_ai_router() -> ProviderRouter:
    global _ai_router
    if _ai_router is None:
        _ai_router = ProviderRouter()
    return _ai_router


def _get_scraper() -> WebScraper:
    global _scraper
    if _scraper is None:
        _scraper = WebScraper()
    return _scraper


def _get_insta_finder() -> InstagramFinder:
    global _insta_finder
    if _insta_finder is None:
        _insta_finder = InstagramFinder()
    return _insta_finder


def _get_social_discovery() -> SocialDiscovery:
    global _social_discovery
    if _social_discovery is None:
        _social_discovery = SocialDiscovery()
    return _social_discovery


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _safe_dm_fallback(business_name: str, sector: Optional[str]) -> str:
    """Deterministic Turkish DM used when AI generation fails or returns empty."""
    first = (business_name or "İşletme").split()[0]
    sec = sector or "bu sektör"
    return (
        f"Merhaba {first}, {sec} alanındaki son çalışmalarınızı ilgiyle takip ediyorum."
    )


def _split_multi_value(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[\n,;]", str(value)) if part.strip()]


# ---------------------------------------------------------------------------
# (1) Provider registry — keeps "all" mode + name-based dispatch in one place.
# New keyless providers are appended here. Providers needing an API key
# (e.g. Google Places) are kept out of this list and added conditionally.
# ---------------------------------------------------------------------------
from aegisScout.discovery.doktorsitesi_provider import DoktorSitesiDiscoveryProvider
from aegisScout.discovery.serpapi_provider import SerpApiMapsDiscoveryProvider, SerpApiLocalPackDiscoveryProvider
from aegisScout.discovery.photon_provider import PhotonDiscoveryProvider

# —— New Turkish OSINT directory providers ————————————————————————
try:
    from aegisScout.discovery.bulurum_provider import BulurumDiscoveryProvider
    _BULURUM_AVAILABLE = True
except ImportError:
    BulurumDiscoveryProvider = None  # type: ignore
    _BULURUM_AVAILABLE = False

try:
    from aegisScout.discovery.haritane_provider import HaritaneDiscoveryProvider
    _HARITANE_AVAILABLE = True
except ImportError:
    HaritaneDiscoveryProvider = None  # type: ignore
    _HARITANE_AVAILABLE = False

try:
    from aegisScout.discovery.tikla_provider import TiklaDiscoveryProvider
    _TIKLA_AVAILABLE = True
except ImportError:
    TiklaDiscoveryProvider = None  # type: ignore
    _TIKLA_AVAILABLE = False

try:
    from aegisScout.discovery.findcomtr_provider import FindComTrDiscoveryProvider
    _FINDCOMTR_AVAILABLE = True
except ImportError:
    FindComTrDiscoveryProvider = None  # type: ignore
    _FINDCOMTR_AVAILABLE = False

from aegisScout.discovery.social_media_provider import SocialMediaDiscoveryProvider
try:
    from aegisScout.discovery.bing_search_provider import BingSearchDiscoveryProvider  # type: ignore[assignment]
    _BING_AVAILABLE = True
except ImportError:  # pragma: no cover
    BingSearchDiscoveryProvider = None  # type: ignore
    _BING_AVAILABLE = False

BASE_DISCOVERY_PROVIDERS: list[tuple[str, type]] = [
    ("photon", PhotonDiscoveryProvider),
    ("osm", OSMDiscoveryProvider),
    ("web_search", WebSearchDiscoveryProvider),
    ("social_media", SocialMediaDiscoveryProvider),
    ("serpapi_maps", SerpApiMapsDiscoveryProvider),
    ("serpapi_local", SerpApiLocalPackDiscoveryProvider),
    ("doktorsitesi", DoktorSitesiDiscoveryProvider),
    ("google_maps_scraper", GoogleMapsScraperDiscoveryProvider),
    ("yelp_tripadvisor", YelpTripAdvisorDiscoveryProvider),
    ("sahibinden_sarisayfalar", SahibindenSariSayfalarDiscoveryProvider),
    ("linkedin_company", LinkedinCompanyDiscoveryProvider),
]
if _BING_AVAILABLE and BingSearchDiscoveryProvider is not None:
    BASE_DISCOVERY_PROVIDERS.append(("bing_search", BingSearchDiscoveryProvider))
else:
    logger.info("Bing search provider not available; skipping registration.")
if _DOKTORTAKVIMI_AVAILABLE and DoktorTakvimiDiscoveryProvider is not None:
    BASE_DISCOVERY_PROVIDERS.append(("doktortakvimi", DoktorTakvimiDiscoveryProvider))
else:
    logger.info("DoktorTakvimi provider not available; skipping registration.")
if _BULURUM_AVAILABLE and BulurumDiscoveryProvider is not None:
    BASE_DISCOVERY_PROVIDERS.append(("bulurum", BulurumDiscoveryProvider))
    logger.info("Bulurum.com provider registered.")
if _HARITANE_AVAILABLE and HaritaneDiscoveryProvider is not None:
    BASE_DISCOVERY_PROVIDERS.append(("haritane", HaritaneDiscoveryProvider))
    logger.info("Haritane.com provider registered.")
if _TIKLA_AVAILABLE and TiklaDiscoveryProvider is not None:
    BASE_DISCOVERY_PROVIDERS.append(("tikla", TiklaDiscoveryProvider))
    logger.info("Tikla.com.tr provider registered.")
try:
    from aegisScout.discovery.sitelike_provider import SitelikeDiscoveryProvider
    _SITELIKE_AVAILABLE = True
except ImportError:
    SitelikeDiscoveryProvider = None  # type: ignore
    _SITELIKE_AVAILABLE = False

if _SITELIKE_AVAILABLE and SitelikeDiscoveryProvider is not None:
    BASE_DISCOVERY_PROVIDERS.append(("sitelike", SitelikeDiscoveryProvider))
    logger.info("Sitelike.org provider registered.")

# Convenience group: all Turkish directory providers in one shot
TURKEY_DIRECTORY_PROVIDERS = ["bulurum", "haritane", "tikla", "findcomtr", "doktortakvimi", "doktorsitesi", "sahibinden_sarisayfalar", "sitelike"]



# ---------------------------------------------------------------------------
# Helpers shared by discover_leads + research_lead
# ---------------------------------------------------------------------------

# (2) Multi-word search tuning. When a sector phrase (e.g. "diş hekimi")
# returns fewer than this many results, fall back to per-word searches and
# merge — protects against providers that collapse multi-word queries into
# junk aggregate pages like "en iyi 50 diş hekimi listesi".
LOW_RESULT_THRESHOLD = 3

# (3) Aggregate / ranking / "top 10" pages are NOT specific businesses.
# Common Turkish + English patterns that signal listicle junk.
# Covers: "en iyi 50 psikolog", "top 10 doktor", "istanbul psikolog listesi",
# "önerilen terapistler", "rehberi", blog/article pages, comparison pages, etc.
_AGGREGATE_PATTERNS = re.compile(
    r"\b("
    r"en\s+iyi|en\s+ucuz|en\s+iyi\s+\d+|top\s+\d+|top\s+rated|top\s+list|"
    r"\d+\s+en\s+iyi|\d+\s+top|"
    r"sıralama|sıralaması|sıralandı|"
    r"önerilen|öneriler|tavsiye|tavsiyeler|"
    r"liste|listesi|listeler|"
    r"best|recommended|ranking|rankings|"
    r"rehberi|rehber|guide|directory|dizin|"
    r"nerede\s+bul|nasıl\s+bul|hangi\s+\w+\s+seç|"
    r"\w+\s+fiyatları|\w+\s+ücretleri|\w+\s+maliyeti|"
    r"karşılaştırma|compare|comparison|"
    r"blog|makale|yazı|haber|article|news"
    r")\b",
    re.IGNORECASE,
)

# Words too short to be useful as standalone search terms (conjunctions,
# articles). Used by _extract_sector_keywords.
_MIN_SECTOR_WORD_LEN = 3


def _is_aggregate_or_ranking(candidate) -> bool:
    """Return True if the candidate looks like a list/ranking page or a directory listing, not a real business."""
    from aegisScout.discovery.noise_filter import is_directory_url
    url = getattr(candidate, "website_url", "") or ""
    if url and is_directory_url(url):
        return True
    haystack = f"{candidate.business_name} {candidate.address or ''}"
    return bool(_AGGREGATE_PATTERNS.search(haystack))


def _extract_sector_keywords(sector: str) -> list[str]:
    """Split a sector phrase into individual searchable keywords (filtering stopwords)."""
    if not sector:
        return []
    return [w for w in sector.split() if len(w) >= _MIN_SECTOR_WORD_LEN]


def _dedupe_candidates(candidates) -> list:
    """Dedupe a list of LeadCandidate by (business_name, address). Order preserved."""
    seen: set = set()
    out: list = []
    for c in candidates:
        key = (
            (c.business_name or "").strip().lower(),
            (c.address or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


# (4) Instagram bio extraction — try multiple HTML meta sources in order
# because Instagram's server-rendered HTML varies by locale/account state.
_IG_BIO_META_DESCRIPTION = re.compile(
    r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^\'\"]+)["\']',
    re.IGNORECASE,
)
_IG_BIO_OG_DESCRIPTION = re.compile(
    r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^\'\"]+)["\']',
    re.IGNORECASE,
)
_IG_BIO_TWITTER_DESCRIPTION = re.compile(
    r'<meta[^>]*name=["\']twitter:description["\'][^>]*content=["\']([^\'\"]+)["\']',
    re.IGNORECASE,
)
_IG_BIO_LD_JSON = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def _find_description_in_jsonld(obj) -> Optional[str]:
    """Recursively find a string 'description' field in a parsed JSON-LD object."""
    if isinstance(obj, dict):
        desc = obj.get("description")
        if isinstance(desc, str) and desc.strip():
            return desc
        for v in obj.values():
            found = _find_description_in_jsonld(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_description_in_jsonld(item)
            if found:
                return found
    return None


def _extract_instagram_bio(html: str) -> str:
    """Pull the Instagram bio string from raw page HTML using fallback strategies:
      1. <meta name="description" content="...">       (standard)
      2. <meta property="og:description" content="..."> (Open Graph)
      3. <meta name="twitter:description" content="..."> (Twitter cards)
      4. JSON-LD <script type="application/ld+json"> with "description"
    Returns the first non-empty match, stripped.
    """
    if not html:
        return ""
    for pattern in (
        _IG_BIO_META_DESCRIPTION,
        _IG_BIO_OG_DESCRIPTION,
        _IG_BIO_TWITTER_DESCRIPTION,
    ):
        m = pattern.search(html)
        if m:
            return m.group(1).strip()
    for ld_match in _IG_BIO_LD_JSON.finditer(html):
        try:
            data = json.loads(ld_match.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        desc = _find_description_in_jsonld(data)
        if desc:
            return desc.strip()
    return ""


# ---------------------------------------------------------------------------
# Lead Discovery
# ---------------------------------------------------------------------------

async def discover_leads(
    sector: str,
    location: str,
    radius_km: int,
    provider_name: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    session_id: int = 1,
    task_id: Optional[str] = None,
    **kwargs
) -> Tuple[int, int, int]:
    """
    Discover leads using the selected provider, deduplicate, and save to DB.
    Returns the number of newly added leads.
    """
    tqm = None
    if task_id:
        from aegisScout.core.task_queue import TaskQueueManager
        tqm = TaskQueueManager.get_instance()

    def _cb(msg: str) -> None:
        logger.info(msg)
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass

    _cb(f"Başlatılıyor: Sektör='{sector}', Konum='{location}', Yarıçap={radius_km}km, Sağlayıcı='{provider_name}'...")

    # (1) Build the provider list from BASE_DISCOVERY_PROVIDERS so newly
    # registered providers (e.g. DoktorTakvimi) automatically participate
    # in both "all" mode and name-based dispatch — no edit needed here.
    p_name_lower = provider_name.lower().strip()
    base_by_name = dict(BASE_DISCOVERY_PROVIDERS)
    providers: list[tuple[str, BaseDiscoveryProvider]] = []

    def _instantiate(name: str, cls: type) -> None:
        try:
            providers.append((name, cls()))
        except Exception as e:  # pragma: no cover — defensive
            logger.warning(f"Provider '{name}' init failed: {e}")

    if p_name_lower == "all":
        for name, cls in BASE_DISCOVERY_PROVIDERS:
            _instantiate(name, cls)
        # Google Places is optional (requires API key) — not in the base registry.
        gp = GooglePlacesDiscoveryProvider()
        if gp.api_key:
            providers.append(("google_places", gp))
        else:
            logger.info("Google Places API key is empty. Skipping it in 'all' search.")
    else:
        matched = False
        for name, cls in BASE_DISCOVERY_PROVIDERS:
            if p_name_lower == name:
                _instantiate(name, cls)
                matched = True
                break
        if not matched and p_name_lower == "google_places":
            providers.append(("google_places", GooglePlacesDiscoveryProvider()))
        if not providers:
            # Default fallback to OSM (always present in the registry).
            osm_cls = base_by_name.get("osm")
            if osm_cls is not None:
                _instantiate("osm", osm_cls)
            else:  # pragma: no cover — registry is never empty
                logger.error("OSM provider missing from BASE_DISCOVERY_PROVIDERS registry.")

    # Support multiple comma-separated sectors and locations
    sectors = _split_multi_value(sector) or [sector]
    parsed_locations = _split_multi_value(location) or ([location] if location else ["Türkiye"])

    _BROAD_LOCATIONS = {"türkiye", "turkey", "tr", "tüm türkiye", "türkiye geneli", "all turkey", "hepsi"}
    locations: list[str] = []
    for loc_item in parsed_locations:
        if str(loc_item).strip().lower() in _BROAD_LOCATIONS:
            # Expand country-wide search into major metropolitan areas for maximum lead yield
            locations.extend(["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep", "Kocaeli", "Kayseri"])
        else:
            locations.append(loc_item)
    # Deduplicate expanded locations preserving order
    seen_locs: set = set()
    locations = [l for l in locations if not (l.lower() in seen_locs or seen_locs.add(l.lower()))]

    candidates = []
    # Track per-provider progress for real-time reporting
    completed_providers = 0
    total_provider_runs = 0  # Will be counted after building the full list

    for idx_l, loc in enumerate(locations):
        for idx_s, sec in enumerate(sectors):
            # (2) Pre-compute per-keyword fallback list for multi-word sectors.
            # Only used when the full-phrase search returns too few hits.
            keywords = _extract_sector_keywords(sec) if sec else []
            full_phrase_lower = sec.lower() if sec else ""
            for name, provider in providers:
                total_provider_runs += 1

    completed_providers = 0
    candidates = []
    for idx_l, loc in enumerate(locations):
        for idx_s, sec in enumerate(sectors):
            # (2) Pre-compute per-keyword fallback list for multi-word sectors.
            # Only used when the full-phrase search returns too few hits.
            keywords = _extract_sector_keywords(sec) if sec else []
            full_phrase_lower = sec.lower() if sec else ""
            for prov_idx, (name, provider) in enumerate(providers):
                if tqm and task_id:
                    await tqm.wait_if_paused(task_id)

                # Real-time progress: start of provider
                pct_start = int(5 + (completed_providers / max(1, total_provider_runs)) * 75)
                _cb(json.dumps({
                    "progress": pct_start,
                    "message": (
                        f"'{name}' kaynağında '{sec}' aranıyor "
                        f"({idx_s + 1}/{len(sectors)} sektör, {idx_l + 1}/{len(locations)} konum)..."
                    )
                }))
                try:
                    # Strategy A: full phrase (existing behavior).
                    sec_candidates = await provider.search(sec, loc, radius_km)
                    # Strategy B: for 2+ word sectors, if the full phrase returns
                    # too few results, try each keyword individually and merge.
                    # This rescues queries like "diş hekimi" or "psikolog" that
                    # get bucketed into "en iyi 50 ..." listicles instead of
                    # returning real businesses.
                    if len(keywords) >= 2 and len(sec_candidates) < LOW_RESULT_THRESHOLD:
                        _cb(json.dumps({
                            "progress": pct_start,
                            "message": (
                                f"  '{sec}' için sonuç yetersiz ({len(sec_candidates)}<{LOW_RESULT_THRESHOLD}). "
                                f"Kelime kelime deneniyor: {', '.join(keywords)}"
                            )
                        }))
                        for word in keywords:
                            if word.lower() == full_phrase_lower:
                                continue
                            try:
                                word_candidates = await provider.search(word, loc, radius_km)
                                sec_candidates.extend(word_candidates)
                            except Exception as we:
                                logger.warning(
                                    f"Per-word search failed for '{word}' in '{loc}': {we}"
                                )
                    sec_candidates = _dedupe_candidates(sec_candidates)
                    candidates.extend(sec_candidates)

                    # Real-time progress: provider done
                    completed_providers += 1
                    pct_done = int(5 + (completed_providers / max(1, total_provider_runs)) * 75)
                    _cb(json.dumps({
                        "progress": pct_done,
                        "message": f"'{name}' tamamlandı: {len(sec_candidates)} aday bulundu."
                    }))
                except Exception as e:
                    completed_providers += 1
                    logger.error(f"Error searching sector '{sec}' in '{loc}' with '{name}': {e}")
                    _cb(json.dumps({
                        "progress": int(5 + (completed_providers / max(1, total_provider_runs)) * 75),
                        "message": f"[HATA] '{name}' kaynağından '{sec}' ('{loc}') aranırken hata: {str(e)[:80]}"
                    }))


    # (3) Drop aggregate / ranking / "top 10" list pages — those are not
    # real businesses and would pollute the lead pipeline.
    pre_filter_count = len(candidates)
    candidates = [c for c in candidates if not _is_aggregate_or_ranking(c)]
    dropped = pre_filter_count - len(candidates)
    if dropped:
        _cb(json.dumps({
            "progress": 82,
            "message": f"{dropped} aday toplu/sıralama sayfası olarak filtrelendi (en iyi / top 10 / list vb.)."
        }))

    _cb(json.dumps({
        "progress": 85,
        "message": f"Tarama bitti. {len(candidates)} aday veritabanı ile karşılaştırılıyor (Tekilleştirme)..."
    }))


    added_count = 0
    duplicate_count = 0
    with Session(engine) as session:
        total_cand = len(candidates)
        for idx, c in enumerate(candidates):
            if tqm and task_id:
                await tqm.wait_if_paused(task_id)
                tqm.update_progress(task_id, 85.0 + (idx / max(1, total_cand)) * 13.0)
            # Progress update every 50 leads
            if idx % 50 == 0 and idx > 0:
                pct = int(85 + (idx / max(1, total_cand)) * 13)
                _cb(json.dumps({"progress": pct, "message": f"DB kontrol: {idx}/{total_cand} aday işlendi..."}))

            # Deduplication: prefer place_id (Google), fallback to name+address
            place_id_val = getattr(c, '_place_id', None)
            if place_id_val:
                stmt = select(Lead).where(
                    (Lead.place_id == place_id_val) &
                    (Lead.session_id == session_id)
                )
                if session.exec(stmt).first():
                    duplicate_count += 1
                    continue
            elif c.address:
                stmt = select(Lead).where(
                    (Lead.business_name == c.business_name) &
                    (Lead.address == c.address) &
                    (Lead.session_id == session_id)
                )
                if session.exec(stmt).first():
                    duplicate_count += 1
                    continue
            else:
                stmt = select(Lead).where(
                    Lead.business_name == c.business_name,
                    col(Lead.address).is_(None),
                    Lead.session_id == session_id
                )
                if session.exec(stmt).first():
                    duplicate_count += 1
                    continue

            lead = Lead(
                business_name=c.business_name,
                sector=c.sector,
                phone=c.phone,
                email=getattr(c, 'email', None),
                address=c.address,
                website_url=c.website_url,
                has_website=c.has_website,
                instagram_handle=c.instagram_handle,
                instagram_url=c.instagram_url,
                instagram_bio=getattr(c, 'instagram_bio', None),
                profile_image_url=getattr(c, 'profile_image_url', None),
                youtube_url=getattr(c, 'youtube_url', None),
                linkedin_url=getattr(c, 'linkedin_url', None),
                tiktok_url=getattr(c, 'tiktok_url', None),
                facebook_url=getattr(c, 'facebook_url', None),
                telegram_url=getattr(c, 'telegram_url', None),
                twitter_url=getattr(c, 'twitter_url', None),
                github_url=getattr(c, 'github_url', None),
                whatsapp_url=getattr(c, 'whatsapp_url', None),
                osint_data=getattr(c, '_osint_data', None) if isinstance(getattr(c, '_osint_data', None), str) else (json.dumps(getattr(c, '_osint_data', {})) if getattr(c, '_osint_data', None) else None),
                rating=c.rating,
                review_count=c.review_count,
                source=c.source,
                status="new",
                session_id=session_id,
                # Extended metadata from enriched providers
                place_id=getattr(c, '_place_id', None),
                lat=getattr(c, '_lat', None),
                lon=getattr(c, '_lon', None),
                reviews_json=getattr(c, '_reviews_json', None),
            )
            session.add(lead)
            added_count += 1

         # Log search results summary
        log_details = (
            f"Discovered {added_count} new leads (skipped {duplicate_count} duplicates) "
            f"out of {len(candidates)} candidates for sector='{sector}', location='{location}' via '{provider_name}'"
        )
        log = ActivityLog(
            action="discover",
            details=log_details,
            session_id=session_id,
        )
        session.add(log)

        try:
            session.commit()
            _cb(json.dumps({
                "progress": 100,
                "message": (
                    f"İşlem tamamlandı. Toplam {len(candidates)} adaydan "
                    f"{duplicate_count} tanesi zaten kayıtlıydı. "
                    f"{added_count} yeni potansiyel müşteri veritabanına kaydedildi."
                )
            }))
        except Exception as e:
            session.rollback()
            logger.error(f"Error committing leads: {e}")
            _cb(json.dumps({
                "progress": 0,
                "message": f"Veritabanı kayıt hatası: {e}"
            }))
            added_count = 0

    return added_count, len(candidates), duplicate_count


# ---------------------------------------------------------------------------
# Lead Research
# ---------------------------------------------------------------------------

async def research_lead(lead_id: int, force: bool = False, task_id: Optional[str] = None, **kwargs) -> None:
    """
    Research a specific lead:
      1. Scrape website (quality score, phone, Instagram handle)
      2. Search Instagram handle via Google Custom Search / DuckDuckGo if missing
      3. Scrape Instagram bio (best-effort, non-blocking)
      4. Generate AI outreach message draft

    Skips if status='researched' and force=False.
    """
    tqm = None
    if task_id:
        from aegisScout.core.task_queue import TaskQueueManager
        tqm = TaskQueueManager.get_instance()

    scraper = _get_scraper()
    insta_finder = _get_insta_finder()
    social_discovery = _get_social_discovery()
    ai_router = _get_ai_router()

    # Language/tone from config.toml
    outreach_cfg = config_data.get("outreach", {})
    language = outreach_cfg.get("language", "tr")
    tone = outreach_cfg.get("tone", "warm")

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            logger.warning(f"Lead ID {lead_id} not found.")
            return

        if lead.status == "researched" and not force:
            logger.info(f"Lead '{lead.business_name}' (ID:{lead_id}) zaten araştırılmış. --force kullanın.")
            return

        # (5) Normalize has_website from the actual website_url — some
        # provider results set has_website=False while still shipping a
        # URL, which would otherwise leave the lead mis-categorized.
        if lead.website_url and not lead.has_website:
            lead.has_website = True

        logger.info(f"Researching lead: {lead.business_name} (ID:{lead_id})...")
        if tqm and task_id:
            await tqm.wait_if_paused(task_id)
            tqm.update_progress(task_id, 15.0)

        # 1. Scrape website
        scraped_handle: Optional[str] = None
        scraped_phone: Optional[str] = None
        quality_score: Optional[int] = None
        website_notes: str = ""
        opportunities_text: str = ""
        is_new_domain: bool = False

        if lead.website_url:
            logger.info(f"Scraping website: {lead.website_url}...")
            try:
                audit = await scraper.audit_site(lead.website_url)
                scraped_handle = audit["instagram_handle"]
                scraped_phone = audit["phone"]
                quality_score = audit["quality_score"]
                website_notes = audit["notes"]
                opportunities_text = audit.get("opportunities", "")
                is_new_domain = audit.get("is_new_domain", False)
                
                # Persist technical audit details
                lead.email = audit["email"]
                lead.kvkk_compliant = audit["kvkk_compliant"]
                lead.has_broken_links = audit["has_broken_links"]
                lead.broken_links_details = audit["broken_links_details"]
                lead.page_speed_desktop = audit["page_speed_desktop"]
                lead.page_speed_mobile = audit["page_speed_mobile"]
                lead.technologies = audit["technologies"]
            except Exception as e:
                logger.warning(f"Website scrape failed for {lead.website_url}: {e}")

            note = ResearchNote(
                lead_id=lead.id,
                source="website",
                content=f"Quality Score: {quality_score}/100. Notes: {website_notes}",
            )
            session.add(note)

            if scraped_handle and not lead.instagram_handle:
                lead.instagram_handle = scraped_handle
                lead.instagram_url = f"https://instagram.com/{scraped_handle}"
            if scraped_phone and not lead.phone:
                lead.phone = scraped_phone
            if quality_score is not None:
                lead.website_quality_score = quality_score

        if tqm and task_id:
            await tqm.wait_if_paused(task_id)
            tqm.update_progress(task_id, 45.0)

        # 2. Instagram handle search
        if not lead.instagram_handle:
            logger.info("Instagram handle missing. Searching via Google/DuckDuckGo...")
            try:
                searched_handle = await insta_finder.find_instagram(lead.business_name, lead.address or "")
                if searched_handle:
                    logger.info(f"Found Instagram handle: @{searched_handle}")
                    lead.instagram_handle = searched_handle
                    lead.instagram_url = f"https://instagram.com/{searched_handle}"
                    session.add(ResearchNote(
                        lead_id=lead.id,
                        source="google_custom_search",
                        content=f"Instagram handle found: @{searched_handle}",
                    ))
            except Exception as e:
                logger.warning(f"Instagram handle search failed: {e}")

        if tqm and task_id:
            await tqm.wait_if_paused(task_id)
            tqm.update_progress(task_id, 65.0)

        # 3. Instagram bio scrape (best-effort) — multiple HTML fallbacks
        # because Instagram's server-rendered markup varies by locale,
        # account state, and bot-detection tier.
        instagram_bio = ""
        if lead.instagram_handle:
            try:
                bio_url = f"https://www.instagram.com/{lead.instagram_handle}/"
                logger.info(f"Fetching Instagram bio from {bio_url}...")
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                }
                async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as hclient:
                    bio_resp = await hclient.get(bio_url)
                if bio_resp.status_code == 200:
                    # (4) Try meta description, og:description, twitter:description,
                    # and JSON-LD in that order — first non-empty wins.
                    instagram_bio = _extract_instagram_bio(bio_resp.text)
                if instagram_bio:
                    lead.instagram_bio = instagram_bio[:2000]
                    session.add(ResearchNote(
                        lead_id=lead.id,
                        source="instagram_bio",
                        content=f"Instagram bio (@{lead.instagram_handle}): {instagram_bio}",
                    ))
                    logger.info(f"Instagram bio fetched: {instagram_bio[:80]}...")
                else:
                    logger.info(
                        f"No bio meta tags found on Instagram page for @{lead.instagram_handle}."
                    )
            except Exception as bio_err:
                logger.warning(f"Instagram bio scraping failed (best-effort): {bio_err}")

        # 3b. Multi-platform social discovery (YouTube, LinkedIn, TikTok, etc.)
        # Skips already-resolved URLs so we never overwrite a known-good value.
        existing_socials = {
            "youtube_url": lead.youtube_url,
            "linkedin_url": lead.linkedin_url,
            "tiktok_url": lead.tiktok_url,
            "facebook_url": lead.facebook_url,
            "telegram_url": lead.telegram_url,
            "twitter_url": lead.twitter_url,
        }
        # (6) Pass the Instagram handle to SocialDiscovery (appended to the
        # business name) so cross-platform searches can match the same
        # handle reused on YouTube / LinkedIn / TikTok — same handle
        # across platforms is a very strong uniqueness signal.
        discovery_query_name = lead.business_name
        if lead.instagram_handle:
            stripped_handle = lead.instagram_handle.lstrip("@").strip()
            if stripped_handle and stripped_handle.lower() not in (lead.business_name or "").lower():
                discovery_query_name = f"{lead.business_name} @{stripped_handle}"
                logger.debug(
                    f"Social discovery: appending Instagram handle '@{stripped_handle}' "
                    f"to business name for cross-platform matching."
                )
        try:
            profiles = social_discovery.discover_all_sync(
                business_name=discovery_query_name,
                location=lead.address or "",
                existing=existing_socials,
            )
            for field, url in profiles.to_dict().items():
                if url and not existing_socials.get(field):
                    setattr(lead, field, url)
                    session.add(ResearchNote(
                        lead_id=lead.id,
                        source=f"social_discovery.{field}",
                        content=f"Auto-discovered: {url}",
                    ))
            found = [k for k, v in profiles.to_dict().items() if v]
            if found:
                logger.info(
                    f"Multi-platform discovery for {lead.business_name}: "
                    f"found {', '.join(found)}"
                )
        except Exception as e:
            logger.warning(f"Multi-platform social discovery failed: {e}")

        if tqm and task_id:
            await tqm.wait_if_paused(task_id)
            tqm.update_progress(task_id, 85.0)

        # 4. Generate AI outreach message
        logger.info("Generating AI outreach message draft using Multi-Agent flow...")
        review_highlights = f"Rating: {lead.rating or 'N/A'}. Total reviews: {lead.review_count or 'N/A'}."

        social_context_parts: list[str] = []
        if lead.youtube_url:
            social_context_parts.append(f"YouTube: {lead.youtube_url}")
        if lead.linkedin_url:
            social_context_parts.append(f"LinkedIn: {lead.linkedin_url}")
        if lead.tiktok_url:
            social_context_parts.append(f"TikTok: {lead.tiktok_url}")
        if lead.facebook_url:
            social_context_parts.append(f"Facebook: {lead.facebook_url}")
        if lead.telegram_url:
            social_context_parts.append(f"Telegram: {lead.telegram_url}")
        if lead.twitter_url:
            social_context_parts.append(f"X/Twitter: {lead.twitter_url}")
        if social_context_parts:
            review_highlights += " Sosyal medya kanalları: " + ", ".join(social_context_parts) + "."

        safe_fallback = _safe_dm_fallback(lead.business_name, lead.sector)
        draft_content = ""
        analysis_content = ""

        try:
            from aegisScout.ai.multi_agent import generate_multi_agent_draft
            agent_res = await generate_multi_agent_draft(
                business_name=lead.business_name,
                sector=lead.sector or "Bilinmiyor",
                has_website=bool(lead.has_website),
                website_notes=website_notes,
                instagram_bio=instagram_bio or "",
                review_highlights=review_highlights,
                opportunities=opportunities_text,
                language=language,
                tone=tone
            )
            draft_content = agent_res.get("opening_message", "")
            analysis_content = agent_res.get("analysis", "")
        except Exception as ae:
            logger.warning(
                f"Multi-agent generation failed for lead {lead.id} ({lead.business_name}): {ae}. "
                f"Falling back to deterministic safe text."
            )
            draft_content = safe_fallback
            analysis_content = f"AI Generation Failed: {ae}; used deterministic fallback."

        # Final safety net
        if not draft_content or not draft_content.strip():
            draft_content = safe_fallback
            if not analysis_content:
                analysis_content = "Empty draft replaced by deterministic fallback."

        # Remove old drafts then save new
        old_drafts = session.exec(
            select(Message).where(
                (Message.lead_id == lead.id) &
                (Message.status == "draft")
            )
        ).all()
        for old_d in old_drafts:
            session.delete(old_d)

        session.add(Message(
            lead_id=lead.id,
            direction="outbound",
            channel="instagram_manual",
            content=draft_content,
            ai_generated=True,
            status="draft",
        ))

        # Heuristic Lead Scoring & Prioritization
        base_score = 50.0
        if not lead.has_website:
            base_score += 20.0
        elif lead.website_quality_score is not None and lead.website_quality_score < 50:
            base_score += 15.0
            
        if lead.rating is not None and lead.rating >= 4.0:
            base_score += 10.0
        if lead.review_count is not None:
            if lead.review_count >= 25:
                base_score += 10.0
            elif lead.review_count < 5:
                base_score -= 10.0
                
        priority_score = min(max(base_score, 0.0), 100.0)
        lead.priority_score = priority_score
        
        if is_new_domain:
            lead.priority_label = "Yeni Girişim (Cold Lead)"
            lead.priority_score = min(95.0, priority_score + 30.0)
        else:
            if priority_score >= 75.0:
                lead.priority_label = "Yüksek (Hot Lead)"
            elif priority_score >= 50.0:
                lead.priority_label = "Orta (Warm)"
            else:
                lead.priority_label = "Düşük (Cold)"

        lead.status = "researched"
        lead.notes = f"AI Analiz: {analysis_content}"
        lead.updated_at = _utcnow()

        session.add(ActivityLog(
            action="research",
            details=f"Researched lead {lead.business_name} (ID: {lead.id}). Quality Score: {lead.website_quality_score or 'N/A'}.",
        ))

        try:
            session.commit()
            logger.info(f"Research complete for {lead.business_name}. Draft message created.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving research results for lead {lead_id}: {e}")


# ---------------------------------------------------------------------------
# Multi-platform social discovery (additive enrichment)
# ---------------------------------------------------------------------------

async def enrich_lead_socials(lead_id: int, social_discovery=None) -> Dict[str, Optional[str]]:
    """
    Run multi-platform social discovery for a single lead and persist any
    new URLs that are found. Returns the (possibly updated) social fields
    as a dict. Existing URLs are never overwritten.
    """
    from aegisScout.discovery.social_discovery import SocialDiscovery
    sd = social_discovery or SocialDiscovery()

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            logger.warning(f"enrich_lead_socials: lead {lead_id} not found.")
            return {}

        existing = {
            "youtube_url": lead.youtube_url,
            "linkedin_url": lead.linkedin_url,
            "tiktok_url": lead.tiktok_url,
            "facebook_url": lead.facebook_url,
            "telegram_url": lead.telegram_url,
            "twitter_url": lead.twitter_url,
        }
        try:
            profiles = await sd.discover_all(
                business_name=lead.business_name,
                location=lead.address or "",
                existing=existing,
            )
        except Exception as e:
            logger.warning(f"enrich_lead_socials: discovery failed: {e}")
            return existing

        updates: Dict[str, Optional[str]] = {}
        for field, url in profiles.to_dict().items():
            if url and not existing.get(field):
                setattr(lead, field, url)
                updates[field] = url
                session.add(ResearchNote(
                    lead_id=lead.id,
                    source=f"social_discovery.{field}",
                    content=f"Auto-discovered (GUI/CLI): {url}",
                ))

        if updates:
            lead.updated_at = _utcnow()
            session.add(ActivityLog(
                action="social_discovery",
                details=(
                    f"Multi-platform discovery for {lead.business_name} (ID: {lead.id}): "
                    f"found {', '.join(updates.keys())}"
                ),
            ))
            try:
                session.commit()
                logger.info(
                    f"Social discovery updated lead {lead_id}: {', '.join(updates.keys())}"
                )
            except Exception as e:
                session.rollback()
                logger.error(f"enrich_lead_socials: commit failed: {e}")
        else:
            logger.info(f"Social discovery: no new URLs for lead {lead_id}.")

        return {**existing, **updates}
