# Technical Analysis & Implementation Blueprint for Milestone M3: Search & Candidate Profile Matching Overhaul

**Author**: `explorer_m3`  
**Date**: 2026-08-06  
**Target Files**:
- `src/aegisScout/discovery/instagram_finder.py`
- `src/aegisScout/discovery/noise_filter.py`
- `tests/test_discovery/test_instagram_finder.py`
- `tests/test_noise_filter_enhanced.py`

---

## 1. Executive Summary

Milestone M3 focuses on upgrading aegisScout's Instagram search engine, candidate profile matching, and relevance scoring algorithm.
Currently, candidate profile relevance scoring (`_calculate_relevance_score`) relies on a simple unweighted keyword counter (adding arbitrary increments like +15 for username match, +10 for full name match) and accepts only `target_sector`. It lacks awareness of target business names, target domain URLs, target locations, aggregator handle suppression, location conflicts, and exact word boundary enforcement (leading to false positives like `"diş"` matching `"disney"`).

Baseline testing confirms that all **150 discovery unit and integration tests** currently pass cleanly (`pytest tests/test_discovery/`).

This document formulates the technical specifications and precise implementation blueprints for the **5 core features of Milestone M3**:
1. **6-Factor Composite Candidate Scoring Formula**: Normalized 0-100 scale using weighted components: Name (30%), Domain (25%), Location (15%), Sector (15%), Contact (10%), Activity (5%), minus Aggregator Penalty (-40) and Location Conflict Penalty (-20).
2. **Bidirectional SLD Domain Cross-Referencing**: Extraction of Second-Level Domains (SLD) from target website URLs and candidate URLs / linktrees / usernames with multi-part TLD support (`.com.tr`, `.net.tr`, `.org.tr`).
3. **Directory & Aggregator Filter**: Suppression of directory/aggregator handles (`@rehberi`, `@portali`, `@turkiye`, `@firmalari`, etc.) and directory URL structures with a -40 penalty.
4. **Location Strictness & Conflict Penalty**: City and district compliance matching with a -20 penalty when candidate bio/name explicitly specifies a major city conflicting with the target city.
5. **Boundary-Enforced Keyword Matching**: Tokenized regex matching (`\b...`) with Turkish character slugification to eliminate false-positive substring matches (e.g. `diş` vs `disney`, `bar` vs `bardak`, `oto` vs `otobüs`).

---

## 2. Codebase Audit & Detailed Findings

### 2.1 Audit of `src/aegisScout/discovery/instagram_finder.py`

#### A. Existing `_calculate_relevance_score` Implementation (Lines 1763–1820)
```python
def _calculate_relevance_score(self, profile: Dict, target_sector: str) -> int:
    if not target_sector:
        score = 50
        if profile.get("email"): score += 8
        if profile.get("phone"): score += 8
        if profile.get("website"): score += 4
        if profile.get("is_verified"): score += 5
        return min(score, 75)

    keywords = [w.lower() for w in target_sector.split() if len(w) > 2]
    ascii_keywords = [_slugify_tr(w) for w in keywords]
    
    username_text = profile.get("username", "").lower()
    full_name_text = profile.get("full_name", "").lower()
    bio_text = profile.get("bio", "").lower()
    category_text = profile.get("category", "").lower()
    
    username_matches = sum(1 for k in ascii_keywords if k in username_text)
    fullname_matches = sum(1 for k in keywords if k in full_name_text)
    bio_matches = sum(1 for k in keywords if k in bio_text)
    cat_matches = sum(1 for k in keywords if k in category_text)
    
    score = 45
    score += min(username_matches * 15, 25)
    score += min(fullname_matches * 10, 20)
    score += min(bio_matches * 6, 15)
    score += min(cat_matches * 5, 10)
    
    if profile.get("email"): score += 6
    if profile.get("phone"): score += 6
    if profile.get("website"): score += 3
    if profile.get("is_verified"): score += 4
    if profile.get("linktree_url"): score += 2
    
    total_matches = username_matches + fullname_matches + bio_matches + cat_matches
    if total_matches == 0:
        score = max(score - 20, 30)
    
    return min(int(score), 99)
```

