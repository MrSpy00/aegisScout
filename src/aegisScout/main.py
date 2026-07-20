"""
aegisScout — CLI entry point.

Run as:
  - Console script:    aegisScout [--help] [COMMAND]
  - Module:            python -m aegisScout.main [--help] [COMMAND]
  - Help per command:  aegisScout <command> --help

Design notes:
  * Heavy/outreach modules (InstagramClient, Mod B deps) are imported lazily
    so the bare CLI help + Mod A workflows don't require the optional `mod-b`
    extra to be installed.
  * Database init is idempotent and lazy: it runs once per process on the
    first command that needs it (via `_ensure_db()`), not on import.
  * `app()` is a Typer object and is the module-level entry point exposed
    to the console_scripts entry `aegisScout = "aegisScout.main:app"`.
  * GUI auto-launches when no subcommand is passed (replaces the old
    `if __name__ == "__main__"` no-args handler).
"""

from __future__ import annotations

import os
import sys
import asyncio
import csv
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from sqlmodel import Session, select, col

from aegisScout import __version__
from aegisScout.core.config import settings
from aegisScout.core.database import init_db, engine
from aegisScout.core.models import Lead, Message, ActivityLog, Campaign
from aegisScout.core.toml_config import config_data
from aegisScout.cli import commands
from aegisScout.outreach.assisted_mode import send_assisted_message
from aegisScout.utils.logger import get_logger
from aegisScout.utils.email_verifier import verify_email
from aegisScout.core.waterfall import run_waterfall_enrichment
from aegisScout.core.screen_audit import run_website_screen_audit
from aegisScout.outreach.warmup import run_p2p_warmup_cycle

logger = get_logger("main")

# ---------------------------------------------------------------------------
# Console + Typer app
# ---------------------------------------------------------------------------
app = typer.Typer(
    name="aegisScout",
    help=(
        "aegisScout — Self-hosted business discovery, analysis & outreach CLI.\n\n"
        "Run with no arguments to launch the desktop GUI. Use --help on any "
        "command to see usage, examples, and risk warnings."
    ),
    add_completion=False,
    no_args_is_help=False,   # We handle the no-args case in the callback to launch GUI.
    rich_markup_mode="rich",
)
console = Console()
err_console = Console(stderr=True, style="bold")

# ---------------------------------------------------------------------------
# Lazy / idempotent helpers
# ---------------------------------------------------------------------------
_db_initialized: bool = False


def _ensure_db() -> None:
    """Initialise the database once per process. Idempotent."""
    global _db_initialized
    if _db_initialized:
        return
    try:
        init_db()
        _db_initialized = True
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        err_console.print(f"[bold red]Veritabanı başlatılamadı:[/bold red] {e}")
        raise typer.Exit(code=1)


def _print_banner() -> None:
    """Print the branded ASCII banner to stderr. Uses aegisSoft gold (#d4af37)."""
    banner_text = (
        "[bold #d4af37]  __ _  ___  __ _ _ ___ ___   ___ ___  _   _ |_  [/bold #d4af37]\n"
        "[bold #d4af37] / _` / _ \\/ _` | / __/ __| / __/ _ \\| | | |  _|[/bold #d4af37]\n"
        "[bold #d4af37]| (_| |  __/ (_| | \\__ \\__ \\| (_| (_) | |_| | |_ [/bold #d4af37]\n"
        "[bold #d4af37] \\__,_ \\___|\\__, |_|___/___/ \\___\\___/ \\__,_|\\__|[/bold #d4af37]\n"
        "[bold #d4af37]            |___/                                [/bold #d4af37]\n"
        f"[dim]v{__version__}  ·  Self-hosted business discovery & outreach[/dim]\n"
        f"[dim #d4af37]© aegisSoft  ·  local-only  ·  no cloud[/dim #d4af37]"
    )
    panel = Panel(
        banner_text,
        border_style="#d4af37",
        padding=(0, 2),
        expand=False,
    )
    try:
        err_console.print(panel)
    except Exception:
        # Fallback to plain stderr if Rich misbehaves in any environment
        sys.stderr.write("aegisScout\n")


# ---------------------------------------------------------------------------
# Safe DM text fallback (deterministic, no AI call required)
# ---------------------------------------------------------------------------
def _safe_fallback_text(business_name: str, sector: Optional[str]) -> str:
    """Return a deterministic Turkish DM fallback when AI generation fails/returns empty."""
    first = (business_name or "İşletme").split()[0]
    sec = sector or "bu sektör"
    return (
        f"Merhaba {first}, {sec} alanındaki son çalışmalarınızı ilgiyle takip ediyorum."
    )


# ---------------------------------------------------------------------------
# Top-level app callback — runs before any subcommand
# ---------------------------------------------------------------------------
def _should_skip_db(ctx: typer.Context) -> bool:
    """Return True if the current invocation does not require database initialization."""
    if "--help" in sys.argv or "-h" in sys.argv:
        return True
    
    current = ctx
    while current:
        if current.resilient_parsing:
            return True
        if any(h in current.args for h in ("--help", "-h")):
            return True
        current = current.parent  # type: ignore[assignment]

    args_list = sys.argv[1:]
    all_words = set(args_list)
    if ctx.args:
        all_words.update(ctx.args)
    if "version" in all_words or "docs" in all_words:
        return True
        
    return False


@app.callback(invoke_without_command=True)
def _app_callback(ctx: typer.Context) -> None:
    """
    Global app callback. Runs once before any subcommand.

    - Prints the aegisScout banner to stderr.
    - If no subcommand was passed, launches the desktop GUI.
    - Initialises the database (idempotent).
    """
    _print_banner()
    if not _should_skip_db(ctx):
        _ensure_db()

    # When invoked with no subcommand (e.g. plain `aegisScout`), open the GUI.
    if ctx.invoked_subcommand is None:
        try:
            from aegisScout.gui import start_gui
        except Exception as e:
            err_console.print(f"[bold red]GUI başlatılamadı:[/bold red] {e}")
            raise typer.Exit(code=1)
        start_gui()
        raise typer.Exit()


# ---------------------------------------------------------------------------
# `version` command
# ---------------------------------------------------------------------------
@app.command(name="version")
def version() -> None:
    """Print the aegisScout version and exit."""
    rprint(f"[bold #d4af37]aegisScout[/bold #d4af37] [white]v{__version__}[/white]")


