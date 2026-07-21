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

import stat
import time

_PRESERVE_PATHS = [
    ".env",
    "config",
    "data",
    "logs",
]


def _kill_running_exe():
    """Attempt to terminate any running aegisScout.exe process before build."""
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "aegisScout.exe"], capture_output=True, text=True)
            time.sleep(0.5)
        except Exception:
            pass


def _safe_remove(path: Path):
    """Safely remove a file or directory with permission handling and retries."""
    if not path.exists():
        return
    try:
        if path.is_file() or path.is_symlink():
            try:
                path.chmod(stat.S_IWRITE)
            except Exception:
                pass
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except PermissionError as pe:
        print(f"  [UYARI] {path.name} kilitli veya silinemedi ({pe}), build sırasında üzerine yazılacak.")
    except Exception as e:
        print(f"  [UYARI] {path.name} silinirken hata: {e}")


def _clean_build_artifacts(clean_mode: bool = False):
    """
    Build öncesi temizlik.
    
    clean_mode=True  : dist/ TAMAMEN silinir (user data dahil)
    clean_mode=False : dist/ içinde sadece PyInstaller çıktısı (.exe, _internal/)
                        silinir; .env, config/, data/, logs/ korunur
    """
    _kill_running_exe()

    if clean_mode:
        if DIST_DIR.exists():
            _safe_remove(DIST_DIR)
            print(f"[CLEAN] dist/ temizlendi.")
        if BUILD_DIR.exists():
            _safe_remove(BUILD_DIR)
            print(f"[CLEAN] build/ temizlendi.")
        for spec_file in ROOT.glob("*.spec"):
            if spec_file.name != "build_exe.spec":
                _safe_remove(spec_file)
        print("[CLEAN] Temiz build modu tamamlandı.")
        return

    # Normal mod: dist/ içindeki PyInstaller çıktısını sil, kullanıcı verilerini koru
    if DIST_DIR.exists():
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
                _safe_remove(item)
                print(f"  [SILINDI] {item.name}/")
            else:
                _safe_remove(item)
                print(f"  [SILINDI] {item.name}")
    else:
        print("  dist/ henüz mevcut değil, yeni oluşturulacak.")

    # build/ tamamen sil (her zaman güvenli, PyInstaller geçici dosyası)
    if BUILD_DIR.exists():
        _safe_remove(BUILD_DIR)
        print(f"  [SILINDI] build/ (PyInstaller geçici)")

    # Root'taki ekstra .spec dosyalarını sil (build_exe.spec koru)
    for spec_file in ROOT.glob("*.spec"):
        if spec_file.name != "build_exe.spec" and (ROOT / "scripts" / spec_file.name).exists():
            _safe_remove(spec_file)


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