#### B. Flaws Identified in `_calculate_relevance_score`
1. **Limited Parameter Signature**: Accepts only `profile: Dict` and `target_sector: str`. Does NOT accept or evaluate `target_business_name`, `target_website`, or `target_location`.
2. **Naive Substring Keyword Matching**: Uses Python's `if k in text` operator. This causes false-positive matches (e.g. `diş` matches `disney`, `bar` matches `barış` or `bardak`, `oto` matches `otobüs`).
3. **No Domain Cross-Referencing**: Ignores `target_website` even when available. A candidate whose Instagram bio links directly to the business's official domain receives no domain match boost.
4. **No Aggregator Filter**: Aggregator/directory accounts like `@istanbul_kuafor_rehberi` or `@turkiye_doktorlar` receive high scores because they contain sector keywords in their handle and bio.
5. **No Location Conflict Penalty**: A search targeted at `"Ankara"` will score an `"İstanbul"` profile high as long as sector keywords match, creating location misalignments.

#### C. Search Entry Points and Parameter Propagation
- `fetch_profile_details` (Line 679): Currently signature is `(self, username: str, target_sector: str = "")`. Needs expansion to `(self, username: str, target_sector: str = "", target_business_name: str = "", target_website: str = "", target_location: str = "")`.
- `search_profiles_by_username_or_sector` (Line 1284): Currently takes `sector_keywords`, `username_query`, `location`, `limit`. Needs to accept `target_business_name` and `target_website`.
- `search_profiles_by_sector` (Line 1449): Currently takes `sector_keywords`, `location`, `limit`. Needs to accept `target_business_name` and `target_website`.

---

### 2.2 Audit of `src/aegisScout/discovery/noise_filter.py`

Currently, `noise_filter.py` provides:
- `DEFAULT_EXCLUDED_OSM_TAGS` & `DEFAULT_EXCLUDED_GOOGLE_TYPES`
- `NOISE_NAME_PATTERNS` (includes strings like `"otopark"`, `"ATM"`, `"cami"`, `"bulurum"`, `"sgk"`, `"vergi dairesi"`)
- `is_directory_url(url: str) -> bool` using `_DIRECTORY_URL_BLACKLIST_PATTERNS` (detects listing domain pages like `yellowpages`, `bulurum.com`, `haritane.com/kategori`).

#### Gaps in `noise_filter.py` for Instagram Discovery
- `NOISE_NAME_PATTERNS` does not include Instagram-specific directory handle patterns (`rehberi`, `portali`, `turkiye`, `firmalari`, `sayfalari`, `dizin`).
- There is no function `is_aggregator_handle(username: str, full_name: str, bio: str) -> bool` or `is_aggregator_profile(profile: dict) -> bool` to evaluate Instagram candidate dicts.

---

### 2.3 Audit of Existing Tests (`tests/test_discovery/test_instagram_finder.py`)

Current tests for relevance scoring:
- `test_relevance_score_no_sector`: Verifies score is 50-75 when sector is empty.
- `test_relevance_score_with_username_keyword_match`: Verifies handle match yields score >= 70.
- `test_relevance_score_no_keyword_match_penalty`: Verifies score <= 50 when no keyword matches.

All 16 tests in `test_instagram_finder.py` pass. However, there are no tests for:
- 6-factor composite formula sub-scores and weights
- Bidirectional SLD matching
- Aggregator handle penalties (-40)
- Location conflict penalties (-20)
- Word boundary keyword matching (`diş` vs `disney`)

---

## 3. Implementation Blueprints for Milestone M3

### 3.1 Feature 9: 6-Factor Composite Candidate Scoring Formula

#### Mathematical Model & Weights
$$S_{\text{composite}} = 0.30 \cdot S_{\text{name}} + 0.25 \cdot S_{\text{domain}} + 0.15 \cdot S_{\text{location}} + 0.15 \cdot S_{\text{sector}} + 0.10 \cdot S_{\text{contact}} + 0.05 \cdot S_{\text{activity}} - P_{\text{aggregator}} - P_{\text{location\_conflict}}$$

