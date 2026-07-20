import pyperclip
import webbrowser
import urllib.parse
from aegisScout.core.models import Lead, Message
from aegisScout.core.database import Session, engine
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.assisted")

def send_assisted_message(lead: Lead, draft_message: str) -> bool:
    """
    Assisted Mode (Mod A): Mesajı panoya kopyalar ve Instagram DM'i tarayıcıda açar.

    Handle bulunduğunda: İşletmenin Instagram profil sayfası açılır.
    Handle bulunamadığında: Kullanıcıya açık talimat + Google arama linki verilir.
    """
    try:
        # Mesajı panoya kopyala
        pyperclip.copy(draft_message)
        logger.info(f"Draft message copied to clipboard for {lead.business_name}")

        if lead.instagram_handle:
            # Profil sayfasını aç — kullanıcı "Mesaj Gönder" düğmesine tıklar
            profile_url = f"https://www.instagram.com/{lead.instagram_handle}/"
            logger.info(f"Opening Instagram profile: {profile_url}")
            print(f"\n✅ Mesaj panoya kopyalandı!")
            print(f"   İşletme  : {lead.business_name}")
            print(f"   Profil   : {profile_url}")
            print(f"   Tarayıcıda profil açılıyor... 'Mesaj Gönder' butonuna tıklayıp mesajı yapıştırın.")
            webbrowser.open(profile_url)
        else:
            # Handle bulunamadı — kullanıcıya elle bulma talimatı ver
            google_query = urllib.parse.quote(f"{lead.business_name} Instagram")
            google_url = f"https://www.google.com/search?q={google_query}"

            print(f"\n⚠️  '{lead.business_name}' için Instagram handle bulunamadı.")
            print(f"   Mesaj panoya kopyalandı — lütfen aşağıdaki adımları takip edin:\n")
            print(f"   1. Google'da profili ara: {google_url}")
            print(f"   2. Instagram'da profili bul ve 'Mesaj Gönder'e tıkla.")
            print(f"   3. Panodan mesajı yapıştır (Ctrl+V / Cmd+V).\n")
            print(f"   📋 Mesaj içeriği (ilk 120 karakter): {draft_message[:120]}...")

            # Google arama linkini aç — genel inbox değil
            logger.warning(
                f"No instagram handle for {lead.business_name}. "
                f"Opening Google search to help user find profile."
            )
            webbrowser.open(google_url)

        return True
    except Exception as e:
        logger.error(f"Error in assisted outreach for lead {lead.id}: {e}")
        return False
