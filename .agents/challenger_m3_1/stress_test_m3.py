import sys
import os
import re
import pytest

# Ensure src directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from aegisScout.discovery.instagram_finder import (
    extract_sld,
    match_keyword_bounded,
    calculate_domain_score,
    calculate_location_score_and_penalty,
    calculate_sector_score,
    calculate_name_score,
    InstagramFinder,
)
from aegisScout.discovery.noise_filter import is_aggregator_profile


def test_extract_sld_edge_cases():
    print("\n--- 1. Testing extract_sld Edge Cases ---")

    test_cases = [
        # Standard
        ("https://www.akdenizdis.com.tr/tr", "akdenizdis"),
        ("http://subdomain.mycompany.net.tr/page", "mycompany"),
        ("https://linktr.ee/akdenizdis", "akdenizdis"),
        # Case & whitespace
        ("  HTTPS://WWW.MY-COMPANY.COM.TR/PATH  ", "my-company"),
        # Custom ports & auth credentials
        ("http://user:pass@company.com:8080/path", "company"),
        # Aggregators with query & fragment
        ("https://beacons.ai/mydentist?ref=ig#bio", "mydentist"),
        ("https://shopier.com/store_name/item/123", "store_name"),
        ("https://taplink.cc/user.name_tr", "username_tr"),
        # Empty / malformed host
        ("", ""),
        ("https://", ""),
        ("http://[::1]/path", ""),
        # Deep subdomains
        ("https://sub1.sub2.sub3.example.com.tr", "example"),
        ("https://a.b.c.d.company.com", "company"),
        # Multi-part TLDs unlisted in default set
        ("https://www.ankara.bel.tr", "ankara"),
        ("https://metu.edu.tr", "metu"),
        ("https://school.k12.tr", "school"),
        ("https://oxford.ac.uk", "oxford"),
    ]

    passed = 0
    failed = 0
    results = []
    for input_url, expected in test_cases:
        actual = extract_sld(input_url)
        ok = actual == expected
        if ok:
            passed += 1
        else:
            failed += 1
        results.append((input_url, expected, actual, ok))
        print(f"[{'PASS' if ok else 'FAIL'}] extract_sld('{input_url}') -> Got '{actual}', Expected '{expected}'")

    return results, passed, failed


def test_is_aggregator_profile_edge_cases():
    print("\n--- 2. Testing is_aggregator_profile Edge Cases ---")

    test_cases = [
        # True aggregators
        ({"username": "istanbul_kuafor_rehberi", "bio": "Kuaförler rehberi"}, True, "Known handle pattern"),
        ({"username": "turkiye_doktorlar", "bio": "Doktorlar portalı"}, True, "Known handle pattern"),
        ({"username": "saglik_dizini", "bio": "Tüm firmalar burada"}, True, "Known handle pattern"),
        ({"username": "dr_ahmet", "bio": "Türkiye rehberi portalı"}, True, "Known bio phrase"),
        ({"username": "salon_xyz", "website": "https://yellowpages.com.tr/cat"}, True, "Directory website"),

        # Potential False Positives (Legitimate businesses that might be misflagged)
        ({"username": "rehber_danismanlik", "bio": "Kişisel ve kurumsal rehberlik danışmanlık hizmetleri"}, False, "Guidance/counseling service handle starts with rehber_"),
        ({"username": "kuafor_sayfasi_official", "bio": "Güzellik salonu resmi Instagram sayfası"}, False, "Legitimate handle with _official suffix"),
        ({"username": "doktorlar_klinigi", "bio": "Müşteri portalı üzerinden online randevu alabilirsiniz."}, False, "Bio uses 'portalı' for customer portal"),
        ({"username": "hasta_portali_tr", "bio": "Hasta portalı giriş ekranı"}, False, "Uses portal in healthcare tech sense"),
    ]

    passed = 0
    failed = 0
    results = []
    for profile, expected, reason in test_cases:
        actual = is_aggregator_profile(profile)
        ok = actual == expected
        if ok:
            passed += 1
        else:
            failed += 1
        results.append((profile.get("username"), reason, expected, actual, ok))
        print(f"[{'PASS' if ok else 'FAIL'}] is_aggregator_profile(@{profile.get('username')}) [{reason}] -> Got {actual}, Expected {expected}")

    return results, passed, failed