Final score is clamped to `[0, 100]`:
$$S_{\text{final}} = \max(0, \min(100, \text{round}(S_{\text{composite}})))$$

#### Sub-Score Breakdown

1. **$S_{\text{name}}$ (Weight: 30%) — Target Name & Handle Match Score (0–100)**:
   - Target string $T_{\text{name}}$ is `target_business_name` or `username_query` (slugified).
   - Candidate handle $H = \text{slugify}(profile.get("username"))$.
   - Candidate full name $F = \text{slugify}(profile.get("full\_name"))$.
   - Scoring rules:
     - Exact handle match ($H == T_{\text{name}}$): **100**
     - Prefix handle match ($H.startswith(T_{\text{name}})$ or $T_{\text{name}}.startswith(H)$): **85**
     - Target slug inside handle or handle inside target slug: **75**
     - Full name exact match ($F == T_{\text{name}}$): **90**
     - Token overlap ratio ($N_{\text{matching\_tokens}} / N_{\text{target\_tokens}}$): $100 \times \text{ratio}$
     - If no `target_business_name` provided: fallback to sector keyword match on username/name, default **50**.

2. **$S_{\text{domain}}$ (Weight: 25%) — Website / Domain SLD Match Score (0–100)**:
   - Uses Bidirectional SLD Cross-Referencing (Section 3.2).
   - Exact SLD match between target website and candidate website/linktree: **100**
   - Substring SLD match (candidate linktree path matches target SLD): **85**
   - Candidate username matches target SLD: **80**
   - Bio text contains target SLD domain: **70**
   - Target website provided, but candidate has no website/linktree & no bio domain match: **0**
   - Target website NOT provided: neutral score **50** (or **60** if candidate has any valid external website).

3. **$S_{\text{location}}$ (Weight: 15%) — Location Match Score (0–100)**:
   - Target location $L$ parsed into city and district tokens.
   - Candidate text $C_{\text{loc}} = \text{bio} + \text{full\_name} + \text{username} + \text{category}$.
   - City AND district match $C_{\text{loc}}$: **100**
   - City match $C_{\text{loc}}$: **80**
   - District match $C_{\text{loc}}$: **70**
   - Target location provided, but candidate text has no location mention: **40**
   - Target location NOT provided: neutral score **50**.

4. **$S_{\text{sector}}$ (Weight: 15%) — Boundary-Enforced Sector Match Score (0–100)**:
   - Sector keywords tokenized and checked using boundary-enforced regex (`match_keyword_bounded`).
   - Sector keyword in username (boundary enforced): **+40**
   - Sector keyword in full name (boundary enforced): **+30**
   - Sector keyword in bio (boundary enforced): **+20**
   - Sector keyword in category: **+20**
   - Sum capped at **100**. If 0 keyword matches: **0**.
   - Sector NOT provided: neutral score **50**.

5. **$S_{\text{contact}}$ (Weight: 10%) — Contact Richness Score (0–100)**:
   - Email present (`profile.get("email")`): **+35**
   - Phone or WhatsApp present (`profile.get("phone")` or `profile.get("whatsapp_link")`): **+35**
   - Website present (`profile.get("website")`): **+20**
   - Linktree / Bio link present (`profile.get("linktree_url")`): **+10**
   - Sum capped at **100**.

6. **$S_{\text{activity}}$ (Weight: 5%) — Recency & Activity Score (0–100)**:
   - `recency_status` == `"ACTIVE"` (or `last_active_raw` $\le 30$): **100**
   - `recency_status` == `"MODERATE"` (or `last_active_raw` $\le 90$): **70**
   - `recency_status` == `"INACTIVE"` or `is_zero_post` is True: **20**
   - Verified account bonus (`is_verified`): **+20** (capped at 100).

7. **$P_{\text{aggregator}}$ — Aggregator & Directory Handle Penalty**:
   - If candidate handle, bio, or website indicates an aggregator/directory: **-40 points**.

8. **$P_{\text{location\_conflict}}$ — Location Conflict Penalty**:
   - If target location specifies a major city (e.g. `"Ankara"`) and candidate text explicitly specifies a different major city (e.g. `"İstanbul"`) without mentioning the target city: **-20 points**.

