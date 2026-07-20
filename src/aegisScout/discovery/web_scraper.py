import re
import httpx
import socket
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Optional, Tuple
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.web_scraper")


async def get_domain_age_days(domain: str) -> Optional[int]:
    """
    Finds the registration age of a domain in days using a keyless RDAP lookup,
    falling back to a raw socket WHOIS query on port 43 if RDAP is unavailable.
    """
    # 1. Try RDAP first (modern REST standard)
    try:
        url = f"https://rdap.org/domain/{domain}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("events", [])
                for ev in events:
                    if ev.get("eventAction") in ("registration", "creation"):
                        date_str = ev.get("eventDate")
                        # datetime.fromisoformat supports Z in >=3.11
                        date_str = date_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(date_str)
                        dt_naive = dt.replace(tzinfo=None)
                        age = (datetime.utcnow() - dt_naive).days
                        return age
    except Exception as e:
        logger.debug(f"RDAP lookup failed for {domain}: {e}")

    # 2. Fallback to raw socket WHOIS on port 43
    try:
        def query_whois(server: str, query: str) -> str:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((server, 43))
                s.sendall((query + "\r\n").encode("utf-8"))
                response = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                s.close()
                return response.decode("utf-8", errors="ignore")
            except Exception:
                return ""

        # Query IANA to find the correct referral registry server
        iana_res = query_whois("whois.iana.org", domain)
        refer_server = "whois.iana.org"
        for line in iana_res.splitlines():
            if line.strip().lower().startswith("refer:") or line.strip().lower().startswith("whois:"):
                refer_server = line.split(":", 1)[1].strip()
                break
        
        # Fallback to common TLD registries if IANA is silent
        if refer_server == "whois.iana.org":
            tld = domain.split(".")[-1].lower()
            servers = {
                "com": "whois.verisign-grs.com",
                "net": "whois.verisign-grs.com",
                "org": "whois.pir.org",
                "info": "whois.afilias-net.info",
                "biz": "whois.neulevel.biz",
                "tr": "whois.trabis.gov.tr",
                "io": "whois.nic.io",
                "co": "whois.nic.co",
                "uk": "whois.nic.uk",
                "de": "whois.denic.de",
            }
            refer_server = servers.get(tld, "whois.iana.org")

        res = query_whois(refer_server, domain)
        if not res:
            res = query_whois("whois.verisign-grs.com", domain)

        if res:
            date_patterns = [
                r"(?:Creation Date|Created On|Created Date|Registration Time|Registration Date|creation date|created|registered|Record created on):\s*([^\n\r]+)",
                r"(?:Domain Name Creation Date):\s*([^\n\r]+)",
            ]
            for pattern in date_patterns:
                match = re.search(pattern, res, re.IGNORECASE)
                if match:
                    date_str = match.group(1).strip()
                    clean_date_str = re.sub(r"\s*(?:UTC|GMT|EST|EDT|PST|PDT|BST|EEST|EET)\s*", "", date_str)
                    clean_date_str = clean_date_str.split("T")[0]
                    for fmt in (
                        "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", 
                        "%Y.%m.%d", "%d.%m.%Y", "%d-%b-%Y", "%Y-%b-%d"
                    ):
                        try:
                            dt = datetime.strptime(clean_date_str[:10], fmt)
                            return (datetime.utcnow() - dt).days
                        except Exception:
                            pass
                    # Regex fallback if formatting differs
                    nums = re.findall(r"\d+", clean_date_str)
                    if len(nums) >= 3:
                        try:
                            if len(nums[0]) == 4:
                                dt = datetime(int(nums[0]), int(nums[1]), int(nums[2]))
                            elif len(nums[2]) == 4:
                                dt = datetime(int(nums[2]), int(nums[1]), int(nums[0]))
                            else:
                                continue
                            return (datetime.utcnow() - dt).days
                        except Exception:
                            pass
    except Exception as e:
        logger.debug(f"Socket WHOIS lookup failed for {domain}: {e}")

    return None