def test_calculate_location_score_and_penalty_edge_cases():
    print("\n--- 3. Testing calculate_location_score_and_penalty Edge Cases ---")

    test_cases = [
        # Standard major city
        ("İstanbul", {"bio": "İstanbul Kadıköy", "full_name": "Klinik"}, 80, 0, "Major city match"),
        ("Ankara", {"bio": "İstanbul Kadıköy", "full_name": "Klinik"}, 40, 20, "Cross-city conflict"),

        # Multi-city bios
        ("Ankara", {"bio": "Ankara ve İstanbul şubelerimizle hizmetinizdeyiz", "full_name": "Klinik Group"}, 80, 0, "Multi-city bio target included"),
        ("İstanbul", {"bio": "İzmir, Ankara ve İstanbul salonları", "full_name": "Güzellik"}, 80, 0, "Multi-city list target included"),

        # Rare / non-major Turkish cities (not in TURKISH_MAJOR_CITIES set)
        ("Bayburt", {"bio": "Bayburt merkez kuaför", "full_name": "Bayburt Kuaför"}, 70, 0, "Rare city match (Bayburt not in major cities)"),
        ("Bayburt", {"bio": "İstanbul Kadıköy kuaför", "full_name": "İstanbul Kuaför"}, 40, 0, "Cross-city with rare target city (Bayburt)"),
        ("Bartın", {"bio": "Bartın Amasra diş kliniği", "full_name": "Amasra Diş"}, 70, 0, "Rare city match (Bartın)"),

        # Non-Turkish cities
        ("London", {"bio": "İstanbul salonu", "full_name": "Salon"}, 40, 0, "Non-Turkish target city"),

        # District without city in target
        ("Kadıköy", {"bio": "İstanbul Kadıköy Moda caddesi", "full_name": "Klinik"}, 70, 0, "District target match"),
    ]

    passed = 0
    failed = 0
    results = []
    for target_loc, profile, exp_score_min, exp_penalty, reason in test_cases:
        score, penalty = calculate_location_score_and_penalty(target_loc, profile)
        ok_score = score >= exp_score_min if exp_score_min > 50 else score <= exp_score_min
        ok_pen = penalty == exp_penalty
        ok = ok_score and ok_pen
        if ok:
            passed += 1
        else:
            failed += 1
        results.append((target_loc, profile.get("username", "test"), reason, (exp_score_min, exp_penalty), (score, penalty), ok))
        print(f"[{'PASS' if ok else 'FAIL'}] loc_score('{target_loc}', bio='{profile.get('bio')}') [{reason}] -> Got score={score}, penalty={penalty} (Expected min_score={exp_score_min}, pen={exp_penalty})")

    return results, passed, failed


def test_match_keyword_bounded_edge_cases():
    print("\n--- 4. Testing match_keyword_bounded Edge Cases ---")

    test_cases = [
        # Standard bounded match
        ("diş", "Ahmet Diş Kliniği", True, "Basic Turkish word"),
        ("diş", "Disney Plus TR Official", False, "Substring false positive check"),

        # Turkish uppercase & dot/i variations
        ("DİŞ", "Ağız ve Diş Sağlığı", True, "Uppercase keyword DİŞ"),
        ("diş", "AĞIZ VE DİŞ SAĞLIĞI POLİKLİNİĞİ", True, "Uppercase text DİŞ"),
        ("IŞIK", "Işık Fotoğrafçılık Studio", True, "Dotless I / IŞIK uppercase"),
        ("ışık", "IŞIK FOTOĞRAFÇILIK", True, "Lowercase ışık matching uppercase IŞIK"),
        ("İSTİNYE", "İstinye Park Kuaför", True, "Dotted İ uppercase"),

        # Delimiters: underscores and dots in handles
        ("kuafor", "kuafor_istanbul", True, "Handle with underscore delimiter"),
        ("kuafor", "kuafor.istanbul", True, "Handle with dot delimiter"),
        ("istanbul", "kuafor.istanbul", True, "Dot boundary second word"),

        # Special characters / Punctuation in keywords
        ("diş & çene", "Ağız Diş & Çene Cerrahisi", True, "Keyword with ampersand"),
        ("dr.", "Dr. Ahmet Yılmaz Klinik", True, "Keyword with trailing dot"),
        ("c++", "C++ Developer Community", True, "Keyword with plus signs"),
        ("bar+grill", "Kadıköy Bar+Grill Bistro", True, "Keyword with plus sign"),
    ]

    passed = 0
    failed = 0
    results = []
    for kw, text, expected, reason in test_cases:
        actual = match_keyword_bounded(kw, text)
        ok = actual == expected
        if ok:
            passed += 1
        else:
            failed += 1
        results.append((kw, text, reason, expected, actual, ok))
        print(f"[{'PASS' if ok else 'FAIL'}] match_keyword_bounded('{kw}', '{text}') [{reason}] -> Got {actual}, Expected {expected}")

    return results, passed, failed


if __name__ == "__main__":
    print("=========================================================")
    print("  aegisScout M3 Candidate Matching Adversarial Harness  ")
    print("=========================================================")

    r1, p1, f1 = test_extract_sld_edge_cases()
    r2, p2, f2 = test_is_aggregator_profile_edge_cases()
    r3, p3, f3 = test_calculate_location_score_and_penalty_edge_cases()
    r4, p4, f4 = test_match_keyword_bounded_edge_cases()

    total_p = p1 + p2 + p3 + p4
    total_f = f1 + f2 + f3 + f4
    print("\n=========================================================")
    print(f"SUMMARY: Total Passed: {total_p}, Total Failed: {total_f}")
    print("=========================================================")