---

### 3.2 Feature 10: Bidirectional SLD Domain Cross-Referencing Blueprint

#### Second-Level Domain (SLD) Extractor
```python
def extract_sld(url_or_domain: str) -> str:
    """
    Extract Second-Level Domain (SLD) from URL or hostname.
    Supports Turkish multi-level TLDs (.com.tr, .net.tr, .org.tr, .gov.tr, .edu.tr)
    and social link aggregators (linktr.ee/username, beacons.ai/username, taplink.cc/username).
    
    Examples:
        'https://www.akdenizdis.com.tr/tr' -> 'akdenizdis'
        'https://linktr.ee/akdenizdis' -> 'akdenizdis'
        'http://subdomain.mycompany.com' -> 'mycompany'
    """
    if not url_or_domain:
        return ""
    
    # 1. Clean protocol and trailing path whitespace
    cleaned = url_or_domain.strip().lower()
    cleaned = re.sub(r"^https?://", "", cleaned)
    
    # 2. Check for link aggregator domains where SLD/handle is in path
    aggregator_domains = (
        "linktr.ee", "beacons.ai", "taplink.cc", "shopier.com",
        "linkin.bio", "lnk.to", "bio.site", "link.bio", "allmylinks.com"
    )
    for agg in aggregator_domains:
        if cleaned.startswith(agg):
            parts = cleaned.split("/")
            if len(parts) > 1 and parts[1].strip():
                return _slugify_tr(parts[1].split("?")[0].strip())
    
    # 3. Extract hostname only
    host = cleaned.split("/")[0].split("?")[0].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    
    # 4. Handle Turkish and international multi-part TLDs
    parts = host.split(".")
    if len(parts) == 1:
        return _slugify_tr(parts[0])
    
    # Known multi-level TLD suffixes
    two_part_tlds = {"com.tr", "net.tr", "org.tr", "gov.tr", "edu.tr", "co.uk", "com.br", "co.jp"}
    joined_last_two = f"{parts[-2]}.{parts[-1]}"
    
    if joined_last_two in two_part_tlds and len(parts) >= 3:
        sld = parts[-3]
    else:
        sld = parts[-2]
    
    return _slugify_tr(sld)
```

#### Bidirectional Matching Logic
```python
def calculate_domain_score(target_website: str, profile_website: str, profile_linktree: str, profile_username: str, profile_bio: str) -> int:
    if not target_website:
        # No target website to match against
        return 60 if (profile_website or profile_linktree) else 50

    target_sld = extract_sld(target_website)
    if not target_sld:
        return 50

    cand_web_sld = extract_sld(profile_website)
    cand_link_sld = extract_sld(profile_linktree)
    cand_u_slug = _slugify_tr(profile_username)
    bio_slug = _slugify_tr(profile_bio)

    # 1. Exact SLD match on website or linktree URL
    if (cand_web_sld and cand_web_sld == target_sld) or (cand_link_sld and cand_link_sld == target_sld):
        return 100

    # 2. Partial SLD match (target SLD contained in candidate SLD or vice versa)
    if cand_web_sld and (target_sld in cand_web_sld or cand_web_sld in target_sld) and len(cand_web_sld) >= 4:
        return 85
    if cand_link_sld and (target_sld in cand_link_sld or cand_link_sld in target_sld) and len(cand_link_sld) >= 4:
        return 85

    # 3. Username matches target SLD
    if cand_u_slug == target_sld or target_sld in cand_u_slug:
        return 80

    # 4. Target SLD mentioned in bio
    if target_sld in bio_slug and len(target_sld) >= 4:
        return 70

    # Target website specified but no candidate domain match
    return 0
```

---

### 3.3 Feature 11: Directory & Aggregator Filter Blueprint

#### Detection Rules & Regexes
Aggregator handles on Instagram typically use suffixes like `_rehberi`, `_portali`, `_turkiye`, `_firmalari`, `_dizin`, `_sayfalari`.

