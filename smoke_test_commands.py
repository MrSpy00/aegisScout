"""Smoke test for cli/commands.py helpers — verifies the 6 required changes."""
import importlib.util
import sys
import types
from pathlib import Path

WORKSPACE = Path(r"X:\Projects\ActiveProjects\aegisScout\src")

# Stub optional heavy deps so import doesn't blow up during the smoke test.
stubs = {
    "aegisScout": types.ModuleType("aegisScout"),
    "aegisScout.core": types.ModuleType("aegisScout.core"),
    "aegisScout.core.database": types.ModuleType("aegisScout.core.database"),
    "aegisScout.core.database": types.ModuleType("aegisScout.core.database"),
    "aegisScout.core.models": types.ModuleType("aegisScout.core.models"),
    "aegisScout.core.toml_config": types.ModuleType("aegisScout.core.toml_config"),
    "aegisScout.discovery": types.ModuleType("aegisScout.discovery"),
    "aegisScout.discovery.models": types.ModuleType("aegisScout.discovery.models"),
    "aegisScout.ai": types.ModuleType("aegisScout.ai"),
    "aegisScout.ai.provider_router": types.ModuleType("aegisScout.ai.provider_router"),
    "aegisScout.ai.prompts": types.ModuleType("aegisScout.ai.prompts"),
    "aegisScout.ai.prompts.outreach_message": types.ModuleType("aegisScout.ai.prompts.outreach_message"),
    "aegisScout.utils": types.ModuleType("aegisScout.utils"),
    "aegisScout.utils.logger": types.ModuleType("aegisScout.utils.logger"),
    "aegisScout.utils.json_helper": types.ModuleType("aegisScout.utils.json_helper"),
}
sys.modules.update(stubs)
sys.path.insert(0, str(WORKSPACE))

# Minimal pydantic stub
class _PydBase:
    def __init__(self, **kw): self.__dict__.update(kw)
pyd = types.ModuleType("pydantic")
pyd.BaseModel = _PydBase
sys.modules["pydantic"] = pyd

# Minimal sqlmodel stub
sqlm = types.ModuleType("sqlmodel")
sqlm.Session = object
sqlm.select = lambda *a, **k: None
sys.modules["sqlmodel"] = sqlm

# Configure stubs
stubs["aegisScout.core.database"].engine = object()
stubs["aegisScout.core.toml_config"].config_data = {}
class _Lead: pass
class _RN: pass
class _Msg: pass
class _AL: pass
stubs["aegisScout.core.models"].Lead = _Lead
stubs["aegisScout.core.models"].ResearchNote = _RN
stubs["aegisScout.core.models"].Message = _Msg
stubs["aegisScout.core.models"].ActivityLog = _AL
stubs["aegisScout.discovery.models"].LeadCandidate = _PydBase
stubs["aegisScout.utils.logger"].get_logger = lambda n: types.SimpleNamespace(
    info=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
    debug=lambda *a, **k: None,
)
stubs["aegisScout.utils.json_helper"].extract_json = lambda s: {}
class _PR:
    def __init__(self): pass
stubs["aegisScout.ai.provider_router"].ProviderRouter = _PR
stubs["aegisScout.ai.prompts.outreach_message"].build_prompt = lambda **k: ""
stubs["aegisScout.discovery"].base = types.ModuleType("aegisScout.discovery.base")
class _BaseDP:
    pass
stubs["aegisScout.discovery.base"].BaseDiscoveryProvider = _BaseDP
# Provider modules — each exports a class with the same name.
provider_classes = [
    "OSMDiscoveryProvider", "GooglePlacesDiscoveryProvider",
    "WebSearchDiscoveryProvider", "WebScraper", "InstagramFinder",
    "SocialDiscovery", "DoktorTakvimiDiscoveryProvider",
]
for name in provider_classes:
    modname = name.replace("Provider", "_provider").lower()
    if name == "WebScraper":
        modname = "web_scraper"
    elif name == "InstagramFinder":
        modname = "instagram_finder"
    elif name == "SocialDiscovery":
        modname = "social_discovery"
    elif name == "DoktorTakvimiDiscoveryProvider":
        modname = "doktortakvimi_provider"
    full = f"aegisScout.discovery.{modname}"
    m = types.ModuleType(full)
    setattr(m, name, type(name, (_BaseDP,), {}))
    sys.modules[full] = m
    stubs["aegisScout.discovery"][name] = getattr(m, name)