# ---------------------------------------------------------------------------
# `discover` — Business discovery (no Mod B risk)
# ---------------------------------------------------------------------------
@app.command()
def discover(
    sector: str = typer.Option(
        ..., "--sector", "-s",
        help="Sektör (tek veya virgülle ayrılmış liste, ör. 'kuaför,berber')."
    ),
    location: str = typer.Option(
        ..., "--location", "-l",
        help="Konum (ör. 'Kadıköy, İstanbul')."
    ),
    radius: int = typer.Option(
        10, "--radius", "-r",
        help="Arama yarıçapı (km)."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p",
        help="Veri sağlayıcı (osm | google_places). Varsayılan: .env DISCOVERY_PRIMARY_PROVIDER."
    ),
) -> None:
    """
    Belirli sektör ve konumda işletme keşfi yapar ve veritabanına kaydeder.

    \b
    Modifies: Veritabanına yeni `Lead` satırları ekler.
    Risk: Yok (Mod A — sadece okuma).
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout discover --sector "kuaför" --location "Kadıköy" --radius 5
      aegisScout discover -s "kafe,mimar" -l "Beşiktaş" -r 10 -p google_places
    """
    effective_provider = provider or settings.discovery_primary_provider
    sectors = [s.strip() for s in sector.split(",") if s.strip()]

    total_added = 0
    for s in sectors:
        rprint(
            f"[bold #d4af37]aegisScout[/bold #d4af37] · "
            f"Arama: [green]{s}[/green] @ [green]{location}[/green] "
            f"({radius} km) [{effective_provider}]..."
        )
        res = asyncio.run(
            commands.discover_leads(s, location, radius, effective_provider)
        )
        added = res[0]
        rprint(f"  ↳ [bold green]{added}[/bold green] yeni kayıt eklendi.")
        total_added += added

    if len(sectors) > 1:
        rprint(
            f"[bold green]Toplam:[/bold green] {total_added} yeni işletme veritabanına eklendi."
        )


# ---------------------------------------------------------------------------
# `list` — list leads
# ---------------------------------------------------------------------------
@app.command(name="list")
def list_leads(
    status: Optional[str] = typer.Option(
        None, "--status",
        help="Lead durum filtresi (new, researched, drafted, contacted, replied, vb.)."
    ),
    limit: int = typer.Option(
        20, "--limit", "-n",
        help="Gösterilecek maksimum kayıt sayısı."
    ),
) -> None:
    """
    Potansiyel müşteri adaylarını (lead) listeler.

    \b
    Modifies: Hiçbir şey (salt okunur).
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout list
      aegisScout list --status researched --limit 50
      aegisScout list --status contacted -n 10
    """
    with Session(engine) as session:
        stmt = select(Lead)
        if status:
            stmt = stmt.where(Lead.status == status)
        stmt = stmt.order_by(col(Lead.id).desc()).limit(limit)
        leads = session.exec(stmt).all()

        if not leads:
            rprint("[yellow]Gösterilecek kayıt bulunamadı.[/yellow]")
            return

        table = Table(title="Potansiyel Müşteri Adayları (Leads)")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("İşletme Adı", style="bold white")
        table.add_column("Sektör", style="magenta")
        table.add_column("Konum/Adres", style="dim")
        table.add_column("Telefon", style="green")
        table.add_column("Sosyal Medya", style="blue")
        table.add_column("Web Sitesi", style="yellow")
        table.add_column("Skor", justify="right", style="cyan")
        table.add_column("Durum", style="bold green")

        def _socials_compact(lead) -> str:
            tags = []
            if lead.instagram_handle:
                tags.append(f"IG:@{lead.instagram_handle}")
            if lead.youtube_url:
                tags.append("YT")
            if lead.linkedin_url:
                tags.append("LI")
            if lead.tiktok_url:
                tags.append("TT")
            if lead.facebook_url:
                tags.append("FB")
            if lead.telegram_url:
                tags.append("TG")
            if lead.twitter_url:
                tags.append("X")
            return " | ".join(tags) if tags else "-"

        for lead in leads:
            score = str(lead.website_quality_score) if lead.website_quality_score is not None else "-"
            website = "Evet" if lead.has_website else "Hayır"
            table.add_row(
                str(lead.id),
                lead.business_name,
                lead.sector or "-",
                lead.address or "-",
                lead.phone or "-",
                _socials_compact(lead),
                website,
                score,
                lead.status,
            )

        console.print(table)


# ---------------------------------------------------------------------------
# `research` — research a lead + generate AI draft
# ---------------------------------------------------------------------------
@app.command()
def research(
    lead_id: int = typer.Option(
        ..., "--lead-id", "-id",
        help="Araştırılacak lead'in ID'si."
    ),
    force: bool = typer.Option(
        False, "--force",
        help="Zaten araştırılmış lead'leri yeniden araştır."
    ),
) -> None:
    """
    Belirli bir lead için web scraping, Instagram araştırması ve AI mesaj taslağı oluşturur.

    \b
    Modifies: Lead.status → 'researched', yeni `Message` (draft) ekler, ResearchNote ekler.
    Risk: Düşük (harici HTTP istekleri).
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout research --lead-id 1
      aegisScout research --lead-id 1 --force
    """
    rprint(
        f"[bold #d4af37]aegisScout[/bold #d4af37] · Lead araştırması başlatılıyor (ID: {lead_id})..."
    )
    asyncio.run(commands.research_lead(lead_id, force=force))
    rprint("[bold green]Tamamlandı![/bold green] Araştırma ve taslak oluşturma tamamlandı.")