Added to `src/aegisScout/discovery/noise_filter.py`:
```python
AGGREGATOR_HANDLE_PATTERNS = [
    r"rehberi$", r"portali$", r"turkiye$", r"firmalari$",
    r"sayfalari$", r"dizin$", r"rehber$", r"katalogu$",
    r"^rehber_", r"^portal_", r"^dizin_"
]

AGGREGATOR_BIO_PATTERNS = [
    "firma rehberi", "türkiye rehberi", "turkiye rehberi",
    "sektörel dizin", "sektorel dizin", "ücretsiz firma kaydı",
    "tüm firmalar", "türkiyenin en büyük rehberi", "rehber portalı"
]

def is_aggregator_profile(profile: dict) -> bool:
    """
    Detect if an Instagram candidate profile is a directory/aggregator account.
    """
    username = _slugify_tr(str(profile.get("username", "")))
    full_name = _slugify_tr(str(profile.get("full_name", "")))
    bio = str(profile.get("bio", "")).lower()
    website = str(profile.get("website", "") or profile.get("website_url", ""))

    # 1. Handle regex suffix check
    for pat in AGGREGATOR_HANDLE_PATTERNS:
        if re.search(pat, username):
            return True

    # 2. Bio phrase check
    for phrase in AGGREGATOR_BIO_PATTERNS:
        if phrase in bio:
            return True

    # 3. Website directory URL check
    if website and is_directory_url(website):
        return True

    # 4. NOISE_NAME_PATTERNS check on full_name
    for noise_pat in ("firma rehberi", "sarı sayfalar", "yellowpages", "bulurum"):
        if noise_pat in full_name:
            return True

    return False
```

#### Penalty Application
In `_calculate_relevance_score`:
```python
aggregator_penalty = 40 if is_aggregator_profile(profile) else 0
```

---

### 3.4 Feature 12: Location Strictness & Conflict Penalty Blueprint

#### Major Turkish Cities List
```python
TURKISH_MAJOR_CITIES = {
    "istanbul", "ankara", "izmir", "bursa", "antalya", "adana", "konya",
    "gaziantep", "kocaeli", "mersin", "diyarbakir", "hatay", "manisa",
    "kayseri", "samsun", "balikesir", "kahramanmaras", "van", "aydin",
    "denizli", "tekirdag", "mugla", "eskisehir", "trabzon", "ordu",
    "sanliurfa", "malatya", "erzurum", "sakarya", "rize", "canakkale"
}
```

#### Matching & Conflict Logic
```python
def calculate_location_score_and_penalty(target_location: str, profile: dict) -> tuple[int, int]:
    """
    Returns (location_score, location_conflict_penalty).
    location_score: 0-100
    location_conflict_penalty: 0 or 20
    """
    if not target_location:
        return 50, 0

    target_loc_clean = _slugify_tr(target_location)
    target_tokens = set(re.findall(r"\w+", target_loc_clean))
    
    cand_text = _slugify_tr(
        f"{profile.get('bio', '')} {profile.get('full_name', '')} {profile.get('username', '')} {profile.get('category', '')}"
    )
    cand_tokens = set(re.findall(r"\w+", cand_text))

    # Identify target city if present in target_tokens
    target_cities = target_tokens.intersection(TURKISH_MAJOR_CITIES)
    
    # 1. Location Score Calculation
    matching_tokens = target_tokens.intersection(cand_tokens)
    if target_cities and target_cities.issubset(cand_tokens) and len(matching_tokens) > len(target_cities):
        # City AND district matched
        location_score = 100
    elif target_cities and target_cities.issubset(cand_tokens):
        # City matched
        location_score = 80
    elif matching_tokens:
        # District or region matched
        location_score = 70
    elif "turkiye" in cand_text or "tr" in cand_text:
        location_score = 60
    else:
        # Target location specified, but candidate mentions no location
        location_score = 40

    # 2. Location Conflict Penalty Calculation
    penalty = 0
    if target_cities:
        target_city = next(iter(target_cities))
        # Find any OTHER major city in candidate text
        other_cities_in_cand = cand_tokens.intersection(TURKISH_MAJOR_CITIES) - {target_city}
        
        # If candidate explicitly mentions a DIFFERENT city AND does NOT mention target city
        if other_cities_in_cand and target_city not in cand_tokens:
            penalty = 20

    return location_score, penalty
```