class WebScraper:
    """
    Scrapes the target business website for details like Instagram handle, phone numbers,
    emails, and technologies, performing technical audits up to a depth of 2.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    # -------------------------------------------------------------------------
    # Phone extraction helpers (regex bank, in priority order)
    # -------------------------------------------------------------------------
    _TR_MOBILE_RE = re.compile(
        r"(?:\+?90|0)?\s*5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}"
    )
    _INTL_PHONE_RE = re.compile(
        r"\+?\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}"
    )

    def _extract_phone(self, text: str) -> Optional[str]:
        """
        Find the first plausible phone number in arbitrary text.
        """
        if not text:
            return None
        m = self._TR_MOBILE_RE.search(text)
        if m:
            return m.group(0).strip()
        m = self._INTL_PHONE_RE.search(text)
        if m:
            return m.group(0).strip()
        return None

    async def scrape_site(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[int], str]:
        """
        Scrapes a website and returns (instagram_handle, phone, quality_score, notes).
        Maintains backwards compatibility by calling audit_site.
        """
        audit = await self.audit_site(url)
        return audit["instagram_handle"], audit["phone"], audit["quality_score"], audit["notes"]

    async def audit_site(self, url: str) -> dict:
        """
        Runs full technical audit on the site using a BFS crawler (up to depth 2, max 15 pages).
        """
        result = {
            "instagram_handle": None,
            "phone": None,
            "email": None,
            "quality_score": 0,
            "notes": "",
            "technologies": "Custom HTML/CSS",
            "kvkk_compliant": False,
            "has_broken_links": False,
            "broken_links_details": "",
            "page_speed_desktop": 90,
            "page_speed_mobile": 80,
            "domain_age_days": None,
            "is_new_domain": False,
            "opportunities": ""
        }

        url_clean = url.strip() if url else ""
        if not url_clean or url_clean.lower() in ["", "-", "n/a", "none", "null", "undefined", "blank", "about:blank"]:
            result["notes"] = "Web sitesi adresi geçersiz veya tanımlanmamış."
            return result

        if not url_clean.startswith("http"):
            url_clean = "http://" + url_clean
        url = url_clean

        from urllib.parse import urljoin, urlparse
        base_domain = urlparse(url).netloc
        
        # Determine Domain Age
        domain_name = base_domain
        if domain_name.startswith("www."):
            domain_name = domain_name[4:]
        try:
            age_days = await asyncio.to_thread(get_domain_age_days, domain_name)
            result["domain_age_days"] = age_days
            if age_days is not None:
                result["is_new_domain"] = age_days < 90
        except Exception as e:
            logger.debug(f"Domain age check failed: {e}")

        # BFS Crawl Setup
        import asyncio
        visited = set()
        queue = [(url, 0)]
        
        all_emails = set()
        all_phones = set()
        detected_techs = set()
        instagram_handles = []
        broken_links = []
        
        has_viewport = False
        has_ssl = False
        has_desc = False
        has_sufficient_content = False
        
        homepage_html = ""
        homepage_soup = None
        notes = []
        
        while queue and len(visited) < 15:
            curr_url, depth = queue.pop(0)
            if curr_url in visited:
                continue
            visited.add(curr_url)
            
            # Download page
            html = ""
            verify_ssl = True
            try:
                try:
                    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, verify=True) as client:
                        resp = await client.get(curr_url, headers=self.headers)
                except httpx.SSLError:
                    verify_ssl = False
                    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, verify=False) as client:
                        resp = await client.get(curr_url, headers=self.headers)
                    if curr_url == url:
                        notes.append("SSL sertifikası geçersiz veya süresi dolmuş.")
                        
                if resp.status_code == 200:
                    html = resp.text
                    if curr_url == url:
                        homepage_html = html
                        resp_url = getattr(resp, "url", None)
                        scheme = getattr(resp_url, "scheme", "https" if str(resp_url or "").lower().startswith("https") else "http") if resp_url else "http"
                        has_ssl = verify_ssl and (scheme == "https" or curr_url.startswith("https"))
                else:
                    if curr_url != url:
                        broken_links.append(curr_url)
            except Exception as e:
                logger.debug(f"Crawl failed for {curr_url}: {e}")
                if curr_url == url:
                    notes.append(f"Web sitesine erişilemedi: {e}")
                else:
                    broken_links.append(curr_url)
                continue
                
            if not html:
                continue
                
            soup = BeautifulSoup(html, "html.parser")
            if curr_url == url:
                homepage_soup = soup
                
            # Extract E-mails
            # A) mailto links
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().startswith("mailto:"):
                    email_addr = href.replace("mailto:", "").strip().split("?")[0]
                    if "@" in email_addr:
                        all_emails.add(email_addr)
            # B) Regex scan
            email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            for m in email_pattern.finditer(html):
                email_addr = m.group(0).strip()
                if not any(email_addr.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")):
                    all_emails.add(email_addr)
                    
            # Extract Phones
            # A) tel links
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().startswith("tel:"):
                    phone_num = href.replace("tel:", "").strip()
                    if phone_num:
                        all_phones.add(phone_num)
            # B) Regex scan
            body_text = soup.body.get_text() if soup.body else soup.get_text()
            phone_val = self._extract_phone(body_text)
            if phone_val:
                all_phones.add(phone_val)
                
            # Extract Instagram links
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                if "instagram.com" in href:
                    match = re.search(r"instagram\.com/([a-zA-Z0-9_\.]+)", href)
                    if match:
                        handle = match.group(1)
                        if handle not in ["p", "tv", "reel", "explore", "developer", "about"]:
                            if handle not in instagram_handles:
                                instagram_handles.append(handle)
                                if curr_url != url:
                                    notes.append(f"Instagram adresi iletişim/hakkımızda sayfasından bulundu: {curr_url}")
                                
            # Detect Technologies
            if "/wp-content/" in html.lower() or "/wp-includes/" in html.lower() or 'name="generator" content="wordpress"' in html.lower():
                detected_techs.add("WordPress")
            if "webflow.com" in html.lower() or "data-wf-page" in html.lower():
                detected_techs.add("Webflow")
            if "ghost.org" in html.lower() or "ghost-sdk" in html.lower():
                detected_techs.add("Ghost")
            # Ecommerce
            if "cdn.shopify.com" in html.lower() or "shopify.shop" in html.lower():
                detected_techs.add("Shopify")
            if "woocommerce" in html.lower() or "wp-content/plugins/woocommerce" in html.lower():
                detected_techs.add("WooCommerce")
            if "wix.com" in html.lower() or "wixpress" in html.lower():
                detected_techs.add("Wix")
            if "magento" in html.lower() or "magento_themes" in html.lower():
                detected_techs.add("Magento")
            # Analytics
            if "googletagmanager.com/gtag/js" in html.lower() or "window.gtag" in html.lower() or "analytics.js" in html.lower() or "g-adwords" in html.lower():
                detected_techs.add("Google Analytics 4")
            if "mc.yandex.ru/metrika" in html.lower() or "ym(" in html.lower():
                detected_techs.add("Yandex Metrica")
            if "hotjar.com" in html.lower() or "hj(" in html.lower() or "_hjsettings" in html.lower():
                detected_techs.add("Hotjar")
            # Ads
            if "connect.facebook.net" in html.lower() or "fbq(" in html.lower() or "fbevents.js" in html.lower():
                detected_techs.add("Facebook Pixel")
            if "tiktok.com/i18n/pixel" in html.lower() or "ttq.load" in html.lower() or "ttq(" in html.lower():
                detected_techs.add("TikTok Pixel")
            if "googletagmanager.com/gtm.js" in html.lower() or "gtm.js?id=" in html.lower():
                detected_techs.add("Google Tag Manager")

            # Homepage checks
            if curr_url == url:
                viewport = soup.find("meta", attrs={"name": "viewport"})
                has_viewport = viewport is not None
                
                desc = soup.find("meta", attrs={"name": "description"})
                has_desc = desc is not None
                
                has_sufficient_content = len(html) > 5000
                
            # Queue internal subpages
            if depth < 2:
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("tel:") or href.startswith("mailto:"):
                        continue
                    full_link = urljoin(curr_url, href)
                    link_domain = urlparse(full_link).netloc
                    
                    if link_domain == base_domain:
                        is_priority = any(k in full_link.lower() for k in ["contact", "iletisim", "about", "hakkimizda", "privacy", "terms", "gizlilik"])
                        if full_link not in visited and not any(q[0] == full_link for q in queue):
                            if is_priority:
                                queue.insert(0, (full_link, depth + 1))
                            else:
                                queue.append((full_link, depth + 1))

        # Compile final results
        result["instagram_handle"] = instagram_handles[0] if instagram_handles else None
        result["phone"] = list(all_phones)[0] if all_phones else None
        result["email"] = list(all_emails)[0] if all_emails else None
        
        # Calculate Quality Score
        quality_score = 0
        if has_viewport:
            quality_score += 30
            notes.append("Mobil uyumlu (viewport mevcut).")
        else:
            notes.append("Mobil uyumsuz olabilir (viewport eksik).")
            
        if has_ssl:
            quality_score += 30
            notes.append("Güvenli bağlantı (SSL/HTTPS mevcut).")
        else:
            notes.append("Güvensiz bağlantı (SSL/HTTPS eksik).")
            
        if has_sufficient_content:
            quality_score += 20
            notes.append("İçerik yoğunluğu yeterli.")
        else:
            notes.append("İçerik miktarı yetersiz.")
            
        if has_desc:
            quality_score += 20
            notes.append("SEO meta açıklaması mevcut.")
        else:
            notes.append("SEO meta açıklaması eksik.")
            
        result["quality_score"] = min(max(quality_score, 0), 100)
        
        # Technologies
        if not detected_techs:
            detected_techs.add("Custom HTML/CSS")
        result["technologies"] = ", ".join(sorted(list(detected_techs)))
        
        # Broken links
        if broken_links:
            result["has_broken_links"] = True
            result["broken_links_details"] = ", ".join(list(set(broken_links))[:5])
            notes.append(f"Kırık linkler tespit edildi: {result['broken_links_details']}")
        
        # PageSpeed Insights
        desktop_speed = await self._get_page_speed(url, "desktop")
        mobile_speed = await self._get_page_speed(url, "mobile")
        
        if desktop_speed is not None:
            result["page_speed_desktop"] = desktop_speed
        else:
            result["page_speed_desktop"] = self._estimate_page_speed_locally(homepage_html, homepage_soup or BeautifulSoup("", "html.parser"))
            
        if mobile_speed is not None:
            result["page_speed_mobile"] = mobile_speed
        else:
            result["page_speed_mobile"] = max(40, result["page_speed_desktop"] - 10)

        # Opportunities / Issues Analysis for LLM Prompt
        opportunities_list = []
        if "Facebook Pixel" not in detected_techs:
            opportunities_list.append("Web sitenizde Facebook Pixel kodu yüklü değil, reklam dönüşümleri ölçülemiyor.")
        if "Google Analytics 4" not in detected_techs and "Google Tag Manager" not in detected_techs:
            opportunities_list.append("Google Analytics veya Google Tag Manager kurulu değil, site trafik analizi yapılamıyor.")
        if "Hotjar" not in detected_techs:
            opportunities_list.append("Kullanıcı davranış analizi aracı Hotjar kurulu değil.")
        if result["has_broken_links"]:
            opportunities_list.append(f"Web sitenizde bazı iç linkler kırık: {result['broken_links_details']}.")
        if result["quality_score"] < 70:
            opportunities_list.append(f"Mobil uyumluluk veya SEO etiketleri eksik, genel kalite skoru düşük ({result['quality_score']}/100).")
        if result["page_speed_mobile"] < 60:
            opportunities_list.append(f"Mobil site yüklenme hızı yavaş ({result['page_speed_mobile']}/100).")
        if result["is_new_domain"]:
            opportunities_list.append(f"Alan adınız son 3 ay içinde alınmış çok yeni bir girişim ({result['domain_age_days']} günlük).")

        result["opportunities"] = " | ".join(opportunities_list)
        result["notes"] = "; ".join(notes)
        result["kvkk_compliant"] = self._check_kvkk(homepage_html)
        
        return result

    def _detect_technologies(self, html: str) -> str:
        # Legacy placeholder method kept for backwards compatibility
        return "Custom HTML/CSS"

    def _check_kvkk(self, html: str) -> bool:
        keywords = ["kvkk", "gdpr", "çerez", "cookie", "aydınlatma metni", "gizlilik politikası", "privacy policy"]
        html_lower = html.lower()
        return any(kw in html_lower for kw in keywords)

    async def _check_broken_links(self, base_url: str, soup: BeautifulSoup) -> Tuple[bool, str]:
        # Legacy placeholder method kept for backwards compatibility
        return False, ""

    async def _get_page_speed(self, url: str, strategy: str) -> Optional[int]:
        import urllib.parse
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={urllib.parse.quote(url)}&strategy={strategy}"
        try:
            async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    score = data["lighthouseResult"]["categories"]["performance"]["score"]
                    return int(score * 100)
        except Exception:
            pass
        return None

    def _estimate_page_speed_locally(self, html: str, soup: BeautifulSoup) -> int:
        score = 100
        scripts_count = len(soup.find_all("script"))
        score -= min(15, scripts_count * 1)
        links_count = len(soup.find_all("link", rel="stylesheet"))
        score -= min(15, links_count * 2)
        images_count = len(soup.find_all("img"))
        score -= min(15, images_count * 1.5)
        html_size_kb = len(html or "") / 1024
        if html_size_kb > 200:
            score -= min(25, int((html_size_kb - 200) / 20))
        return int(max(40, score))

