"""
aegisScout — PyInstaller Build Betigi v3
======================================

Kullanim:
    Cift tikla: build.bat           (en kolay)
    Terminal  : python scripts/build_exe.py
              : python scripts/build_exe.py --clean   (tam temiz build)

Cikti: dist/aegisScout.exe

Build modlari:
    Normal  (varsayilan): .env, config/, data/, logs/ korunur
    --clean             : dist/ tamamen silinir, baslanir
"""

import sys
import subprocess
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
SPEC_FILE = ROOT / "scripts" / "build_exe.spec"
DIST_DIR  = ROOT / "dist"
BUILD_DIR = ROOT / "build"

# dist/ icinde korunacak dosya/klasorler (normal build'de)
_PRESERVE_PATHS = [
    ".env",
    "config",
    "data",
    "logs",
]


def _clean_build_artifacts(clean_mode: bool = False):
    """
    Build oncesi temizlik.
    
    clean_mode=True  : dist/ TAMAMEN silinir (user data dahil)
    clean_mode=False : dist/ icinde sadece PyInstaller ciktisi (.exe, _internal/)
                        silinir; .env, config/, data/, logs/ korunur
    """
    if clean_mode:
        if DIST_DIR.exists():
            shutil.rmtree(DIST_DIR)
            print(f"[CLEAN] dist/ tamamen temizlendi.")
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)
            print(f"[CLEAN] build/ tamamen temizlendi.")
        for spec_file in ROOT.glob("*.spec"):
            spec_file.unlink()
        print("[CLEAN] Temiz build modu: her sey silindi.")
        return

    # Normal mod: dist/ icindeki PyInstaller ciktisini sil, kullanici verilerini koru
    if DIST_DIR.exists():
        # Silinecek ogeler: .exe, _internal/, her sey ama PRESERVE haric
        for item in DIST_DIR.iterdir():
            should_preserve = False
            for preserve in _PRESERVE_PATHS:
                if item.name == preserve or item.name.startswith(preserve):
                    should_preserve = True
                    break
            if should_preserve:
                print(f"  [KORUNDU] {item.name}")
                continue
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  [SILINDI] {item.name}/")
            else:
                item.unlink()
                print(f"  [SILINDI] {item.name}")
    else:
        print("  dist/ henuz mevcut degil, yeni olusturulacak.")

    # build/ tamamen sil (her zaman guvenli, PyInstaller gecici dosyasi)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  [SILINDI] build/ (PyInstaller gecici)")

    # Root'taki .spec dosyalarini sil
    for spec_file in ROOT.glob("*.spec"):
        spec_file.unlink()
        print(f"  [SILINDI] {spec_file.name}")


def _find_py311() -> Path | None:
    """Windows'ta Python 3.11 dogru calistirilabilir yolunu arar."""
    candidates = [
        Path(r"C:\Users\mrSpy\AppData\Local\Programs\Python\Python311\python.exe"),
        Path(r"C:\Python311\python.exe"),
        Path(r"C:\Program Files\Python311\python.exe"),
        Path(r"C:\Program Files (x86)\Python311\python.exe"),
    ]
    for p in candidates:
        if p.exists():
            return p
    try:
        r = subprocess.run(["py", "-3.11", "-c", "import sys; print(sys.executable)"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return Path(r.stdout.strip())
    except Exception:
        pass
    return None


def _ensure_pyinstaller():
    """PyInstaller bu Python surumunde yok ise 3.11 ile yeniden baslat."""
    try:
        import PyInstaller  # noqa: F401
        return
    except ImportError:
        pass

    print(f"[!] Bu Python'da PyInstaller yok: {sys.executable}")
    print("[>>] PyInstaller yukleniyor...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            timeout=120,
        )
        print("[OK] PyInstaller basariyla yuklendi.")
        return
    except Exception:
        pass

    py311 = _find_py311()
    if py311 is None:
        print("[HATA] Python 3.11 bulunamadi. PyInstaller'i manuel kurun:")
        print("       pip install pyinstaller")
        sys.exit(1)

    print(f"[>>] Python 3.11 bulundu, yeniden baslatiliyor: {py311}")
    result = subprocess.run([str(py311)] + sys.argv, cwd=ROOT)
    sys.exit(result.returncode)


def _check_webview():
    """Check if webview (pywebview) is available — warn if not."""
    try:
        import webview  # noqa: F401
        return True
    except ImportError:
        print("[!] UYARI: pywebview (webview) bu Python'da yuklu degil.")
        print("    GUI ozelligi EXE'de calismayacak. Sadece CLI modu kullanilabilir.")
        print("    Yuklemek icin: pip install pywebview")
        return False


def build():
    parser = argparse.ArgumentParser(description="aegisScout PyInstaller Build")
    parser.add_argument("--clean", action="store_true",
                        help="Tam temiz build: .env, config, data, logs DAHIL her sey silinir")
    args = parser.parse_args()

    _ensure_pyinstaller()
    _check_webview()

    print(f"[aegisScout Build] Python      : {sys.executable}")
    print(f"[aegisScout Build] Proje kok   : {ROOT}")
    print(f"[aegisScout Build] .spec dosyasi: {SPEC_FILE}")
    print(f"[aegisScout Build] Build modu  : {'TAM TEMIZ (--clean)' if args.clean else 'NORMAL (kullanici verileri korunur)'}")
    print()

    if not SPEC_FILE.exists():
        print(f"[HATA] .spec dosyasi bulunamadi: {SPEC_FILE}")
        sys.exit(1)

    # Build oncesi temizlik — user data korumali
    _clean_build_artifacts(clean_mode=args.clean)
    print()

    print("[aegisScout Build] PyInstaller baslatiliyor...\n")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(SPEC_FILE)],
        cwd=ROOT,
    )

    if result.returncode != 0:
        print(f"\n[HATA] Build basarisiz. Cikis kodu: {result.returncode}")
        print("\nYaygin hata cozumleri:")
        print("  1) Emin olun: pip install -e . (tum bagimliliklar yuklu)")
        print("  2) PyInstaller versiyonu: pip install --upgrade pyinstaller")
        print("  3) Windows Defender/antivirus build klasorunu engelliyor olabilir")
        sys.exit(result.returncode)

    exe_name = "aegisScout.exe" if sys.platform == "win32" else "aegisScout"
    exe_path = DIST_DIR / exe_name

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] Build tamamlandi!")
        print(f"    Calistirilabilir dosya: {exe_path}")
        print(f"    Boyut: {size_mb:.1f} MB")

        # Post-build: .env dosyasini dist/ icine kopyala (varsa)
        env_src = ROOT / ".env"
        env_dst = DIST_DIR / ".env"
        if env_src.exists():
            import shutil
            shutil.copy2(env_src, env_dst)
            print(f"    [OK] .env dosyasi dist/ icne kopyalandi.")
        else:
            env_example = ROOT / ".env.example"
            if env_example.exists():
                shutil.copy2(env_example, env_dst)
                print(f"    [!] .env bulunamadi, .env.example -> dist/.env kopyalandi (anahtarlar bos).")
            else:
                print(f"    [!] .env dosyasi bulunamadi — API anahtarlari olmadan calismaz.")
    else:
        print(f"\n[UYARI] Build tamamlandi ancak {exe_path} bulunamadi.")
        print("dist/ klasoru icerigini kontrol edin.")


if __name__ == "__main__":
    build()