# ---------------------------------------------------------------------------
# `review` — interactively review leads with researched OR drafted status
# ---------------------------------------------------------------------------
@app.command()
def review() -> None:
    """
    Araştırılmış veya taslaklanmış lead'leri interaktif olarak inceler.

    \b
    Modifies: Lead.status ve Message.status değişebilir (sent / rejected / edited).
    Risk: Mod A (panoya kopyalama, tarayıcı açma) — Mod B (Instagram otomasyonu)
    sadece `automate enable --i-understand-the-risk` ile etkinleştirilmişse kullanılır.
    Requires --i-understand-the-risk: Hayır (Mod B ayrıca onaylanmalıdır).

    \b
    Examples:
      aegisScout review
    """
    with Session(engine) as session:
        stmt = select(Lead).where(col(Lead.status).in_(["researched", "drafted"]))
        leads = session.exec(stmt).all()

        if not leads:
            rprint(
                "[yellow]İncelenecek araştırılmış/taslaklanmış lead bulunamadı. "
                "Önce 'research' komutunu çalıştırın.[/yellow]"
            )
            return

        for lead in leads:
            rprint("\n" + "=" * 50)
            rprint(f"[bold cyan]İşletme Adı:[/bold cyan] {lead.business_name}")
            rprint(f"[bold cyan]Sektör:[/bold cyan] {lead.sector}")
            rprint(f"[bold cyan]Telefon:[/bold cyan] {lead.phone or '-'}")
            rprint(f"[bold cyan]Instagram:[/bold cyan] {lead.instagram_url or '-'}")
            rprint(f"[bold cyan]YouTube:[/bold cyan] {lead.youtube_url or '-'}")
            rprint(f"[bold cyan]LinkedIn:[/bold cyan] {lead.linkedin_url or '-'}")
            rprint(f"[bold cyan]TikTok:[/bold cyan] {lead.tiktok_url or '-'}")
            rprint(f"[bold cyan]Facebook:[/bold cyan] {lead.facebook_url or '-'}")
            rprint(f"[bold cyan]Telegram:[/bold cyan] {lead.telegram_url or '-'}")
            rprint(f"[bold cyan]X/Twitter:[/bold cyan] {lead.twitter_url or '-'}")
            rprint(f"[bold cyan]Web Sitesi:[/bold cyan] {lead.website_url or '-'}")
            rprint(f"[bold cyan]Web Kalite Skoru:[/bold cyan] {lead.website_quality_score or '-'}")
            if lead.instagram_bio:
                rprint(f"[bold cyan]Instagram Bio:[/bold cyan] {lead.instagram_bio[:140]}{'...' if len(lead.instagram_bio) > 140 else ''}")

            # Fetch latest message draft
            msg_stmt = select(Message).where(
                (Message.lead_id == lead.id) & (Message.status == "draft")
            )
            message = session.exec(msg_stmt).first()

            # CRITICAL: never pass None to clipboard / InstagramClient.
            if not message or not message.content or not message.content.strip():
                fallback = _safe_fallback_text(lead.business_name, lead.sector)
                logger.warning(
                    f"Lead {lead.id} ({lead.business_name}): empty/None draft. "
                    f"Using deterministic fallback for review."
                )
                rprint(
                    f"[bold yellow]AI taslağı boş — güvenli fallback kullanılıyor:[/bold yellow]"
                )
                rprint(f"[italic]{fallback}[/italic]")
            else:
                rprint(f"[bold yellow]AI Tarafından Oluşturulan Mesaj:[/bold yellow]")
                rprint(f"[italic]{message.content}[/italic]")
            rprint("=" * 50)

            choice = typer.prompt(
                "Ne yapmak istersiniz?\n"
                "[g] Gönder (Assisted/Auto)\n"
                "[d] Taslağı Düzenle\n"
                "[r] Reddet / Pas geç\n"
                "[s] Sonraki\n"
                "Seçiminiz",
                default="s",
            ).lower().strip()

            if choice == "g":
                # If there was no draft, create one from the safe fallback so the
                # clipboard / Mod B call always has a non-empty payload.
                if not message:
                    message = Message(
                        lead_id=lead.id,
                        direction="outbound",
                        channel="instagram_manual",
                        content=fallback,
                        ai_generated=False,
                        status="draft",
                    )
                    session.add(message)
                    session.commit()
                    session.refresh(message)
                elif not message.content or not message.content.strip():
                    message.content = fallback
                    session.add(message)
                    session.commit()
                    session.refresh(message)

                if settings.outreach_mode == "full_auto":
                    flag_file = Path("data/sessions/automation_authorized.flag")
                    if not flag_file.exists() or not _mod_b_acknowledged():
                        rprint(
                            "[red]Hata: Tam otomasyon modu (Mod B) etkin değil.[/red]"
                        )
                        rprint(
                            "[yellow]Bunu açmak için önce "
                            "`aegisScout automate enable --i-understand-the-risk` "
                            "çalıştırın.[/yellow]"
                        )
                        continue

                    if not lead.instagram_handle:
                        rprint(
                            "[red]Instagram hesabı bulunmadığı için otomatik DM gönderilemedi.[/red]"
                        )
                        continue

                    rprint(
                        f"[bold #d4af37]Instagram DM otomatik olarak gönderiliyor... "
                        f"@{lead.instagram_handle}[/bold #d4af37]"
                    )
                    # Lazy import — only required when Mod B is engaged.
                    from aegisScout.outreach.instagram_client import InstagramClient
                    ig = InstagramClient()
                    success = ig.send_direct_message(lead.instagram_handle, message.content)
                    if success:
                        message.status = "sent"
                        message.channel = "instagram_auto"
                        lead.status = "contacted"
                        session.add(message)
                        session.add(lead)
                        session.commit()
                        rprint(
                            "[green]Başarıyla gönderildi ve durum 'contacted' olarak güncellendi.[/green]"
                        )
                    else:
                        rprint("[red]Gönderim başarısız oldu.[/red]")
                else:
                    # Assisted Mode A (Clipboard + browser)
                    rprint(
                        "[bold #d4af37]Metin panoya kopyalanıyor ve Instagram profil sayfası açılıyor...[/bold #d4af37]"
                    )
                    if send_assisted_message(lead, message.content):
                        message.status = "sent"
                        message.channel = "instagram_manual"
                        lead.status = "contacted"
                        session.add(message)
                        session.add(lead)
                        session.commit()
                        rprint(
                            "[green]Metin panoya kopyalandı! Tarayıcıda mesajı yapıştırıp gönderebilirsiniz.[/green]"
                        )
                    else:
                        rprint("[red]Hata oluştu.[/red]")

            elif choice == "d":
                if not message:
                    rprint("[yellow]Bu lead için taslak yok — önce 'research' çalıştırın.[/yellow]")
                    continue
                new_msg = typer.prompt("Yeni mesaj içeriğini girin")
                message.content = new_msg
                session.add(message)
                session.commit()
                rprint("[green]Taslak güncellendi.[/green]")

            elif choice == "r":
                lead.status = "rejected"
                session.add(lead)
                session.commit()
                rprint("[dim]Lead reddedildi olarak işaretlendi.[/dim]")

            elif choice == "s":
                continue


# ---------------------------------------------------------------------------
# `send` — send the AI draft for a specific lead (Mod A by default)
# ---------------------------------------------------------------------------
@app.command()
def send(
    lead_id: int = typer.Option(
        ..., "--lead-id", "-id",
        help="Gönderilecek lead ID'si."
    ),
) -> None:
    """
    Mod A: Belirli bir lead için taslak mesajı panoya kopyalar ve Instagram DM sayfasını tarayıcıda açar.

    Taslak AI tarafından üretilmediyse (boş/None) deterministik bir fallback kullanılır
    ve bir uyarı loglanır — asla None panoya gönderilmez.

    \b
    Modifies: Message.status → 'sent', Lead.status → 'contacted'.
    Risk: Mod A (güvenli). Mod B outreach_mode=full_auto ise Instagram API
    üzerinden otomatik gönderim yapar — sadece `automate enable --i-understand-the-risk` ile.
    Requires --i-understand-the-risk: Hayır (Mod A). Mod B ayrıca onay gerektirir.

    \b
    Examples:
      aegisScout send --lead-id 1
    """
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            rprint(f"[red]Lead ID {lead_id} bulunamadı.[/red]")
            raise typer.Exit(code=1)

        msg_stmt = select(Message).where(
            (Message.lead_id == lead.id) & (Message.status == "draft")
        )
        message = session.exec(msg_stmt).first()

        if not message or not message.content or not message.content.strip():
            fallback = _safe_fallback_text(lead.business_name, lead.sector)
            logger.warning(
                f"Lead {lead_id}: send called with empty/None draft. Using fallback."
            )
            rprint(
                "[yellow]Taslak mesaj boş — güvenli fallback kullanılıyor.[/yellow]"
            )
            content_to_send = fallback
            if not message:
                message = Message(
                    lead_id=lead.id,
                    direction="outbound",
                    channel="instagram_manual",
                    content=fallback,
                    ai_generated=False,
                    status="draft",
                )
                session.add(message)
        else:
            content_to_send = message.content

        rprint(
            "[bold #d4af37]Metin panoya kopyalanıyor ve Instagram DM açılıyor...[/bold #d4af37]"
        )
        if send_assisted_message(lead, content_to_send):
            message.status = "sent"
            message.channel = "instagram_manual"
            lead.status = "contacted"
            session.add(message)
            session.add(lead)
            session.commit()
            rprint(
                "[green]Başarılı! Mesaj gönderildikten sonra durum otomatik güncellendi.[/green]"
            )
        else:
            rprint("[red]Hata oluştu.[/red]")


