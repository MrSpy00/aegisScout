"""
DoktorTakvimi.com Discovery Provider.

Scrapes doktortakvimi.com — a Turkish directory of doctors, dentists,
psychologists and counselors — to discover professional leads with
contact details, ratings and review counts.

Follows the same async pattern as WebSearchDiscoveryProvider /
OSMDiscoveryProvider: a single ``search(sector, location, radius_km)``
entry point that returns a list of ``LeadCandidate`` objects.
"""
import re
import urllib.parse
import httpx
from typing import List, Optional, Set

from bs4 import BeautifulSoup, Tag

from aegisScout.discovery.base import BaseDiscoveryProvider
from aegisScout.discovery.models import LeadCandidate
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.doktortakvimi")

# Realistic desktop browser fingerprint. doktortakvimi.com is a generic
# marketing-style site but still benefits from a non-default UA.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
}

_BASE_URL = "https://www.doktortakvimi.com"
_SEARCH_URL = f"{_BASE_URL}/ara"

# Maximum results to fetch per search to avoid hammering the upstream.
_MAX_RESULTS = 30
# Cap the number of detail pages we crawl — protects against huge cities.
_MAX_DETAIL_FETCHES = 15
# HTTP timeout for any single upstream request.
_HTTP_TIMEOUT_SEC = 20.0


