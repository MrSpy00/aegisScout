import pytest
from aegisScout.discovery.noise_filter import is_noise, is_directory_url

def test_directory_url_and_name_filtering():
    # Directory URLs
    assert is_directory_url("https://www.bulurum.com/details/12345") is True
    assert is_directory_url("https://yellowpages.com.tr/arama") is True
    assert is_directory_url("https://www.firmasec.com/sektor/123") is True
    assert is_directory_url("https://www.facebook.com/pages/category/salon") is True

    # Real website URLs
    assert is_directory_url("https://www.ahmetkuafor.com") is False
    assert is_directory_url("https://www.instagram.com/dentalklinik") is False

    # Directory names
    assert is_noise({"name": "bulurumcom", "website_url": ""}) is True
    assert is_noise({"name": "Bulurum.com Detay", "website_url": ""}) is True
    assert is_noise({"name": "Yellowpages Firma Rehberi", "website_url": ""}) is True

def test_public_and_state_institution_filtering():
    # Health institutions
    assert is_noise({"name": "Kadıköy 3 Nolu Aile Sağlığı Merkezi"}) is True
    assert is_noise({"name": "Moda Sağlık Ocağı"}) is True
    assert is_noise({"name": "Kadıköy ASM"}) is True
    assert is_noise({"name": "Haydarpaşa Numune Devlet Hastanesi"}) is True
    assert is_noise({"name": "Marmara Üniversitesi Hastanesi"}) is True

    # Governmental / Municipal
    assert is_noise({"name": "İstanbul Büyükşehir Belediyesi"}) is True
    assert is_noise({"name": "Kadıköy Kaymakamlığı"}) is True
    assert is_noise({"name": "Kadıköy İlçe Emniyet Müdürlüğü"}) is True
    assert is_noise({"name": "Sosyal Güvenlik Kurumu SGK"}) is True
    assert is_noise({"name": "Caferağa Mahallesi Muhtarlığı"}) is True

    # Legitimate private businesses
    assert is_noise({"name": "Ahmet Kuaför & Güzellik Salonu"}) is False
    assert is_noise({"name": "DentKadıköy Özel Diş Kliniği"}) is False
    assert is_noise({"name": "Stüdyo Mimarlık Ltd. Şti."}) is False
    assert is_noise({"name": "Kadıköy Espresso Kafe"}) is False
