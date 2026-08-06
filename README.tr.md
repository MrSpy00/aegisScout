# aegisScout — İşletme Keşif, OSINT Analiz ve Satış Otomasyonu Platformu

[![English README](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Türkçe README](https://img.shields.io/badge/Dil-Türkçe-red.svg)](README.tr.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://www.python.org/)

**aegisScout**; web tasarımı, yazılım geliştirme, dijital pazarlama ve SEO hizmeti sunan ajanslar ile freelancerlar için özel olarak geliştirilmiş, **kendi bilgisayarınızda çalışan (self-hosted)**, %100 yerel ve gizlilik odaklı bir müşteri keşif, derin OSINT araştırması, AI destekli metin yazımı ve çok kanallı outreach otomasyon platformudur.

---

## 🖼️ Masaüstü Arayüzü Ekran Görüntüleri

Uygulama masaüstü arayüzüne ait canlı panel görüntüleri (tüm veriler temsilidir):

### 📊 Dashboard & Keşif Radarı
![Dashboard](assets/screenshot_dashboard.png)

### 📋 Müşteri Adayları Yöneticisi (Leads Manager)
![Leads Manager](assets/screenshot_leads.png)

### 🎯 Kampanya Yöneticisi (Campaigns Manager)
![Campaigns Manager](assets/screenshot_campaigns.png)

### ⚙️ Ayarlar ve Yapılandırma Paneli (Settings)
![Settings Panel](assets/screenshot_settings.png)

---

## ✨ Kapsamlı Özellik Detayları

### 1. İşletme Keşif Motoru & Sıfır-Key OSINT Çerçevesi

- **Harita, Geocoding ve Yer Tespiti:**
  - **OpenStreetMap (OSM) & Overpass API:** Harici API anahtarı gerektirmeden sektör ve konuma göre sınırsız işletme taraması yapar.
  - **Komoot Photon API (`photon.komoot.io`):** Canlı adres ve geocoding koordinat dönüşümlerini sıfır key ile gerçekleştirir.
  - **BigDataCloud & Country.is:** İstemci taraflı ters geocoding ve IP tabanlı konum tespiti sunar.
  - **Google Places API & SerpApi Local 3-Pack:** İsteğe bağlı olarak Google Haritalar ve Local 3-Pack verilerini çeker; API anahtarı yoksa otomatik olarak ücretsiz web kazıyıcılara geçer.

- **Sıfır-Key Derin OSINT Servisleri:**
  - **ICANN RDAP (`rdap.org`):** Domain kayıt yaşı, tescil firması ve WHOIS detaylarını sorgular.
  - **Cloudflare DNS-over-HTTPS (`1.1.1.1`):** Hedef işletmenin MX altyapısını (Google Workspace, Microsoft 365, cPanel, ProtonMail) ve SPF/DMARC güvenlik kayıtlarını analiz eder.
  - **Shodan InternetDB (`internetdb.shodan.io`):** Açık portları, bilinen zafiyetleri (CVE) ve sunucu etiketlerini API anahtarsız tespit eder.
  - **crt.sh Sertifika Taraması:** SSL/TLS şeffaflık günlüklerinden işletmeye ait alt alan adlarını (subdomains) çıkartır.
  - **Mozilla Observatory & Wayback Machine:** Web güvenlik skorlarını ve geçmiş site arşivlerini denetler.
  - **IP-API & Ipify:** Sunucu IP adresini, hosting sağlayıcısını ve coğrafi lokasyonunu belirler.

- **Görsel Zenginleştirme:**
  - **Google Favicon API & Unavatar:** 128x128 kurumsal logoları ve sosyal medya profil resimlerini otomatik çeker.
  - **UI-Avatars & Microlink & Thum.io:** Dinamik renkli harf ikonları, OpenGraph özetleri ve canlı mobil/masaüstü web site önizleme kartları oluşturur.

---

### 2. Çok Kanallı İletişim & Waterfall Zenginleştirme (Cascade)

- **Kademeli E-posta Keşif Şelalesi (Waterfall Cascade):**
  1. **Web Scraping:** Hedef web sitesinin tüm sayfalarını derinlemesine tarayarak e-posta ve iletişim formlarını tespit eder.
  2. **Arama Engine Sorgusu:** Google / DuckDuckGo aramaları üzerinden işletmeye ait kamu e-postalarını sorgular.
  3. **Sosyal Biyo Kazıma:** Instagram, Facebook ve LinkedIn biyografilerinden iletişim bilgilerini ayıklar.
  4. **Akıllı Erken Çıkış (Early Exit):** E-posta adresi herhangi bir aşamada bulunduğunda sonraki adımlar atlanır, kaynak tüketimi önlenir.

- **Derin Sosyal Medya İletişim Taraması:**
  - Web siteleri ve açık kaynaklardan Instagram, Facebook, LinkedIn, Twitter/X, TikTok, Telegram, YouTube, GitHub, Medium, Substack, Behance, Dribbble, Snapchat, Spotify ve Twitch profillerini otomatik tespit eder ve işletme kartı ile eşleştirir.

- **Telefon & Veri Sızıntısı Analizi (Phone & Breach Intel):**
  - **Yerel Telefon Doğrulama:** `phonenumbers` kütüphanesi ile offline operatör, ülke kodu ve biçimlendirme doğrulaması yapar; WhatsApp (`wa.me`) ve Telegram (`t.me`) bağlantılarını kontrol eder.
  - **Sızıntı Denetimi:** HIBP Pwned Passwords ve XposedOrNot servisleri ile e-posta adreslerinin kamuya açık veri ihlallerinde yer alıp almadığını sorgular.

---

### 3. Yerel E-posta Doğrulama ve Teslim Edilebilirlik Motoru

- **4 Aşamalı Yerel Doğrulama:**
  1. **Regex & Biçim Denetimi:** E-posta söz diziminin standartlara uygunluğunu doğrular.
  2. **Geçici (Disposable) Domain Tespiti:** 30+ bilinen tek kullanımlık e-posta sağlayıcısını engeller (`data/disposable_domains.txt` ile genişletilebilir).
  3. **DNS MX Sorgusu:** Domainin aktif e-posta sunucu kayıtlarını kontrol eder.
  4. **Socket Tabanlı SMTP Handshake Simülasyonu:** Gerçek e-posta göndermeden `HELO`, `MAIL FROM`, `RCPT TO` komutları ile e-posta kutusunun varlığını doğrular.
- **%100 Ücretsiz & API'siz:** Tüm işlemler doğrudan Python socket ve dnspython kütüphaneleriyle yerel olarak yürütülür.

---

### 4. Multimodal Ekran Denetimi & Tasarım Analizi (Screen Audit)

- **Playwright ile Görsel Yakalama:** Hedef web sitesinin masaüstü ekran görüntüsünü headless Chromium ile yakalar ve kaydeder.
- **Gemini Vision AI Görsel Analizi:** Ekran görüntüsünü yapay zeka ile analiz ederek mobil uyumluluk sorunlarını, zayıf renk kontrastlarını, tipografi hatalarını ve eksik CTA (Call-to-Action) butonlarını tespit eder.
- **Yerel Sezgisel Skorlama:** Gemini API bulunmadığı durumlarda sayfa açılış hızı, kırık bağlantılar ve SEO etiketleri üzerinden **100 üzerinden Web Sitesi Kalite Skoru** hesaplar.
- **Satış Kancası Üretimi (Outreach Hook):** Tespit edilen tasarım eksikliklerine dayanarak yüksek dönüşümlü, kişiselleştirilmiş ilk temas cümleleri oluşturur.

---

### 5. Çoklu-Ajan AI Metin Yazarı & Yerel RAG Bilgi Tabanı

- **3 Ajanlı Yapay Zeka İş Akışı:**
  - **Inspector (İncelemeci):** İşletmenin teknik ve tasarım fırsatlarını raporlar.
  - **Copywriter (Yazar):** İşletmeye özel teklif ve e-posta taslağını oluşturur.
  - **Editor (Editör):** Yapay zeka jargonunu, klişe selamlaşmaları ve uydurma verileri temizler; doğal insan dili formatına getirir.

- **Yerel RAG (Retrieval-Augmented Generation) Bilgi Tabanı:**
  - `data/knowledge_base/` klasöründeki `.txt`, `.md` ve `.pdf` formatındaki portföy ve referans dosyalarını tarar ve indeksler.
  - **Çift Motorlu Arama:** Offline TF-IDF Cosine Similarity ve opsiyonel Vektör Embedding (Ollama / Gemini API) ile arama yapar.

- **Ürün Fikirleri Motoru:**
  - Keşfedilen her işletme için Türkiye pazarına uygun TL fiyat tahminli 2-3 adet özel yazılım/dijital ürün fikri, kapıda söylenecek satış kancası ve müşteri itirazlarına yanıtlar üretir.

---

### 6. Çoklu LLM Yönlendirici (LLM Router) & Kota Yönetimi

- **Desteklenen Yapay Zeka Sağlayıcıları:**
  - **OpenRouter API** (Açık kaynak ve ticari modellere tek anahtarla erişim)
  - **Google Gemini API** (Gemini 2.5 Flash ile yüksek hızlı analiz)
  - **Groq API** (Llama-3.3-70b ile ultra düşük gecikme)
  - **Mistral AI API** (Mistral Large ile kurumsal akıl yürütme)
  - **DeepSeek API** (Maliyet etkin derin analiz)
  - **OpenAI API** (GPT-4o & GPT-4o mini)
  - **Anthropic Claude API** (Claude 3.5 Haiku)
  - **Ollama** (Tamamen yerel, ücretsiz ve internet gerektirmeyen çevrimdışı LLM desteği)

- **Yedekli Yönlendirme (Failover) ve API Key Rotasyonu:**
  - Virgülle ayrılmış birden fazla API anahtarını otomatik döndürür. Birincil sağlayıcıda kesinti veya kota sınırı yaşandığında sistem otomatik olarak ikincil yedek sağlayıcıya geçer.

---

### 7. Erişim Modları & Çok Kanallı Otomasyon

- **Mod A (Yardımcı Erişim — Varsayılan & %100 Güvenli):**
  - AI tarafından üretilen özelleştirilmiş mesajı panoya kopyalar ve tek tıkla işletmenin Instagram DM veya WhatsApp tarayıcı sayfasını açar.
- **Mod B (Tam Otomasyon — Opsiyonel):**
  - Simüle edilmiş Instagram API (`instagrapi`) kullanarak doğrudan veritabanından oturum açar ve belirlenen günlük limitler dahilinde otomatik DM gönderir.
- **WhatsApp Web & LinkedIn Playwright Otomasyonu:**
  - Kalıcı tarayıcı profilleri (persistent context) kullanarak WhatsApp Web üzerinden doğrudan mesaj gönderir ve LinkedIn üzerinde otomatik bağlantı isteği ("Connect") oluşturur.

---

### 8. SMTP Hesap Havuzu, Takip Dizileri ve P2P Isıtma (Warmup)

- **SMTP Hesap Havuzu & Saatlik Limitler:**
  - Veritabanındaki SMTP hesapları arasında otomatik yük dağıtımı yapar; hesap başına saatlik maksimum 5 e-posta gönderim limiti uygular. Şifreler veritabanında AES-256 Fernet ile saklanır.
- **Çok Aşamalı Soğuk E-posta Dizileri:**
  - İlk e-posta, 1. Takip (3 gün sonra) ve 2. Takip (7 gün sonra) şeklinde yapılandırılabilir takip zinciri çalıştırır. Gelen yanıt algılandığında takip e-postaları otomatik olarak durdurulur.
- **P2P E-posta Isıtma Motoru (Warmup):**
  - Tanımlı SMTP hesapları arasında doğal dilde e-posta trafiği simüle eder. IMAP üzerinden Spam/Junk klasörlerini tarayarak düşen mesajları Gelen Kutusu'na taşır, okundu işaretler ve alan adı itibarını yükseltir.

---

### 9. Arka Plan Görev Kuyruğu & Zamanlanmış Görev Motoru (Cron)

- **Async Task Queue:** Tüm arka plan işlemlerini (tarama, analiz, gönderim) tek bir event loop üzerinde `pending -> running -> completed / failed` durumlarıyla yönetir. Görevler duraklatılabilir veya iptal edilebilir.
- **Zamanlayıcı (Cron Manager):** Düzenli müşteri keşfi, otomatik takip e-postaları ve gelen kutusu denetimlerini belirlenen zaman aralıklarında otomatik çalıştırır.

---

### 10. Modern Masaüstü Grafik Arayüzü & SQLite WAL Veritabanı

- **PyWebView Tabanlı Dark Mode GUI:** Pürüzsüz geçişlere sahip modern masaüstü arayüzü. Parametresiz çalıştırıldığında konsol pencerelerini gizleyerek yerel pencere olarak açılır.
- **9 Dilde Tam i18n Desteği:** Türkçe, İngilizce, Almanca, İspanyolca, Fransızca, Arapça, Çince, Rusça ve Hintçe arayüz metinleri. Arapça dilinde otomatik RTL (sağdan sola) düzen.
- **SQLite WAL & SingletonPool / NullPool:** `PRAGMA journal_mode=WAL;` ve bağlantı havuzu optimizasyonları ile veritabanı kilitlenmelerini sıfıra indirir.

---

## 🔒 Güvenlik, Gizlilik ve Sıkılaştırma

- **%100 Yerel Veri Depolama:** Tüm veriler, aday listeleri, veritabanı kayıtları ve ayarlar sadece sizin bilgisayarınızdaki SQLite veritabanında (`data/aegisScout.db`) saklanır.
- **Gizli Anahtar Sınırı (Secrets Boundary):** PyWebView JS köprüsüne hiçbir API anahtarı veya şifre sızdırılmaz. Form verileri doğrudan `.env` dosyasına yazılır.
- **AES-256 Fernet Şifreleme:** Oturum verileri, SMTP şifreleri ve hassas kimlik bilgileri AES-256 Fernet jetonları ile veritabanında şifrelenir.

---

## 🛠️ Kurulum ve Yapılandırma

### 1. Gereksinimler
- **Python 3.11** veya üzeri
- `uv` paket yöneticisi (Önerilen hızlı kurulum aracı)

### 2. Kurulum Adımları

```bash
# Depoyu klonlayın ve proje dizinine gidin
git clone https://github.com/MrSpy00/aegisScout.git
cd aegisScout

# Temel Kurulum (Mod A - Yardımcı Erişim)
uv sync

# Masaüstü Grafik Arayüzü (GUI) dahil kurulum
uv sync --extra gui

# Tam Otomasyon (Mod B) dahil kurulum
uv sync --extra mod-b

# Geliştirici paketi dahil tam kurulum
uv sync --extra dev
```

> **Alternatif Pip Kurulumu:** `pip install -e .`

### 3. Yapılandırma Dosyaları
1. `.env` dosyasını oluşturun:
   ```bash
   copy .env.example .env
   ```
2. `.env` dosyasını düzenleyerek ilgili API anahtarlarınızı ekleyin.
3. `config.toml` dosyasını yapılandırın:
   ```bash
   copy config\config.example.toml config\config.toml
   ```

---

## 💻 Kullanım Kılavuzu (CLI & GUI)

### Masaüstü Uygulamasını Başlatma
Doğrudan GUI ekranını açmak için executable dosyasına çift tıklayın veya terminalde parametresiz çalıştırın:
```bash
python src/aegisScout/main.py
# Veya derlenmiş EXE:
dist/aegisScout.exe
```

### CLI Komutları

```bash
# 1. İşletme Keşfetme
aegisScout discover --sector "kuaför" --location "Kadıköy, İstanbul" --radius 5

# 2. Kampanya Yönetimi
aegisScout campaign create --name "Kadıköy Salonları" --sector "kuaför" --location "Kadıköy"
aegisScout campaign list
aegisScout campaign assign --campaign-id 1 --auto-filter

# 3. Müşteri Araştırma ve AI Analizi
aegisScout research --lead-id 1
aegisScout research --lead-id 1 --force

# 4. Inceleme ve İletişim
aegisScout review
aegisScout send --lead-id 1

# 5. Waterfall E-posta Zenginleştirme
aegisScout waterfall --lead-id 1

# 6. Web Görsel Denetimi (Multimodal Audit)
aegisScout audit --lead-id 1

# 7. E-posta Doğrulama (Local SMTP Handshake)
aegisScout verify "ornek@firma.com"

# 8. E-posta Isıtma (P2P Warmup)
aegisScout warmup

# 9. Arka Plan Görev Yönetimi
aegisScout tasks list
aegisScout tasks cancel <task_id>

# 10. Verileri Dışa Aktarma
aegisScout export --output data/exports/leads.csv
```

---

## ⚖️ Kullanım Şartları ve Yasal Uyarı

- **Instagram ToS Uyarısı:** Mod B (Tam Otomasyon) özelliğinin kullanımı Meta/Instagram Kullanım Koşullarını ihlal edebilir. Hesap güvenliği için günlük limitlere uyulması (maks. 15-20 DM/gün) ve yedek hesaplar kullanılması önerilir.
- **Yasal Uyum (KVKK & İYS & GDPR):** Toplanan verilerin işlenmesi ve soğuk e-posta gönderimi aşamalarında Kişisel Verilerin Korunması Kanunu (KVKK), İleti Yönetim Sistemi (İYS) ve ilgili veri koruma mevzuatına uyulması kullanıcının sorumluluğundadır.

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakabilirsiniz.
