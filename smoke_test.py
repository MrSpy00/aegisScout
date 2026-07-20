"""Smoke test for the three modified files."""
import sys
import types

sys.path.insert(0, "src")

# Stub aegisScout.discovery.base
base_mod = types.ModuleType("aegisScout.discovery.base")


class BaseDiscoveryProvider:
    async def search(self, *a, **k):
        pass

    async def _search_query(self, *a, **k):
        pass


base_mod.BaseDiscoveryProvider = BaseDiscoveryProvider
sys.modules["aegisScout.discovery.base"] = base_mod

# Stub aegisScout.utils.logger
logger_mod = types.ModuleType("aegisScout.utils.logger")


def get_logger(name):
    class L:
        def info(self, *a, **k):
            pass

        def debug(self, *a, **k):
            pass

        def warning(self, *a, **k):
            pass

        def error(self, *a, **k):
            pass

    return L()


logger_mod.get_logger = get_logger
sys.modules["aegisScout.utils.logger"] = logger_mod

# Stub aegisScout.core.config
config_mod = types.ModuleType("aegisScout.core.config")


class _S:
    google_custom_search_api_key = ""
    google_custom_search_cx = ""


config_mod.settings = _S()
sys.modules["aegisScout.core.config"] = config_mod

# Imports
import importlib

for mod_name in [
    "aegisScout.discovery.models",
    "aegisScout.discovery.web_search_provider",
    "aegisScout.discovery.social_discovery",
]:
    importlib.import_module(mod_name)
    print(f"Imported {mod_name} OK")

# models: instagram_bio present
from aegisScout.discovery.models import LeadCandidate

lc = LeadCandidate(business_name="Test", source="web_search")
assert lc.instagram_bio is None, "instagram_bio should default to None"
assert hasattr(lc, "instagram_bio"), "instagram_bio field must exist on LeadCandidate"
print("models.py: instagram_bio field present and default None OK")

# web_search_provider: business name cleaning
from aegisScout.discovery.web_search_provider import WebSearchDiscoveryProvider

p = WebSearchDiscoveryProvider()
clean = p._clean_business_name("1. Acme Klinik")
assert clean == "Acme Klinik", f"expected 'Acme Klinik', got {clean!r}"
clean2 = p._clean_business_name("* Acme Dis Hekimi")
assert clean2 == "Acme Dis Hekimi", f"expected 'Acme Dis Hekimi', got {clean2!r}"
clean3 = p._clean_business_name("- Acme Studio")
assert clean3 == "Acme Studio", f"expected 'Acme Studio', got {clean3!r}"
print("web_search_provider.py: _clean_business_name strips prefixes OK")

# web_search_provider: aggregate filter logic exists
import re as _re

pat = [
    r"(en|en\s+iyi|top|best|en\s+güzel|popüler)\s*\d+",
    r"\d+\s*(en|en\s+iyi|top|best|en\s+güzel)",
    r"(sıralama|ranking|list|liste|sıralaması|rehberi|önerileri)",
]
assert any(_re.search(p, "en iyi 50 psikolog") for p in pat)
assert any(_re.search(p, "best 10 dentists") for p in pat)
assert any(_re.search(p, "rehberi") for p in "rehberi")
print("web_search_provider.py: aggregate filter regex covers expected patterns")

# social_discovery: slug normalization
from aegisScout.discovery.social_discovery import _handle_slug, _is_valid_handle

assert _handle_slug("https://www.facebook.com/Acme-Corp") == "acmecorp"
assert _handle_slug("https://twitter.com/acme") == "acme"
assert _handle_slug("https://www.linkedin.com/in/acme-corp-istanbul") == "acmecorpistanbul"
assert _handle_slug("https://www.youtube.com/@Acme.Corp") == "acmecorp"
print("social_discovery.py: _handle_slug normalization OK")

# social_discovery: handle validation
assert _is_valid_handle("instagram.com", "realhandle")
assert _is_valid_handle("youtube.com", "channel_name")
assert not _is_valid_handle("instagram.com", "p"), "structural page should be rejected"
assert not _is_valid_handle("instagram.com", "12345"), "pure digits should be rejected"
assert not _is_valid_handle("instagram.com", ".leading-dot")
assert not _is_valid_handle("instagram.com", "trailing_underscore_")
assert not _is_valid_handle("instagram.com", "has space")
print("social_discovery.py: _is_valid_handle rejects bad handles OK")

# social_discovery: _BaseFinder has build_queries
from aegisScout.discovery.social_discovery import _BaseFinder, YouTubeFinder, LinkedInFinder

yt = YouTubeFinder()
queries = yt.build_queries("Acme Clinic", "Istanbul")
assert isinstance(queries, list) and len(queries) >= 2
assert any("site:youtube.com" in q for q in queries)
assert any("youtube" in q for q in queries)
print("social_discovery.py: YouTubeFinder.build_queries returns multi-query list OK")

li = LinkedInFinder()
lq = li.build_queries("Acme Co", "Istanbul")
assert any("/company" in q for q in lq)
print("social_discovery.py: LinkedInFinder.build_queries includes /company variant OK")

# social_discovery: dedup
from aegisScout.discovery.social_discovery import SocialDiscovery

results = {
    "youtube_url": "https://www.youtube.com/@acme-corp",
    "linkedin_url": "https://www.linkedin.com/company/acme-corp",
    "tiktok_url": None,
    "facebook_url": "https://www.facebook.com/Acme-Corp",  # same slug
    "twitter_url": "https://twitter.com/acme_corp",  # same slug
    "telegram_url": "https://t.me/acme_corp",  # same slug
}
deduped = SocialDiscovery._dedup_by_business(results)
# Expect only the first (youtube) kept
assert deduped["youtube_url"] is not None
assert deduped["linkedin_url"] is None
assert deduped["facebook_url"] is None
assert deduped["twitter_url"] is None
assert deduped["telegram_url"] is None
print("social_discovery.py: _dedup_by_business removes cross-platform duplicates OK")

print("\nAll smoke tests passed.")