---

### 3.5 Feature 13: Boundary-Enforced Keyword Matching Blueprint

#### Boundary Matching Function
```python
def match_keyword_bounded(keyword: str, text: str) -> bool:
    """
    Boundary-enforced keyword matching supporting Turkish text and multi-word phrases.
    Prevents false-positive substring matches (e.g. 'diş' matching 'disney', 'bar' matching 'bardak').
    
    Example:
        match_keyword_bounded("diş", "Diş Hekimi Ahmet") -> True
        match_keyword_bounded("diş", "Disney Plus TR") -> False
    """
    if not keyword or not text:
        return False
    
    kw_slug = _slugify_tr(keyword.strip())
    text_slug = _slugify_tr(text.strip())
    if not kw_slug or not text_slug:
        return False
    
    pattern = r"\b" + re.escape(kw_slug) + r"\b"
    return bool(re.search(pattern, text_slug, re.IGNORECASE))
```

#### Integration in Sector Scoring
```python
def calculate_sector_score(target_sector: str, profile: dict) -> int:
    if not target_sector:
        return 50

    keywords = [w.strip() for w in re.split(r"\s+", target_sector) if len(w.strip()) >= 3]
    if not keywords:
        return 50

    username = profile.get("username", "")
    full_name = profile.get("full_name", "")
    bio = profile.get("bio", "")
    category = profile.get("category", "")

    score = 0
    for kw in keywords:
        if match_keyword_bounded(kw, username):
            score += 40
        if match_keyword_bounded(kw, full_name):
            score += 30
        if match_keyword_bounded(kw, bio):
            score += 20
        if match_keyword_bounded(kw, category):
            score += 20

    return min(score, 100)
```

---

## 4. Refactoring Plan for `InstagramFinder` Codebase

### 4.1 Refactored `_calculate_relevance_score` Signature & Logic

```python
def _calculate_relevance_score(
    self,
    profile: Dict,
    target_sector: str = "",
    target_business_name: str = "",
    target_website: str = "",
    target_location: str = "",
) -> int:
    """
    6-Factor Composite Candidate Scoring Engine (0-100 scale).
    S_composite = 0.30*S_name + 0.25*S_domain + 0.15*S_location + 0.15*S_sector + 0.10*S_contact + 0.05*S_activity
                 - Penalty_aggregator - Penalty_location_conflict
    """
    # 1. S_name (30%)
    s_name = self._calculate_name_score(target_business_name, target_sector, profile)

    # 2. S_domain (25%)
    s_domain = calculate_domain_score(
        target_website,
        profile.get("website", ""),
        profile.get("linktree_url", ""),
        profile.get("username", ""),
        profile.get("bio", ""),
    )

    # 3. S_location (15%) & Location Conflict Penalty
    s_location, penalty_location_conflict = calculate_location_score_and_penalty(
        target_location, profile
    )

    # 4. S_sector (15%)
    s_sector = calculate_sector_score(target_sector, profile)

    # 5. S_contact (10%)
    s_contact = 0
    if profile.get("email"): s_contact += 35
    if profile.get("phone") or profile.get("whatsapp_link"): s_contact += 35
    if profile.get("website"): s_contact += 20
    if profile.get("linktree_url"): s_contact += 10
    s_contact = min(s_contact, 100)

    # 6. S_activity (5%)
    s_activity = 20
    recency = str(profile.get("recency_status", "")).upper()
    if recency == "ACTIVE" or profile.get("last_active_raw", 999) <= 30:
        s_activity = 100
    elif recency == "MODERATE" or profile.get("last_active_raw", 999) <= 90:
        s_activity = 70
    if profile.get("is_verified"):
        s_activity = min(s_activity + 20, 100)

    # 7. Aggregator Penalty (-40)
    penalty_aggregator = 40 if is_aggregator_profile(profile) else 0

    # 8. Composite Formula Synthesis
    s_raw = (
        0.30 * s_name
        + 0.25 * s_domain
        + 0.15 * s_location
        + 0.15 * s_sector
        + 0.10 * s_contact
        + 0.05 * s_activity
        - penalty_aggregator
        - penalty_location_conflict
    )

    return max(0, min(100, int(round(s_raw))))
```