# ---------------------------------------------------------------------------
# `watch` — start the reply watcher daemon
# ---------------------------------------------------------------------------
@app.command()
def watch(
    interval: int = typer.Option(
        300, "--interval", "-i",
        help="Polleme aralığı (saniye)."
    ),
) -> None:
    """
    Yanıt izleme daemon'ını (Watcher Modülü) başlatır.

    \b
    Modifies: Inbox polling, ActivityLog kayıtları, bildirim tetikler.
    Risk: Instagram API çağrıları (Mod B yüklüyse).
    Requires --i-understand-the-risk: Hayır (sadece okur), Mod B aktifse önerilir.

    \b
    Examples:
      aegisScout watch
      aegisScout watch --interval 120
    """
    rprint(
        "[bold #d4af37]aegisScout[/bold #d4af37] Reply Watcher Daemon başlatılıyor..."
    )
    rprint(f"Polleme aralığı: {interval} saniye.")
    # Lazy import: ReplyWatcher pulls instagrapi if Mod B is installed.
    from aegisScout.monitoring.reply_watcher import ReplyWatcher
    watcher = ReplyWatcher()
    asyncio.run(watcher.watch_loop(interval))


# ---------------------------------------------------------------------------
# `export` — CSV export
# ---------------------------------------------------------------------------
@app.command()
def export(
    output_path: str = typer.Option(
        "data/exports/leads.csv", "--output", "-o",
        help="Dışa aktarma dosya yolu."
    ),
    format: str = typer.Option(
        "csv", "--format", "-f",
        help="Dosya formatı (csv)."
    ),
    status: Optional[str] = typer.Option(
        None, "--status",
        help="Sadece bu durumda olan lead'leri aktar (ör. contacted, replied)."
    ),
    sector: Optional[str] = typer.Option(
        None, "--sector",
        help="Sadece bu sektörü aktar."
    ),
    campaign_id: Optional[int] = typer.Option(
        None, "--campaign-id", "-c",
        help="Sadece bu kampanyaya atanan lead'leri aktar."
    ),
) -> None:
    """
    Veritabanındaki lead kayıtlarını CSV formatında dışa aktarır.

    \b
    Modifies: Belirtilen `output_path`'e dosya yazar.
    Risk: Yok (salt okunur, sadece dosya yazımı).
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout export --output data/exports/leads.csv
      aegisScout export --status contacted -o data/exports/contacted.csv
      aegisScout export --campaign-id 1 -o data/exports/campaign_1.csv
    """
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with Session(engine) as session:
        stmt = select(Lead)
        if status:
            stmt = stmt.where(Lead.status == status)
        if sector:
            stmt = stmt.where(Lead.sector == sector)
        if campaign_id:
            stmt = stmt.where(Lead.campaign_id == campaign_id)
        leads = session.exec(stmt).all()

        if not leads:
            rprint("[yellow]Dışa aktarılacak lead bulunamadı.[/yellow]")
            return

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "İşletme Adı", "Sektör", "Telefon", "Adres", "Web Sitesi",
                "Instagram", "YouTube", "LinkedIn", "TikTok", "Facebook",
                "Telegram", "X/Twitter", "Değerlendirme Puanı", "Yorum Sayısı",
                "Web Kalite Skoru", "Durum", "Keşif Tarihi", "Kampanya ID",
            ])
            for lead in leads:
                writer.writerow([
                    lead.id,
                    lead.business_name,
                    lead.sector or "",
                    lead.phone or "",
                    lead.address or "",
                    lead.website_url or "",
                    lead.instagram_handle or "",
                    lead.youtube_url or "",
                    lead.linkedin_url or "",
                    lead.tiktok_url or "",
                    lead.facebook_url or "",
                    lead.telegram_url or "",
                    lead.twitter_url or "",
                    lead.rating or "",
                    lead.review_count or "",
                    lead.website_quality_score or "",
                    lead.status,
                    lead.discovered_at,
                    lead.campaign_id or "",
                ])

        filter_info = ""
        if status:
            filter_info += f" (durum: {status})"
        if sector:
            filter_info += f" (sektör: {sector})"
        if campaign_id:
            filter_info += f" (kampanya ID: {campaign_id})"
        rprint(
            f"[bold green]Başarılı![/bold green] {len(leads)} kayıt "
            f"'{output_path}' konumuna aktarıldı{filter_info}."
        )


# ---------------------------------------------------------------------------
# `mark-replied` — manual reply marker
# ---------------------------------------------------------------------------
@app.command(name="mark-replied")
def mark_replied(
    lead_id: int = typer.Option(
        ..., "--lead-id", "-id",
        help="Yanıt işaretlenecek lead ID'si."
    ),
    note: Optional[str] = typer.Option(
        None, "--note", "-n",
        help="Opsiyonel not (yanıt içeriği vb.)."
    ),
) -> None:
    """
    Mod A: Belirli bir lead için manuel olarak 'yanıt geldi' işareti koyar.

    \b
    Modifies: Lead.status → 'replied', inbound Message ekler, ActivityLog ekler.
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout mark-replied --lead-id 1
      aegisScout mark-replied --lead-id 1 --note "Pazartesi görüşme talep etti"
    """
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            rprint(f"[red]Lead ID {lead_id} bulunamadı.[/red]")
            raise typer.Exit(code=1)

        old_status = lead.status
        lead.status = "replied"
        from datetime import datetime, timezone
        lead.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        inbound_content = note or "(Yanıt manuel işaretlendi — içerik kullanıcı tarafından girilmedi)"
        inbound_msg = Message(
            lead_id=lead.id,
            direction="inbound",
            channel="instagram_manual",
            content=inbound_content,
            status="sent",
        )
        session.add(inbound_msg)

        log = ActivityLog(
            action="reply_received",
            details=f"Lead {lead.business_name} (ID:{lead_id}) yanıtı manuel işaretlendi. Önceki durum: {old_status}",
        )
        session.add(log)

        session.add(lead)
        session.commit()

        rprint(
            f"[bold green]✓[/bold green] Lead [cyan]{lead.business_name}[/cyan] durumu "
            f"[yellow]{old_status}[/yellow] → [green]replied[/green] olarak güncellendi."
        )
        if note:
            rprint(f"[dim]Not: {note}[/dim]")


# ---------------------------------------------------------------------------
# Mod B acknowledgement helper
# ---------------------------------------------------------------------------
def _mod_b_acknowledged() -> bool:
    """Return True if the user has acknowledged Mod B risk in config.toml."""
    try:
        return bool(config_data.get("outreach", {}).get("mod_b_acknowledged", False))
    except Exception:
        return False


def _persist_mod_b_acknowledged() -> None:
    """Persist mod_b_acknowledged = True in config/config.toml (best-effort)."""
    cfg_path = Path("config") / "config.toml"
    if not cfg_path.exists():
        # Fall back to writing into the example path so the value lives somewhere
        # — most production installs copy the example first.
        return
    try:
        from aegisScout.core.toml_config import load_toml_config, dump_toml
        existing = load_toml_config(cfg_path) if cfg_path.exists() else {}
        if "outreach" not in existing:
            existing["outreach"] = {}
        existing["outreach"]["mod_b_acknowledged"] = True
        dump_toml(existing, cfg_path)
        # Mutate in-memory cache so subsequent reads see the new value
        try:
            config_data.setdefault("outreach", {})["mod_b_acknowledged"] = True
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Could not persist mod_b_acknowledged to {cfg_path}: {e}")