# httpx stub
httpx_stub = types.ModuleType("httpx")
httpx_stub.AsyncClient = object
sys.modules["httpx"] = httpx_stub

# Load the module
spec = importlib.util.spec_from_file_location(
    "commands_test", str(Path(r"X:\Projects\ActiveProjects\aegisScout\src\aegisScout\cli\commands.py"))
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print("Module load: OK")
    print("BASE_DISCOVERY_PROVIDERS =", [n for n, _ in mod.BASE_DISCOVERY_PROVIDERS])
    print("LOW_RESULT_THRESHOLD =", mod.LOW_RESULT_THRESHOLD)

    # === Change 2: multi-word keyword extraction ===
    assert mod._extract_sector_keywords("dis hekimi") == ["dis", "hekimi"]
    assert mod._extract_sector_keywords("psikolog") == ["psikolog"]  # single-word, no split
    assert mod._extract_sector_keywords("en iyi 10 diş hekimi") == ["en", "iyi", "diş", "hekimi"]
    assert mod._extract_sector_keywords("") == []
    print("Multi-word extraction: OK")

    # === Change 3: aggregate/ranking filter ===
    class _C:
        def __init__(self, name, addr=None):
            self.business_name = name
            self.address = addr
    assert mod._is_aggregate_or_ranking(_C("En iyi 50 diş hekimi")) is True
    assert mod._is_aggregate_or_ranking(_C("Top 10 dentists")) is True
    assert mod._is_aggregate_or_ranking(_C("Best psychologists 2024")) is True
    assert mod._is_aggregate_or_ranking(_C("Dr. Ahmet Yılmaz", "Kadıköy")) is False
    assert mod._is_aggregate_or_ranking(_C("Acıbadem Dental Clinic", "Bağdat Cad. No 5")) is False
    assert mod._is_aggregate_or_ranking(_C("Diş Hekimi Listesi Önerilen", "İstanbul")) is True
    print("Aggregate filter: OK")

    # === Change 4: bio extraction with 4 fallbacks ===
    html_meta = '<html><head><meta name="description" content="META bio"></head></html>'
    html_og = '<html><head><meta property="og:description" content="OG bio"></head></html>'
    html_tw = '<html><head><meta name="twitter:description" content="TW bio"></head></html>'
    html_ld = '<html><head><script type="application/ld+json">{"description":"LD bio"}</script></head></html>'
    html_empty = '<html><head></head></html>'
    # Priority: meta > og > twitter > jsonld
    assert mod._extract_instagram_bio(html_meta) == "META bio"
    assert mod._extract_instagram_bio(html_og) == "OG bio"
    assert mod._extract_instagram_bio(html_tw) == "TW bio"
    assert mod._extract_instagram_bio(html_ld) == "LD bio"
    assert mod._extract_instagram_bio(html_empty) == ""
    assert mod._extract_instagram_bio("") == ""
    # Nested JSON-LD
    html_nested = '<script type="application/ld+json">{"@graph":[{"description":"Nested bio"}]}</script>'
    assert mod._extract_instagram_bio(html_nested) == "Nested bio"
    # Meta wins even when og also present
    html_both = '<meta name="description" content="META wins"><meta property="og:description" content="OG loses">'
    assert mod._extract_instagram_bio(html_both) == "META wins"
    print("Bio extraction (4 fallbacks): OK")

    # Candidate dedupe
    cs = [
        _C("A", "addr1"),
        _C("A", "addr1"),       # dup
        _C("A", "addr2"),
        _C("B", None),
        _C("B", None),         # dup
        _C("B", ""),           # dup (normalized)
    ]
    out = mod._dedupe_candidates(cs)
    assert len(out) == 3, f"expected 3 unique, got {len(out)}"
    print("Candidate dedupe: OK")

    # === Change 1: BASE_DISCOVERY_PROVIDERS includes dokortakvimi ===
    names = [n for n, _ in mod.BASE_DISCOVERY_PROVIDERS]
    assert "osm" in names
    assert "web_search" in names
    assert "doktortakvimi" in names
    print("Provider registry includes dokortakvimi: OK")

    # Validate that every registered class is a BaseDiscoveryProvider subclass.
    for _name, cls in mod.BASE_DISCOVERY_PROVIDERS:
        assert issubclass(cls, _BaseDP), f"{_name} is not a BaseDiscoveryProvider"
    print("All providers are BaseDiscoveryProvider subclasses: OK")

    print()
    print("ALL SMOKE TESTS PASSED")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"SMOKE TEST FAILED: {type(e).__name__}: {e}")
    sys.exit(1)
