"""
Milestone M3 Empirical Stress Test Suite — AegisScout
Adversarial challenge for candidate profile scoring, SLD domain extraction,
aggregator filter, location conflict penalty, and keyword boundary matching.
"""
import pytest
from aegisScout.discovery.instagram_finder import (
    InstagramFinder,
    extract_sld,
    calculate_domain_score,
    calculate_location_score_and_penalty,
    calculate_sector_score,
    calculate_name_score,
    match_keyword_bounded,
    TURKISH_MAJOR_CITIES,
    TURKEY_MAJOR_CITIES,
)
from aegisScout.discovery.noise_filter import is_aggregator_profile, is_noise


class TestM3MatchingStress:

    def setup_method(self):
        self.finder = InstagramFinder()

    # =========================================================================
    # 1. COMPOSITE SCORING FORMULA BOUNDS & CLAMPING STRESS
    # =========================================================================

    def test_composite_scoring_maximum_bounds(self):
        """Verify perfect profile with all signals reaches max composite score (clamped to [0, 100])."""
        perfect_profile = {
            "username": "akdenizdis",
            "full_name": "Akdeniz Dis Hekimligi Klinigi",
            "bio": "Istanbul Kadikoy Ozel Akdeniz Dis Klinigi https://akdenizdis.com.tr",
            "website": "https://akdenizdis.com.tr",
            "linktree_url": "https://linktr.ee/akdenizdis",
            "email": "info@akdenizdis.com.tr",
            "phone": "+905321112233",
            "whatsapp_link": "https://wa.me/905321112233",
            "category": "Dis Hekimi",
            "recency_status": "ACTIVE",
            "last_active_raw": 5,
            "is_verified": True,
            "is_zero_post": False,
        }

        score = self.finder._calculate_relevance_score(
            profile=perfect_profile,
            target_sector="Dis Hekimi",
            target_business_name="Akdeniz Dis",
            target_website="https://akdenizdis.com.tr",
            target_location="Kadikoy, Istanbul",
        )

        assert 95 <= score <= 100

    def test_composite_scoring_minimum_bounds_clamping(self):
        """Verify heavy penalties (-40 aggregator, -20 location conflict) clamp cleanly to 0."""
        aggregator_conflict_profile = {
            "username": "ankara_doktorlar_rehberi",
            "full_name": "Ankara Doktorlar ve Dis Hekimleri Rehberi Portal",
            "bio": "Ankara genelinde tum doktorlar rehber portali. Ucretsiz firma kaydi.",
            "website": "https://firmarehberi.com",
            "recency_status": "INACTIVE",
            "last_active_raw": 365,
            "is_zero_post": True,
        }

        score = self.finder._calculate_relevance_score(
            profile=aggregator_conflict_profile,
            target_sector="Yazilim Firmasi",
            target_business_name="Matrix Yazilim",
            target_website="https://matrixyazilim.com",
            target_location="Istanbul",
        )

        assert score == 0, f"Expected 0 due to clamping, got {score}"

    def test_composite_scoring_type_resilience_last_active_string(self):
        """
        STRESS: Test resilience when last_active_raw is passed as string instead of int.
        Demonstrates unhandled TypeError bug when last_active_raw is string.
        """
        profile = {
            "username": "test_clinic",
            "full_name": "Test Clinic",
            "bio": "Test clinic bio",
            "recency_status": "UNKNOWN",
            "last_active_raw": "15",  # string type instead of int
        }

        # Documenting the unhandled TypeError vulnerability
        with pytest.raises(TypeError, match="not supported between instances of 'str' and 'int'"):
            self.finder._calculate_relevance_score(
                profile=profile,
                target_sector="Clinic",
                target_business_name="Test Clinic",
            )

    # =========================================================================
    # 2. AGGREGATOR FILTER STRESS & FAILURE MODES
    # =========================================================================

    def test_aggregator_filter_genuine_aggregators(self):
        """Verify genuine directory/aggregator handles are correctly identified."""
        directory_profiles = [
            {"username": "istanbul_rehberi", "bio": "Istanbul Firma Rehberi Portal"},
            {"username": "sektorel_dizin", "bio": "Turkiye Sektorel Dizin Portali"},
            {"username": "doktorlar_portali", "bio": "Tum doktorlar rehber portali"},
            {"username": "firmakatalogu", "bio": "Ucretsiz firma kaydi"},
            {"username": "rehber_ankara", "bio": "Ankara Rehberi"},
        ]

        for p in directory_profiles:
            assert is_aggregator_profile(p) is True, f"Failed to flag aggregator: {p['username']}"

    def test_aggregator_filter_false_positive_turkiye_suffix(self):
        """
        STRESS / FAILURE MODE TEST: Check handle ending with 'turkiye'.
        'r"turkiye$"' in AGGREGATOR_HANDLE_PATTERNS flags legitimate brand accounts
        like @bmw_turkiye, @nike_turkiye, @dentakdeniz_turkiye as directory aggregators!
        """
        brand_profile = {
            "username": "dentakdeniz_turkiye",
            "full_name": "Dent Akdeniz Dis Klinikleri Turkiye",
            "bio": "Ozel Dent Akdeniz Dis Sagligi Merkezi Resmi Instagram Hesabidir.",
            "website": "https://dentakdeniz.com.tr",
        }

        is_agg = is_aggregator_profile(brand_profile)
        # Note: If r"turkiye$" is in patterns, this returns True (False Positive)
        assert is_agg is True  # Documenting current empirical behavior (overly broad pattern)

    def test_aggregator_filter_false_positive_portali_bio(self):
        """
        STRESS / FAILURE MODE TEST: Check bio containing 'portali'.
        'portali' phrase in AGGREGATOR_BIO_PATTERNS flags legitimate business bios
        that mention customer/patient portals.
        """
        business_profile = {
            "username": "ozel_akdeniz_hastanesi",
            "full_name": "Ozel Akdeniz Hastanesi",
            "bio": "Hasta portali uzerinden online randevu ve tahlil sonuclarinizi alabilirsiniz.",
            "website": "https://akdenizhastanesi.com",
        }

        is_agg = is_aggregator_profile(business_profile)
        assert is_agg is True  # Documenting current empirical behavior (overly broad bio pattern)

    # =========================================================================
    # 3. SLD DOMAIN EXTRACTION & CROSS-REFERENCING STRESS
    # =========================================================================

    def test_extract_sld_various_url_formats(self):
        """Test SLD extraction across protocols, ports, subdomains, and aggregators."""
        cases = [
            ("https://www.akdenizdis.com.tr/tr/iletisim", "akdenizdis"),
            ("http://akdenizdis.com", "akdenizdis"),
            ("http://subdomain.mycompany.com:8080/path?q=1", "mycompany"),
            ("https://linktr.ee/akdenizdis", "akdenizdis"),
            ("https://beacons.ai/akdenizdis?fbclid=123", "akdenizdis"),
            ("https://taplink.cc/akdenizdis/", "akdenizdis"),
            ("AKDENIZDIS.COM.TR", "akdenizdis"),
        ]

        for input_url, expected_sld in cases:
            assert extract_sld(input_url) == expected_sld, f"Failed for {input_url}: expected {expected_sld}, got {extract_sld(input_url)}"

    def test_domain_score_matching_scenarios(self):
        """Test domain scoring logic for exact match, partial match, and no match."""
        # 1. Exact match via website
        assert calculate_domain_score(
            target_website="https://akdenizdis.com.tr",
            profile_website="https://akdenizdis.com",
            profile_linktree="",
            profile_username="akdeniz_dis",
            profile_bio="",
        ) == 100

        # 2. Exact match via linktree
        assert calculate_domain_score(
            target_website="https://akdenizdis.com.tr",
            profile_website="",
            profile_linktree="https://linktr.ee/akdenizdis",
            profile_username="dis_klinik",
            profile_bio="",
        ) == 100

        # 3. Username match
        assert calculate_domain_score(
            target_website="https://akdenizdis.com",
            profile_website="",
            profile_linktree="",
            profile_username="akdenizdis",
            profile_bio="",
        ) == 80

        # 4. Bio mention
        assert calculate_domain_score(
            target_website="https://akdenizdis.com",
            profile_website="",
            profile_linktree="",
            profile_username="dis_hekimim",
            profile_bio="Web sitemiz: akdenizdis.com",
        ) == 70

        # 5. Domain mismatch
        assert calculate_domain_score(
            target_website="https://akdenizdis.com",
            profile_website="https://baskandis.com",
            profile_linktree="",
            profile_username="baskandis",
            profile_bio="",
        ) == 0

    # =========================================================================
    # 4. LOCATION SCORE & CITY CONFLICT STRESS
    # =========================================================================

    def test_location_score_exact_city_and_district(self):
        """Test location score when both city and district match."""
        profile = {
            "bio": "Kadikoy Istanbul Ozel Dis Klinigi",
            "full_name": "Kadikoy Dis Hekimi",
            "username": "kadikoydis",
            "category": "Dis Hekimi",
        }

        score, penalty = calculate_location_score_and_penalty("Kadikoy, Istanbul", profile)
        assert score == 100
        assert penalty == 0

    def test_location_conflict_penalty(self):
        """Test cross-city conflict penalty (-20). Target: Istanbul, Candidate: Ankara."""
        profile = {
            "bio": "Ankara Kizilay Ozel Dis Klinigi",
            "full_name": "Ankara Dis Hekimi",
            "username": "ankaradis",
            "category": "Dis Hekimi",
        }

        score, penalty = calculate_location_score_and_penalty("Istanbul", profile)
        assert score == 40 or score == 0
        assert penalty == 20

    def test_location_city_data_structures_consistency(self):
        """
        STRESS TEST: Compare TURKEY_MAJOR_CITIES list vs TURKISH_MAJOR_CITIES set.
        Uncover any missing cities (e.g. Batman, Sivas, Gebze).
        """
        list_cities = {c for c in TURKEY_MAJOR_CITIES if c}
        set_cities = TURKISH_MAJOR_CITIES

        missing_in_set = list_cities - set_cities
        assert "batman" in missing_in_set
        assert "sivas" in missing_in_set
        assert "gebze" in missing_in_set

    def test_location_conflict_false_positive_person_name(self):
        """
        STRESS / FAILURE MODE: Doctor named 'Aydin' located in Ankara facing target='Ankara'.
        Because 'aydin' is in TURKISH_MAJOR_CITIES set, if candidate bio says 'Dr. Aydin Yilmaz Ankara',
        does it handle it correctly or trigger false conflict?
        """
        profile = {
            "bio": "Dr. Aydin Yilmaz Dis Hekimligi Klinigi Ankara",
            "full_name": "Dr. Aydin Yilmaz",
            "username": "draydinyilmaz",
            "category": "Dis Hekimi",
        }

        score, penalty = calculate_location_score_and_penalty("Ankara", profile)
        assert score >= 80
        assert penalty == 0, f"Expected 0 penalty, got {penalty}"

    # =========================================================================
    # 5. BOUNDARY-ENFORCED KEYWORD MATCHING STRESS & TURKISH SUFFIX LIMITATIONS
    # =========================================================================

    def test_keyword_matching_boundary_enforcement(self):
        """Verify substring false-positives are blocked while exact matches pass."""
        # Substring false positives blocked
        assert match_keyword_bounded("dis", "Disney Store Istanbul") is False
        assert match_keyword_bounded("bar", "Bardak Cafe") is False
        assert match_keyword_bounded("kuafor", "Salonkuafor Sanat") is False

        # Exact boundary-delimited match
        assert match_keyword_bounded("dis", "Dis Hekimi Ahmet") is True
        assert match_keyword_bounded("dis", "kadikoy_dis_hekimligi") is True
        assert match_keyword_bounded("kuafor", "Erkek Kuafor Ali") is True

    def test_keyword_matching_turkish_suffix_inflection_limitation(self):
        """
        STRESS / LIMITATION TEST: Demonstrate that strict r"\\bkw\\b" fails on Turkish inflected suffixes.
        For instance, keyword 'kuafor' does NOT match 'Kuaforu' or 'klinik' does NOT match 'Klinigi'.
        """
        # 'kuafor' vs 'Kuaforu'
        assert match_keyword_bounded("kuafor", "Erkek Kuaforu Ali") is False
        # 'klinik' vs 'Klinigi'
        assert match_keyword_bounded("klinik", "Ozel Dis Klinigi") is False

    def test_keyword_matching_regex_special_characters(self):
        """STRESS: Ensure regex metacharacters in keyword do not cause invalid regex exception."""
        special_keywords = ["c++", "a&b", "(klinik)", "[special]", "dis.*hekimi"]

        for kw in special_keywords:
            try:
                res = match_keyword_bounded(kw, "C++ Yazilim ve (Klinik) Cozumleri A&B")
                assert isinstance(res, bool)
            except Exception as e:
                pytest.fail(f"Regex error for keyword '{kw}': {e}")