# ---------------------------------------------------------------------------
# `automate` — enable/disable Mod B (full Instagram automation)
# ---------------------------------------------------------------------------
@app.command()
def automate(
    action: str = typer.Argument(
        ..., help="Yapılacak işlem: 'enable' veya 'disable'."
    ),
    i_understand_the_risk: bool = typer.Option(
        False,
        "--i-understand-the-risk",
        help=(
            "Onay bayrağı. 'enable' için ZORUNLUDUR. Onaylamadan çalıştırırsanız komut "
            "exit 1 ile sonlanır. Meta/Instagram ToS soğuk DM'leri yasaklar; otomasyon hesap "
            "kısıtlamasına yol açabilir. Detaylar: `aegisScout docs mod-b`."
        ),
    ),
) -> None:
    """
    Mod B (Tam Instagram Otomasyonu) durumunu yönetir.

    \b
    Modifies: config.toml (mod_b_acknowledged), data/sessions/automation_authorized.flag.
    Risk: YÜKSEK. Mod B Instagram ToS'u ihlal eder. Sadece yedek/ikincil hesaplarla ve günlük
    limitleri (maks 15-20 DM/gün) aşmadan kullanın. Tam sorumluluk reddi için
    `aegisScout docs mod-b` çalıştırın.
    Requires --i-understand-the-risk: Evet, `enable` için zorunlu.

    \b
    Examples:
      aegisScout automate enable --i-understand-the-risk
      aegisScout automate disable
    """
    flag_dir = Path("data/sessions")
    flag_dir.mkdir(parents=True, exist_ok=True)
    flag_file = flag_dir / "automation_authorized.flag"

    if action == "enable":
        if not i_understand_the_risk:
            err_console.print(
                "[bold red]ERROR:[/bold red] Mod B (automated Instagram DMs) is not enabled. "
                "To enable, pass --i-understand-the-risk. Be aware Meta ToS prohibits "
                "cold DMs. See `aegisScout docs mod-b` for full disclaimer."
            )
            raise typer.Exit(code=1)

        # Persist acknowledgement in toml config
        _persist_mod_b_acknowledged()
        # Also keep the flag file used by runtime + GUI as a fast path
        with open(flag_file, "w") as f:
            f.write("authorized")
        rprint(
            "[bold green]Mod B (Tam Otomasyon) ETKİNLEŞTİRİLDİ.[/bold green]"
        )
        rprint(
            "[yellow]UYARI: Instagram ToS kuralları gereği bu kullanım hesabınızın "
            "kısıtlanmasına yol açabilir.[/yellow]"
        )

    elif action == "disable":
        if flag_file.exists():
            flag_file.unlink()
        # Best-effort: also clear the toml acknowledgement
        try:
            from aegisScout.core.toml_config import load_toml_config, dump_toml
            cfg_path = Path("config") / "config.toml"
            if cfg_path.exists():
                data = load_toml_config(cfg_path)
                if "outreach" in data:
                    data["outreach"]["mod_b_acknowledged"] = False
                    dump_toml(data, cfg_path)
                    config_data.get("outreach", {})["mod_b_acknowledged"] = False
        except Exception:
            pass
        rprint(
            "[bold green]Mod B (Tam Otomasyon) devre dışı bırakıldı. "
            "Assisted Mod A kullanılacak.[/bold green]"
        )
    else:
        rprint(
            f"[red]Bilinmeyen aksiyon: {action}. Sadece 'enable' veya 'disable' geçerlidir.[/red]"
        )
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# `gui` — explicit GUI launcher
# ---------------------------------------------------------------------------
@app.command()
def gui() -> None:
    """
    aegisScout Grafik Arayüzünü (GUI) başlatır.

    \b
    Modifies: Hiçbir şey.
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout gui
      # Not: Hiçbir argüman olmadan `aegisScout` da GUI'yi otomatik başlatır.
    """
    rprint("[bold #d4af37]aegisScout[/bold #d4af37] Grafik Arayüzü başlatılıyor...")
    from aegisScout.gui import start_gui
    start_gui()


# ---------------------------------------------------------------------------
# `docs` sub-Typer — discoverable help commands
# ---------------------------------------------------------------------------
docs_app = typer.Typer(
    name="docs",
    help="Yerleşik belgeler ve sorumluluk reddi komutları.",
    add_completion=False,
    no_args_is_help=True,
)
app.add_typer(docs_app, name="docs")


@docs_app.command("mod-b")
def docs_mod_b() -> None:
    """
    Mod B (Tam Instagram Otomasyonu) için TAM sorumluluk reddi.

    \b
    Examples:
      aegisScout docs mod-b
    """
    text = (
        "[bold red]Mod B — Tam Otomasyon (Instagram API) Sorumluluk Reddi[/bold red]\n\n"
        "Mod B, aegisScout'un Instagram'a `instagrapi` üzerinden doğrudan oturum açıp\n"
        "soğuk DM gönderdiği deneysel moddur. KULLANIMI AŞAĞIDAKİ RİSKLERİ TAŞIR:\n\n"
        "  1. [bold]Meta/Instagram Kullanım Koşulları İhlali[/bold]: Instagram, otomatik\n"
        "     mesajlaşma araçlarını yasaklar. Tespit edilmesi durumunda hesabınız\n"
        "     geçici olarak kısıtlanabilir (action block / shadow ban) veya kalıcı\n"
        "     olarak kapatılabilir.\n\n"
        "  2. [bold]Hesap Kaybı Riski[/bold]: Instagram bot algılama sistemi hassastır.\n"
        "     Yeni açılmış, doğrulanmamış veya düşük etkileşimli hesaplar ilk\n"
        "     otomasyon denemesinde engellenebilir.\n\n"
        "  3. [bold]Veri Kaybı[/bold]: Oturum verileri veritabanında şifreli\n"
        "     (Fernet/AES-256) saklansa da, başarısız gönderimlerde rate limit ve\n"
        "     hesap sağlığı geri dönülemez şekilde bozulabilir.\n\n"
        "  4. [bold]Yasal Sorumluluk[/bold]: KVKK, GDPR ve yerel doğrudan pazarlama\n"
        "     mevzuatı (ör. İYS) ticari elektronik ileti gönderimini düzenler. Bir\n"
        "     hukuk danışmanına danışmadan Mod B ile toplu gönderim YAPMAYIN.\n\n"
        "[bold]Öneriler[/bold]:\n"
        "  • Yalnızca yedek/ikincil hesaplar kullanın.\n"
        "  • Günlük 15-20 DM sınırını aşmayın (PRD §3.3).\n"
        "  • Göndereceğiniz DM'leri manuel incelemeden asla otomatikleştirmeyin.\n\n"
        "[dim]Detaylar için `aegisScout docs tos` ve `aegisScout docs security`.[/dim]"
    )
    err_console.print(Panel(text, border_style="red", padding=(1, 2)))