### 4.2 Updated Signatures Across `InstagramFinder`

| Function | Current Signature | Updated Signature |
|---|---|---|
| `fetch_profile_details` | `(username: str, target_sector: str = "")` | `(username: str, target_sector: str = "", target_business_name: str = "", target_website: str = "", target_location: str = "")` |
| `_calculate_relevance_score` | `(profile: Dict, target_sector: str)` | `(profile: Dict, target_sector: str = "", target_business_name: str = "", target_website: str = "", target_location: str = "")` |
| `search_profiles_by_sector` | `(sector_keywords: str, location: str = "", limit: int = 20)` | `(sector_keywords: str, location: str = "", limit: int = 20, target_business_name: str = "", target_website: str = "")` |
| `search_profiles_by_username_or_sector` | `(sector_keywords: str = "", username_query: str = "", location: str = "", limit: int = 20)` | `(sector_keywords: str = "", username_query: str = "", location: str = "", limit: int = 20, target_business_name: str = "", target_website: str = "")` |

---

## 5. Proposed Test Matrix for Milestone M3

To achieve 100% test coverage for Milestone M3 features, the worker implementation will add 10 new unit test cases in `tests/test_discovery/test_instagram_finder.py`:

1. `test_composite_scoring_formula_weights`: Validates exact mathematical weighting of all 6 factors ($S_{\text{name}}, S_{\text{domain}}, S_{\text{location}}, S_{\text{sector}}, S_{\text{contact}}, S_{\text{activity}}$).
2. `test_extract_sld_multi_level_tld`: Tests SLD extraction for `.com.tr`, `.net.tr`, `.org.tr`, `.co.uk`, and `linktr.ee` URLs.
3. `test_bidirectional_sld_exact_match`: Verifies exact domain SLD match (`akdenizdis.com` target vs `akdenizdis.com.tr` profile) yields $S_{\text{domain}} = 100$.
4. `test_bidirectional_sld_linktree_and_username_match`: Verifies `linktr.ee/akdenizdis` and `@akdenizdis` username matches yield high domain scores.
5. `test_aggregator_handle_penalty`: Verifies `@istanbul_kuafor_rehberi` and `@turkiye_doktorlar` trigger -40 aggregator penalty.
6. `test_aggregator_directory_url_penalty`: Verifies profile linking to `yellowpages.com.tr` or `bulurum.com` triggers -40 penalty.
7. `test_location_match_city_and_district`: Verifies candidate matching both city ("İstanbul") and district ("Kadıköy") receives $S_{\text{location}} = 100$.
8. `test_location_conflict_penalty`: Verifies candidate specifying `"İstanbul"` when target location is `"Ankara"` triggers -20 conflict penalty.
9. `test_location_multi_city_no_penalty`: Verifies candidate listing both `"Ankara ve İstanbul"` does NOT trigger conflict penalty for `"Ankara"` target.
10. `test_boundary_enforced_keyword_matching`: Verifies `"diş"` matches `"Ahmet Diş Kliniği"` but does NOT match `"Disney Plus TR"`.

---

## 6. Implementation Summary & Next Steps

This analysis provides the complete architectural foundation for worker execution.
- **Noise Filter Enhancement**: Implement `AGGREGATOR_HANDLE_PATTERNS`, `AGGREGATOR_BIO_PATTERNS`, `is_aggregator_profile()` in `noise_filter.py`.
- **Instagram Finder Enhancement**: Implement `extract_sld()`, `match_keyword_bounded()`, `calculate_domain_score()`, `calculate_location_score_and_penalty()`, `calculate_sector_score()`, and refactor `_calculate_relevance_score()` in `instagram_finder.py`.
- **Test Suite Expansion**: Add the 10-test matrix to `test_instagram_finder.py`.