class DoktorTakvimiDiscoveryProvider(BaseDiscoveryProvider):
    """
    Discovery provider that scrapes doktortakvimi.com search results
    and individual profile pages to extract professional leads
    (psychologist, counselor, dentist, doctor, etc.).
    """

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    async def search(
        self, sector: str, location: str, radius_km: int = 10
    ) -> List[LeadCandidate]:
        """
        Search doktortakvimi.com for ``sector`` professionals in ``location``
        and return enriched ``LeadCandidate`` records.

        ``radius_km`` is accepted for interface compatibility with the
        other discovery providers but is ignored — doktortakvimi.com
        performs its own city/keyword matching rather than radius lookups.
        """
        if not sector or not sector.strip():
            logger.warning("DoktorTakvimi search skipped: empty sector.")
            return []
        if not location or not location.strip():
            logger.warning("DoktorTakvimi search skipped: empty location.")
            return []

        logger.info(
            f"Starting DoktorTakvimi discovery for '{sector}' in '{location}' "
            f"(radius_km={radius_km} — ignored by this provider)."
        )

        # ------------------------------------------------------------------
        # 1. Fetch the search results listing page(s).
        # ------------------------------------------------------------------
        detail_urls = await self._collect_profile_urls(sector, location)
        if not detail_urls:
            logger.info(
                f"DoktorTakvimi discovery: no profile links found for "
                f"'{sector}' in '{location}'."
            )
            return []

        logger.debug(
            f"DoktorTakvimi: collected {len(detail_urls)} unique profile URLs."
        )

        # ------------------------------------------------------------------
        # 2. Fetch each profile detail page and parse the data.
        # ------------------------------------------------------------------
        candidates: List[LeadCandidate] = []
        for url in list(detail_urls)[:_MAX_DETAIL_FETCHES]:
            try:
                candidate = await self._parse_profile(url, sector)
            except Exception as e:  # never let a single bad page abort the run
                logger.warning(
                    f"DoktorTakvimi: skipping profile '{url}' due to error: {e}"
                )
                continue
            if candidate is not None:
                candidates.append(candidate)

        logger.info(
            f"DoktorTakvimi discovery finished: found "
            f"{len(candidates)} unique leads for '{sector}' in '{location}'."
        )
        return candidates

    # ------------------------------------------------------------------ #
    # Listing page (search results)                                       #
    # ------------------------------------------------------------------ #

    async def _collect_profile_urls(
        self, sector: str, location: str
    ) -> Set[str]:
        """
        Query the search endpoint with several URL variations, then
        extract profile detail URLs from each result page.
        """
        query = f"{sector} {location}".strip()
        # doktortakvimi.com tends to use a single ``q`` field; we also try
        # the alternative slug-based URL used by older versions of the
        # site.  We dedupe by absolute URL below.
        candidate_urls = [
            f"{_SEARCH_URL}?q={urllib.parse.quote(query)}",
            f"{_SEARCH_URL}?q={urllib.parse.quote(sector)}"
            f"&city={urllib.parse.quote(location)}",
            f"{_BASE_URL}/ara?q={urllib.parse.quote(sector)}"
            f"&il={urllib.parse.quote(location)}",
        ]

        profile_urls: Set[str] = set()
        async with httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT_SEC, follow_redirects=True
        ) as client:
            for url in candidate_urls:
                if len(profile_urls) >= _MAX_RESULTS:
                    break
                html = await self._safe_get(client, url)
                if not html:
                    continue
                self._extract_profile_links(html, profile_urls)
                if profile_urls:
                    # No need to hit the other variants if we already
                    # got a healthy number of results from the first.
                    if len(profile_urls) >= 5:
                        break

        return profile_urls

    def _extract_profile_links(self, html: str, sink: Set[str]) -> None:
        """
        Pull every link on the listing page that *looks* like a profile
        detail URL and add it to ``sink``.  We only keep links under
        the doktortakvimi.com domain and that don't point at obvious
        non-profile resources (search, login, ads, etc.).
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            logger.warning(f"DoktorTakvimi: BeautifulSoup failed on listing: {e}")
            return

        blacklist_substrings = (
            "/giris", "/kayit", "/reklam", "/iletisim",
            "/hakkimizda", "/yardim", "/sss", "/cerez-politikasi",
            "/kullanim-kosullari", "/kvkk", "/gizlilik",
            "/blog", "/makale", "/sayfa",
        )

        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            if any(bad in href.lower() for bad in blacklist_substrings):
                continue
            # Make absolute.
            if href.startswith("/"):
                absolute = f"{_BASE_URL}{href}"
            elif href.startswith("http"):
                absolute = href
            else:
                continue
            if _BASE_URL not in absolute:
                continue
            # Heuristic: a profile URL on doktortakvimi.com always contains
            # a numeric id at the end.  We accept both old (``/doktor/...``)
            # and new (``/doktorlar/...``, ``/{specialty}/...``) layouts.
            if re.search(r"-?\d{3,}$", absolute.split("?")[0]):
                sink.add(absolute.split("?")[0])

    # ------------------------------------------------------------------ #
    # Detail page (profile)                                              #
    # ------------------------------------------------------------------ #

    async def _parse_profile(
        self, detail_url: str, sector: str
    ) -> Optional[LeadCandidate]:
        """
        Fetch a profile page and extract name, phone, address, website,
        rating and review_count.  Returns ``None`` if the page is empty
        or doesn't contain a usable business name.
        """
        async with httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT_SEC, follow_redirects=True
        ) as client:
            html = await self._safe_get(client, detail_url)

        if not html:
            return None
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            logger.warning(
                f"DoktorTakvimi: BeautifulSoup failed on detail '{detail_url}': {e}"
            )
            return None

        name = self._extract_name(soup)
        if not name:
            logger.debug(
                f"DoktorTakvimi: no business name in '{detail_url}', skipping."
            )
            return None

        phone = self._extract_phone(soup)
        address = self._extract_address(soup)
        website = self._extract_website(soup)
        rating, review_count = self._extract_rating(soup)
        detail_sector = self._extract_sector(soup) or sector

        return LeadCandidate(
            business_name=name.strip(),
            sector=detail_sector,
            phone=phone,
            address=address,
            website_url=website,
            has_website=bool(website),
            rating=rating,
            review_count=review_count,
            source="doktortakvimi",
        )

    # ----- field-level extractors (defensive: try multiple selectors) --- #

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Prefer the ``<h1>`` (the visible doctor name) before falling back
        to og:title or the document title.
        """
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return _clean_name(h1.get_text(strip=True))

        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            cleaned = _clean_name(og["content"])
            if cleaned:
                return cleaned

        if soup.title and soup.title.string:
            return _clean_name(soup.title.string)
        return None

    def _extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Look for tel: links, structured ``itemprop="telephone"`` and
        finally a phone-shaped regex on the visible text.
        """
        for tel in soup.find_all("a", href=re.compile(r"^tel:", re.I)):
            number = _normalize_phone(tel.get("href", ""))
            if number:
                return number

        for tag in soup.find_all(attrs={"itemprop": "telephone"}):
            value = tag.get("content") or tag.get_text(strip=True)
            number = _normalize_phone(value)
            if number:
                return number

        # Fallback: scan visible text for a phone number.
        body_text = soup.get_text(separator=" ", strip=True)
        match = re.search(
            r"(\+?90\s?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
            body_text,
        )
        if match:
            return _normalize_phone(match.group(0))
        return None

    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Try schema.org address fields, then fall back to a labelled
        paragraph that contains "Adres".
        """
        for tag in soup.find_all(attrs={"itemprop": "streetAddress"}):
            text = tag.get("content") or tag.get_text(" ", strip=True)
            if text:
                return _clean_whitespace(text)

        for tag in soup.find_all(attrs={"itemprop": "address"}):
            text = tag.get("content") or tag.get_text(" ", strip=True)
            if text:
                return _clean_whitespace(text)

        # Look for a labelled block: "Adres: <text>".
        for elem in soup.find_all(string=re.compile(r"Adres\s*:", re.I)):
            parent: Optional[Tag] = elem.parent
            if parent is None:
                continue
            block_text = parent.get_text(" ", strip=True)
            cleaned = re.sub(r"^Adres\s*:\s*", "", block_text, flags=re.I)
            cleaned = _clean_whitespace(cleaned)
            if cleaned and len(cleaned) > 5:
                return cleaned

        return None

    def _extract_website(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Look for an outbound link that *isn't* a social profile and
        *isn't* a doktortakvimi.com page.
        """
        blacklist_domains = (
            "doktortakvimi.com",
            "facebook.com", "twitter.com", "instagram.com",
            "linkedin.com", "youtube.com", "tiktok.com",
            "twitter.com", "x.com",
        )
        # 1. Schema.org url field.
        for tag in soup.find_all(attrs={"itemprop": "url"}):
            href = tag.get("href") or tag.get("content")
            if href and not any(b in href.lower() for b in blacklist_domains):
                return href.strip()
        # 2. og:url fallback (likely self-referencing — skip).
        # 3. Anchor scan.
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href.startswith("http"):
                continue
            if any(b in href.lower() for b in blacklist_domains):
                continue
            # Ignore mailto, javascript, tel.
            if href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            return href
        return None

    def _extract_rating(self, soup: BeautifulSoup) -> tuple[Optional[float], Optional[int]]:
        """
        Pull rating + review count from common locations:
        - itemprop="ratingValue" / "reviewCount"
        - meta tags with aggregateRating
        - visible text patterns like "5,0" / "(123 yorum)"
        """
        rating = _parse_float(
            soup.find(attrs={"itemprop": "ratingValue"}),
        )
        if rating is None:
            for meta in soup.find_all("meta"):
                content = (meta.get("content") or "").strip()
                if not content:
                    continue
                if "rating" in (meta.get("itemprop") or "").lower():
                    rating = _parse_float_from(content)
                    if rating is not None:
                        break

        review_count = _parse_int(
            soup.find(attrs={"itemprop": "reviewCount"}),
        )
        if review_count is None:
            for meta in soup.find_all("meta"):
                content = (meta.get("content") or "").strip()
                if "reviewCount" in (meta.get("itemprop") or ""):
                    review_count = _parse_int_from(content)
                    if review_count is not None:
                        break

        # Last-ditch fallback: scrape visible text.
        if rating is None or review_count is None:
            text = soup.get_text(" ", strip=True)
            if rating is None:
                m = re.search(
                    r"(\d{1,2}[.,]\d)\s*/\s*5",
                    text,
                )
                if m:
                    rating = _parse_float_from(m.group(1).replace(",", "."))
            if review_count is None:
                m = re.search(
                    r"\(\s*(\d{1,5})\s*(yorum|Değerlendirme|reviews?)\s*\)",
                    text,
                    re.IGNORECASE,
                )
                if m:
                    review_count = _parse_int_from(m.group(1))

        return rating, review_count

    def _extract_sector(self, soup: BeautifulSoup) -> Optional[str]:
        """
        The page usually contains a breadcrumb or sidebar entry that
        names the specialty (e.g. "Psikolog", "Diş Hekimi").  We grab
        the first such match and fall back to None.
        """
        candidates: List[str] = []
        common_specialties = (
            "psikolog", "psikiyatrist", "psikoterapist",
            "diş hekimi", "diyetisyen", "estetisyen",
            "çocuk doktoru", "dahiliye", "kadın doğum",
            "ortopedi", "göz doktoru", "cildiye",
            "kulak burun boğaz", "fizyoterapist",
            "psikolojik danışman", "danışman",
            "psikolojik danışman", "uzman",
            "doktor", "uzman psikolog",
        )
        text = soup.get_text(" ", strip=True).lower()
        for spec in common_specialties:
            if spec in text:
                candidates.append(spec)
        if not candidates:
            return None
        # Prefer the longest match — "uzman psikolog" beats "psikolog".
        return max(candidates, key=len).title()

    # ------------------------------------------------------------------ #
    # Low-level HTTP helper                                               #
    # ------------------------------------------------------------------ #

    async def _safe_get(
        self, client: httpx.AsyncClient, url: str
    ) -> Optional[str]:
        """
        Tiny GET-with-error-handling wrapper.  Never raises so the
        caller's loop is not interrupted by upstream errors.
        """
        try:
            resp = await client.get(url, headers=_HEADERS)
        except httpx.HTTPError as e:
            logger.warning(f"DoktorTakvimi: HTTP error fetching '{url}': {e}")
            return None
        if resp.status_code != 200:
            logger.warning(
                f"DoktorTakvimi: '{url}' returned status {resp.status_code}."
            )
            return None
        return resp.text


# ---------------------------------------------------------------------------
# Module-level pure-function helpers (kept outside the class for clarity).
# ---------------------------------------------------------------------------


def _clean_name(raw: str) -> str:
    """
    Strip common noise from a page title or h1 ("Dr.", "Dt.", trailing
    separators etc.) so the resulting ``business_name`` is presentable.
    """
    text = raw.strip()
    # Collapse internal whitespace.
    text = re.sub(r"\s+", " ", text)
    # Drop a generic site-name suffix if present.
    text = re.sub(
        r"\s*[|•\-–]\s*(DoktorTakvimi|doktortakvimi\.com).*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip(" -|•–") or ""


def _clean_whitespace(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def _normalize_phone(raw: str) -> Optional[str]:
    """
    Strip a phone number down to a canonical ``+90XXXXXXXXXX`` form
    when possible, otherwise return the cleaned original.
    """
    if not raw:
        return None
    text = raw.strip()
    # Drop the tel: / tel:// scheme.
    if text.lower().startswith("tel:"):
        text = text[4:]
    # Keep only digits and a leading +.
    cleaned = re.sub(r"[^\d+]", "", text)
    # Prepend country code if missing.
    if cleaned.startswith("0"):
        cleaned = "+90" + cleaned.lstrip("0")
    elif cleaned.startswith("5") and len(cleaned) == 10:
        cleaned = "+90" + cleaned
    elif not cleaned.startswith("+") and len(cleaned) == 10:
        cleaned = "+90" + cleaned
    if not re.search(r"\d{7,}", cleaned):
        return None
    return cleaned


def _parse_float(tag) -> Optional[float]:
    if tag is None:
        return None
    value = tag.get("content") or tag.get_text(strip=True)
    return _parse_float_from(value)


def _parse_float_from(raw: str) -> Optional[float]:
    if not raw:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", raw)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _parse_int(tag) -> Optional[int]:
    if tag is None:
        return None
    value = tag.get("content") or tag.get_text(strip=True)
    return _parse_int_from(value)


def _parse_int_from(raw: str) -> Optional[int]:
    if not raw:
        return None
    match = re.search(r"\d{1,7}", raw.replace(".", "").replace(",", ""))
    if not match:
        return None
    try:
        return int(match.group(0))
    except (TypeError, ValueError):
        return None