@docs_app.command("tos")
def docs_tos() -> None:
    """
    Meta/Instagram ve diğer sağlayıcıların Kullanım Koşulları özeti.

    \b
    Examples:
      aegisScout docs tos
    """
    text = (
        "[bold]Üçüncü Parti Sağlayıcı Kullanım Koşulları Özeti[/bold]\n\n"
        "[bold]Instagram (Meta Platforms)[/bold]\n"
        "  • https://help.instagram.com/help/contact/552695695608935 — otomasyon yasağı.\n"
        "  • Soğuk DM gönderimi 'spam' kapsamına girer.\n"
        "  • API olmadan scraping yapmak da ToS ihlalidir.\n\n"
        "[bold]Google Places / Custom Search[/bold]\n"
        "  • Google Cloud Terms of Service: https://cloud.google.com/terms\n"
        "  • Kota aşımı ücretlendirilir; field mask kullanın.\n\n"
        "[bold]OpenAI / Anthropic / OpenRouter / Groq / Mistral / DeepSeek / Gemini[/bold]\n"
        "  • Her sağlayıcının kendi kullanım politikası geçerlidir.\n"
        "  • Üretilen içerikten kullanıcı sorumludur — yanıltıcı veya spam içerik\n"
        "    üretmeyin.\n\n"
        "[bold]OpenStreetMap (Overpass API)[/bold]\n"
        "  • https://operations.osmfoundation.org/policies/api/ — rate limit\n"
        "    (max 2 paralel istek) ve kaynak atfetme zorunludur.\n\n"
        "[bold yellow]aegisScout, hiçbir sağlayıcının ürünü değildir. Bu araç yalnızca\n"
        "API'leri sizin adınıza kullandırır; sağlayıcılar hizmeti istedikleri zaman\n"
        "değiştirebilir veya kısıtlayabilir.[/bold yellow]"
    )
    err_console.print(Panel(text, border_style="yellow", padding=(1, 2)))


@docs_app.command("security")
def docs_security() -> None:
    """
    .env / secret hygiene en iyi pratikleri.

    \b
    Examples:
      aegisScout docs security
    """
    text = (
        "[bold]Güvenlik — Çevresel Değişken ve Gizli Anahtar Hijyeni[/bold]\n\n"
        "[bold red]ASLA[/bold red] aşağıdakileri repoya commit etmeyin:\n"
        "  • .env dosyanız\n"
        "  • data/sessions/automation_authorized.flag\n"
        "  • data/aegisScout.db (şifrelenmiş olsa da)\n"
        "  • API anahtarları içeren log çıktıları\n\n"
        ".gitignore dosyası zaten .env, data/, logs/ dizinlerini yoksayır.\n\n"
        "[bold]Fernet şifreleme anahtarı[/bold]\n"
        "  • Yeni anahtar üretmek için:\n"
        "    [dim]python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"[/dim]\n"
        "  • INSTAGRAM_SESSION_ENCRYPTION_KEY env değişkenine yazın.\n"
        "  • Anahtarı KAYBEDERSENİZ veritabanındaki Instagram oturumu\n"
        "    çözülemez — yeni oturum açmanız gerekir.\n\n"
        "[bold]Mod B (Instagram otomasyonu) hesapları için[/bold]\n"
        "  • Asıl iş hesabınızı DEĞİL, yedek hesap kullanın.\n"
        "  • 2FA açıksa Mod B giriş yapamaz; 'app-specific password' gerekir.\n"
        "  • instagrapi sürümü Instagram sürümüne bağlıdır; API değişikliklerinde\n"
        "    bozulabilir.\n\n"
        "[bold]Bildirim kanalları[/bold]\n"
        "  • SMTP için uygulama-özgü parola (Gmail) veya App Password (Outlook) kullanın.\n"
        "  • Telegram bot token'ınızı bir @BotFather'dan alın ve chat_id'nizi\n"
        "    /getUpdates ile doğrulayın."
    )
    err_console.print(Panel(text, border_style="cyan", padding=(1, 2)))


@docs_app.command("architecture")
def docs_architecture() -> None:
    """
    aegisScout bileşen mimarisinin ASCII diyagramı.

    \b
    Examples:
      aegisScout docs architecture
    """
    text = (
        "[bold]aegisScout — Bileşen Mimarisi[/bold]\n\n"
        "                       ┌───────────────────────────┐\n"
        "                       │   Kullanıcı (Siz)         │\n"
        "                       └────────────┬──────────────┘\n"
        "                                    │\n"
        "                  ┌─────────────────┴──────────────────┐\n"
        "                  │                                    │\n"
        "           ┌──────▼──────┐                      ┌───────▼───────┐\n"
        "           │  CLI (Typer)│                      │ GUI (PyWebView)│\n"
        "           │  main.py    │                      │   gui.py      │\n"
        "           └──────┬──────┘                      └───────┬───────┘\n"
        "                  │                                    │\n"
        "                  └─────────────┬──────────────────────┘\n"
        "                                │\n"
        "                  ┌─────────────▼──────────────┐\n"
        "                  │  Core (Settings, Config,   │\n"
        "                  │   Database SQLModel/SQLite) │\n"
        "                  └─────────────┬──────────────┘\n"
        "                                │\n"
        "        ┌───────────┬───────────┼───────────┬────────────┐\n"
        "        │           │           │           │            │\n"
        "  ┌─────▼─────┐ ┌───▼────┐ ┌────▼────┐ ┌─────▼────┐ ┌─────▼─────┐\n"
        "  │Discovery │ │ AI /   │ │Outreach │ │Monitoring│ │ Encryption│\n"
        "  │ OSM / GP  │ │ LLM   │ │ Mod A/B │ │  Watcher  │ │  Fernet   │\n"
        "  └───────────┘ └────────┘ └─────────┘ └──────────┘ └───────────┘\n\n"
        "  • [dim]Discovery[/dim]: Veri sağlayıcılarından lead toplar.\n"
        "  • [dim]AI/LLM[/dim]: Çoklu sağlayıcı router'ı (fallback destekli).\n"
        "  • [dim]Outreach[/dim]: Mod A (panoya kopyalama) + Mod B (Instagram API).\n"
        "  • [dim]Monitoring[/dim]: Inbox polling, Telegram/SMTP bildirim.\n"
        "  • [dim]Encryption[/dim]: Fernet (AES-128-CBC + HMAC-SHA256)."
    )
    err_console.print(Panel(text, border_style="green", padding=(1, 2)))


# ---------------------------------------------------------------------------
# Campaign sub-Typer
# ---------------------------------------------------------------------------
campaign_app = typer.Typer(
    name="campaign",
    help="Kampanya Yönetimi ve Raporlama.",
    add_completion=False,
    no_args_is_help=True,
)


@campaign_app.command("create")
def campaign_create(
    name: str = typer.Option(..., "--name", "-n", help="Kampanya adı."),
    sector: Optional[str] = typer.Option(
        None, "--sector", "-s", help="Filtre sektörü."
    ),
    location: Optional[str] = typer.Option(
        None, "--location", "-l", help="Filtre konumu."
    ),
) -> None:
    """
    Yeni bir kampanya oluşturur.

    \b
    Modifies: Veritabanına Campaign ekler.
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout campaign create --name "Kadıköy Kuaförler" --sector "kuaför" --location "Kadıköy"
    """
    with Session(engine) as session:
        exists = session.exec(select(Campaign).where(Campaign.name == name)).first()
        if exists:
            rprint(f"[red]Hata: '{name}' adında bir kampanya zaten mevcut.[/red]")
            raise typer.Exit(code=1)

        campaign = Campaign(name=name, sector_filter=sector, location_filter=location)
        session.add(campaign)

        log = ActivityLog(action="campaign_create", details=f"Kampanya oluşturuldu: {name}")
        session.add(log)

        session.commit()
        rprint(
            f"[bold green]✓[/bold green] Kampanya [cyan]'{name}'[/cyan] "
            f"başarıyla oluşturuldu (ID: {campaign.id})."
        )


@campaign_app.command("list")
def campaign_list() -> None:
    """
    Mevcut kampanyaları ve istatistiklerini listeler.

    \b
    Modifies: Hiçbir şey.
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout campaign list
    """
    with Session(engine) as session:
        campaigns = session.exec(select(Campaign).order_by(col(Campaign.id).desc())).all()
        if not campaigns:
            rprint("[yellow]Henüz kampanya tanımlanmamış.[/yellow]")
            return

        table = Table(title="Kampanyalar")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Kampanya Adı", style="bold white")
        table.add_column("Sektör Filtresi", style="magenta")
        table.add_column("Konum Filtresi", style="dim")
        table.add_column("Toplam Lead", justify="right", style="green")
        table.add_column("Yanıt Oranı", justify="right", style="yellow")
        table.add_column("Oluşturulma Tarihi", style="blue")

        for c in campaigns:
            leads_stmt = select(Lead).where(Lead.campaign_id == c.id)
            leads = session.exec(leads_stmt).all()
            total_leads = len(leads)

            replied_count = sum(1 for l in leads if l.status == "replied")
            contacted_count = sum(1 for l in leads if l.status in ("contacted", "replied"))

            ratio_str = "-"
            if contacted_count > 0:
                ratio_str = f"%{replied_count / contacted_count * 100:.1f} ({replied_count}/{contacted_count})"
            elif total_leads > 0:
                ratio_str = f"%0 (0/{total_leads} contacted)"

            table.add_row(
                str(c.id),
                c.name,
                c.sector_filter or "-",
                c.location_filter or "-",
                str(total_leads),
                ratio_str,
                c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
        console.print(table)


@campaign_app.command("assign")
def campaign_assign(
    campaign_id: int = typer.Option(..., "--campaign-id", "-c", help="Kampanya ID'si."),
    lead_id: Optional[int] = typer.Option(
        None, "--lead-id", "-l", help="Tekil lead ID'si (opsiyonel)."
    ),
    auto_filter: bool = typer.Option(
        False, "--auto-filter", "-a",
        help="Kampanyanın filtrelerine uyan adayları otomatik ata."
    ),
) -> None:
    """
    Müşteri adaylarını (leads) bir kampanyaya atar.

    \b
    Modifies: Lead.campaign_id.
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout campaign assign --campaign-id 1 --lead-id 5
      aegisScout campaign assign --campaign-id 1 --auto-filter
    """
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            rprint(f"[red]Hata: Kampanya ID {campaign_id} bulunamadı.[/red]")
            raise typer.Exit(code=1)

        if not lead_id and not auto_filter:
            rprint(
                "[red]Hata: --lead-id veya --auto-filter seçeneğinden en az biri belirtilmelidir.[/red]"
            )
            raise typer.Exit(code=1)

        assigned_count = 0
        if lead_id:
            lead = session.get(Lead, lead_id)
            if not lead:
                rprint(f"[red]Hata: Lead ID {lead_id} bulunamadı.[/red]")
                raise typer.Exit(code=1)
            lead.campaign_id = campaign.id
            session.add(lead)
            assigned_count = 1

        if auto_filter:
            stmt = select(Lead).where(col(Lead.campaign_id).is_(None))
            if campaign.sector_filter:
                stmt = stmt.where(Lead.sector == campaign.sector_filter)
            if campaign.location_filter:
                stmt = stmt.where(col(Lead.address).like(f"%{campaign.location_filter}%"))

            leads_to_assign = session.exec(stmt).all()
            for lead in leads_to_assign:
                lead.campaign_id = campaign.id
                session.add(lead)
                assigned_count += 1

        if assigned_count > 0:
            log = ActivityLog(
                action="campaign_assign",
                details=f"{assigned_count} adet lead Kampanya '{campaign.name}' (ID: {campaign.id}) atandı.",
            )
            session.add(log)
            session.commit()
            rprint(
                f"[bold green]✓[/bold green] {assigned_count} adet lead başarıyla "
                f"[cyan]'{campaign.name}'[/cyan] kampanyasına atandı."
            )
        else:
            rprint("[yellow]Kampanyaya atanacak yeni lead bulunamadı.[/yellow]")


@campaign_app.command("show")
def campaign_show(
    campaign_id: int = typer.Argument(..., help="Detayları gösterilecek kampanya ID'si."),
) -> None:
    """
    Bir kampanyanın detaylarını ve içindeki leads listesini gösterir.

    \b
    Modifies: Hiçbir şey.
    Risk: Yok.
    Requires --i-understand-the-risk: Hayır.

    \b
    Examples:
      aegisScout campaign show 1
    """
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            rprint(f"[red]Hata: Kampanya ID {campaign_id} bulunamadı.[/red]")
            raise typer.Exit(code=1)

        rprint(f"[bold cyan]Kampanya Adı:[/bold cyan] {campaign.name}")
        rprint(f"[bold cyan]Sektör Filtresi:[/bold cyan] {campaign.sector_filter or '-'}")
        rprint(f"[bold cyan]Konum Filtresi:[/bold cyan] {campaign.location_filter or '-'}")
        rprint(f"[bold cyan]Oluşturulma:[/bold cyan] {campaign.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        rprint("-" * 50)

        leads = session.exec(select(Lead).where(Lead.campaign_id == campaign.id)).all()
        if not leads:
            rprint("[yellow]Bu kampanyada kayıtlı lead bulunmuyor.[/yellow]")
            return

        table = Table(title=f"'{campaign.name}' Kampanyasındaki İşletmeler")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("İşletme Adı", style="bold white")
        table.add_column("Sektör", style="magenta")
        table.add_column("Instagram", style="blue")
        table.add_column("Durum", style="bold green")

        for lead in leads:
            table.add_row(
                str(lead.id),
                lead.business_name,
                lead.sector or "-",
                f"@{lead.instagram_handle}" if lead.instagram_handle else "-",
                lead.status,
            )
        console.print(table)


# Register campaign sub-Typer
app.add_typer(campaign_app, name="campaign")


# ---------------------------------------------------------------------------
# `waterfall` — Run waterfall enrichment cascade for a lead
# ---------------------------------------------------------------------------
@app.command()
def waterfall(
    lead_id: int = typer.Option(
        ..., "--lead-id", "-id",
        help="Zenginleştirilecek lead ID'si."
    ),
) -> None:
    """
    Waterfall enrichment cascade: website scrape → search query → Instagram bio → email verify.
    Finds and verifies email addresses for a lead through sequential steps.
    """
    rprint(f"[bold #d4af37]aegisScout[/bold #d4af37] · Waterfall enrichment başlatılıyor (ID: {lead_id})...")
    try:
        res = asyncio.run(run_waterfall_enrichment(lead_id))
        if res.get("success"):
            rprint(f"[bold green]✓[/bold green] Waterfall tamamlandı.")
            if res.get("email"):
                rprint(f"  E-posta: [cyan]{res['email']}[/cyan]")
            if res.get("verification_status"):
                rprint(f"  Doğrulama: [cyan]{res['verification_status']}[/cyan]")
            rprint(f"  Adımlar: [cyan]{', '.join(res.get('steps_executed', []))}[/cyan]")
        else:
            rprint(f"[red]Hata: {res.get('error', 'Bilinmeyen hata')}[/red]")
    except Exception as e:
        rprint(f"[red]Waterfall hatası: {e}[/red]")


# ---------------------------------------------------------------------------
# `audit` — Run multimodal screen audit for a lead
# ---------------------------------------------------------------------------
@app.command()
def audit(
    lead_id: int = typer.Option(
        ..., "--lead-id", "-id",
        help="Denetlenecek lead ID'si."
    ),
) -> None:
    """
    Screen audit: captures website screenshot and analyzes design flaws using AI vision.
    Generates personalized outreach hooks based on visual issues found.
    """
    rprint(f"[bold #d4af37]aegisScout[/bold #d4af37] · Screen audit başlatılıyor (ID: {lead_id})...")
    try:
        res = asyncio.run(run_website_screen_audit(lead_id))
        if res.get("success"):
            rprint(f"[bold green]✓[/bold green] Screen audit tamamlandı.")
            rprint(f"  Kalite Skoru: [cyan]{res.get('quality_score')}/100[/cyan]")
            if res.get("hook"):
                rprint(f"  Outreach Hook: [italic]{res['hook'][:120]}...[/italic]")
            if res.get("screenshot_path"):
                rprint(f"  Ekran Görüntüsü: [dim]{res['screenshot_path']}[/dim]")
        else:
            rprint(f"[yellow]Uyarı: {res.get('error', 'Bilinmeyen')}[/yellow]")
    except Exception as e:
        rprint(f"[red]Screen audit hatası: {e}[/red]")


# ---------------------------------------------------------------------------
# `warmup` — Run P2P email warmup cycle
# ---------------------------------------------------------------------------
@app.command()
def warmup() -> None:
    """
    Run a single P2P email warmup cycle between configured SMTP accounts.
    Requires at least 2 active SMTP accounts with IMAP enabled.
    """
    rprint("[bold #d4af37]aegisScout[/bold #d4af37] · P2P Email Warmup döngüsü başlatılıyor...")
    try:
        res = asyncio.run(run_p2p_warmup_cycle())
        if res.get("success"):
            rprint(f"[bold green]✓[/bold green] Warmup döngüsü tamamlandı.")
            if res.get("details"):
                rprint(f"  {res['details']}")
            if res.get("stats"):
                stats = res["stats"]
                rprint(f"  İstatistikler: [cyan]{stats.get('sent', 0)} gönderildi, "
                       f"{stats.get('replied', 0)} yanıtlandı, "
                       f"{stats.get('spam_rescued', 0)} spam'dan kurtarıldı[/cyan]")
        else:
            rprint(f"[yellow]Uyarı: {res.get('error', 'Bilinmeyen')}[/yellow]")
    except Exception as e:
        rprint(f"[red]Warmup hatası: {e}[/red]")


# ---------------------------------------------------------------------------
# `verify` — Local email verification
# ---------------------------------------------------------------------------
@app.command()
def verify(
    email_address: str = typer.Argument(
        ..., help="Doğrulanacak e-posta adresi."
    ),
) -> None:
    """
    Verify an email address locally: format check, disposable domain, DNS MX, SMTP handshake.
    No external API calls — 100% free and private.
    """
    rprint(f"[bold #d4af37]aegisScout[/bold #d4af37] · E-posta doğrulanıyor: [cyan]{email_address}[/cyan]")
    try:
        res = verify_email(email_address)
        if res.get("success"):
            status = res.get("status", "unknown")
            if status == "valid":
                rprint(f"[bold green]✓ GEÇERLİ[/bold green] — {res.get('details', '')}")
            elif status == "mx_only":
                rprint(f"[bold yellow]⚠ MX MEVCUT (SMTP engellenmiş olabilir)[/bold yellow] — {res.get('details', '')}")
            else:
                rprint(f"[bold cyan]? {status.upper()}[/bold cyan] — {res.get('details', '')}")
        else:
            rprint(f"[bold red]✗ GEÇERSİZ[/bold red] — {res.get('details', '')}")
    except Exception as e:
        rprint(f"[red]Doğrulama hatası: {e}[/red]")


# ---------------------------------------------------------------------------
# `tasks` — Manage background tasks
# ---------------------------------------------------------------------------
tasks_app = typer.Typer(
    name="tasks",
    help="Arka plan görevlerini yönetme (Task Queue).",
    add_completion=False,
    no_args_is_help=True,
)


@tasks_app.command("list")
def tasks_list() -> None:
    """List all background tasks and their status."""
    try:
        from aegisScout.core.task_queue import TaskQueueManager
        tqm = TaskQueueManager.get_instance()
        all_tasks = tqm.get_all_statuses()
        if not all_tasks:
            rprint("[yellow]Aktif arka plan görevi bulunamadı.[/yellow]")
            return
        table = Table(title="Arka Plan Görevleri")
        table.add_column("ID", style="cyan")
        table.add_column("İsim", style="bold white")
        table.add_column("Durum", style="green")
        table.add_column("İlerleme", justify="right", style="yellow")
        table.add_column("Hata", style="red")
        for t in all_tasks:
            table.add_row(
                t["id"],
                t["name"],
                t["status"],
                f"{t['progress']:.0f}%",
                t.get("error") or "-",
            )
        console.print(table)
    except Exception as e:
        rprint(f"[red]Görev listesi hatası: {e}[/red]")


@tasks_app.command("cancel")
def tasks_cancel(
    task_id: str = typer.Argument(..., help="İptal edilecek görev ID'si."),
) -> None:
    """Cancel a running or pending background task."""
    try:
        from aegisScout.core.task_queue import TaskQueueManager
        tqm = TaskQueueManager.get_instance()
        if tqm.cancel_task(task_id):
            rprint(f"[bold green]✓[/bold green] Görev [cyan]{task_id}[/cyan] iptal edildi.")
        else:
            rprint(f"[yellow]Görev [cyan]{task_id}[/cyan] bulunamadı veya iptal edilemez durumda.[/yellow]")
    except Exception as e:
        rprint(f"[red]Görev iptal hatası: {e}[/red]")


app.add_typer(tasks_app, name="tasks")


# ---------------------------------------------------------------------------
# Module-level entry point
# ---------------------------------------------------------------------------
# NOTE on the entry-point structure:
#   - pyproject.toml declares the console script: aegisScout = "aegisScout.main:app"
#   - pip-generated launcher does: `from aegisScout.main import app; app()`
#   - `python -m aegisScout.main` should also work (covered by the guard below).
# We deliberately do NOT call `app()` unconditionally at module bottom: the
# top-level `@app.callback()` already handles the no-subcommand case (launches
# GUI), so the import-as-object path (used by tests, packaging) is safe.
if __name__ == "__main__":
    app()
