import os
import sys
import random
import json
import ctypes
import re
from pathlib import Path
from PIL import Image, ImageStat

# ──────────────────────────────────────────────────────────────────────────────
# Pokémon Database (loads Data/pokemon.txt and Images/…)
# ──────────────────────────────────────────────────────────────────────────────

class Pokemon:
    def __init__(self, identifier, name, region, path, pkmn_type,
                 pkmn_type_secondary, dark_threshold):
        self.id      = identifier       # zero-padded string or None for extras
        self.name    = name.lower()
        self.region  = region
        self.path    = path             # full path to the .jpg image
        self.type1   = pkmn_type
        self.type2   = pkmn_type_secondary
        self.dark_th = float(dark_threshold)

class Database:
    """Loads all Pokémon (including extras) from local Data/ and Images/ folders."""
    def __init__(self):
        self._list    = []
        self._by_name = {}
        self.base     = Path(__file__).parent
        self._load_data()
        self._load_extra()

    def _determine_region(self, idx:int):
        if idx < 152: return "kanto"
        if idx < 252: return "johto"
        if idx < 387: return "hoenn"
        if idx < 494: return "sinnoh"
        if idx < 650: return "unova"
        if idx < 720: return "kalos"
        return None

    def _determine_folder(self, region:str):
        sufmap = {
          "kanto":"I - Kanto","johto":"II - Johto","hoenn":"III - Hoenn",
          "sinnoh":"IV - Sinnoh","unova":"V - Unova","kalos":"VI - Kalos"
        }
        suf = sufmap.get(region)
        return self.base / "Images" / f"Generation {suf}"

    def _load_data(self):
        txt = self.base / "Data" / "pokemon.txt"
        if not txt.exists():
            print("❌ Data/pokemon.txt not found.")
            sys.exit(1)
        with txt.open(encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                parts = line.strip().split()
                if not parts: continue
                name, dark_th, t1 = parts[0], parts[1], parts[2]
                t2 = parts[3] if len(parts) > 3 else ""
                rid = f"{idx:03}"
                region = self._determine_region(idx)
                img = self._determine_folder(region) / f"{rid}.jpg"
                img_path = str(img) if img.exists() else None
                poke = Pokemon(rid, name, region, img_path, t1, t2, dark_th)
                self._register(poke)

    def _load_extra(self):
        extra = self.base / "Images" / "Extra"
        if not extra.exists():
            return
        for fn in extra.iterdir():
            if fn.suffix.lower() != ".jpg":
                continue
            name = fn.stem.lower()
            parent = self._by_name.get(name.split('-')[0])
            region = parent.region if parent else None
            t1 = parent.type1 if parent else ""
            t2 = parent.type2 if parent else ""
            dt = parent.dark_th if parent else 0.5
            poke = Pokemon(None, name, region, str(fn), t1, t2, dt)
            self._register(poke)

    def _register(self, poke:Pokemon):
        self._list.append(poke)
        self._by_name[poke.name] = poke

    def get(self, key):
        k = str(key).lower()
        if k == "random":
            return random.choice(self._list)
        if k.isdigit():
            idx = int(k)
            target = f"{idx:03}"
            return next((p for p in self._list if p.id == target), None)
        return self._by_name.get(k)

    def list_names(self):
        return sorted(p.name.title() for p in self._list)

# ──────────────────────────────────────────────────────────────────────────────
# Image luminance helper (Pillow)
# ──────────────────────────────────────────────────────────────────────────────

def avg_luminance(img_path:str) -> float:
    """Return 0.0 (dark) → 1.0 (bright) average luminance of the image."""
    im = Image.open(img_path).convert("L")
    stat = ImageStat.Stat(im)
    return stat.mean[0] / 255.0

# ──────────────────────────────────────────────────────────────────────────────
# Windows Terminal Provider
# ──────────────────────────────────────────────────────────────────────────────

class WindowsTerminalProvider:
    """Sets or clears Windows Terminal backgroundImage and foreground."""

    @staticmethod
    def comment_remover(text:str) -> str:
        """Strip // and /* */ comments so JSON can parse."""
        def repl(m):
            s = m.group(0)
            return " " if s.startswith('/') else s
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL|re.MULTILINE
        )
        return re.sub(pattern, repl, text)

    @staticmethod
    def _load_settings():
        fp = Path(os.getenv("LOCALAPPDATA", "")) / \
             "Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json"
        raw = fp.read_text(encoding="utf8")
        data = json.loads(WindowsTerminalProvider.comment_remover(raw))
        profs = data.get("profiles")
        if isinstance(profs, list):
            data["profiles"] = profs = {"defaults": {}, "list": profs}
        return fp, data

    @staticmethod
    def _write_settings(fp:Path, data:dict):
        fp.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf8")

    @staticmethod
    def set_background_image(path:str):
        """Set backgroundImage + auto‐contrast foreground in profiles.defaults."""
        fp, data = WindowsTerminalProvider._load_settings()
        defaults = data["profiles"].setdefault("defaults", {})

        # remove colorScheme so raw foreground is honored
        defaults.pop("colorScheme", None)

        # set or clear backgroundImage
        if path:
            defaults["backgroundImage"] = path
        else:
            defaults.pop("backgroundImage", None)

        # compute luminance & override foreground
        if path and Path(path).exists():
            lum = avg_luminance(path)
            defaults["foreground"] = "#000000" if lum > 0.5 else "#FFFFFF"
        else:
            defaults.pop("foreground", None)

        WindowsTerminalProvider._write_settings(fp, data)

    @staticmethod
    def clear():
        """Remove backgroundImage, foreground, and colorScheme overrides."""
        fp, data = WindowsTerminalProvider._load_settings()
        defaults = data["profiles"].setdefault("defaults", {})
        for key in ("backgroundImage", "foreground", "colorScheme"):
            defaults.pop(key, None)
        WindowsTerminalProvider._write_settings(fp, data)

    @staticmethod
    def is_compatible() -> bool:
        return "WT_SESSION" in os.environ

# ──────────────────────────────────────────────────────────────────────────────
# Wallpaper Adapter
# ──────────────────────────────────────────────────────────────────────────────

class WallpaperAdapter:
    @staticmethod
    def set(path:str) -> bool:
        if not path or not Path(path).exists():
            print("  ⚠️ image not found:", path)
            return False
        SPI_SETDESKWALLPAPER = 20
        try:
            return bool(ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, str(Path(path).absolute()), 3))
        except Exception as e:
            print("  ❌ Wallpaper error:", e)
            return False

# ──────────────────────────────────────────────────────────────────────────────
# Main CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        print("Usage: python terminalChange.py <pokemon_name_or_id|random|clear>")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd in ("clear", "reset"):
        WindowsTerminalProvider.clear()
        print("✔ Windows Terminal overrides cleared.")
        sys.exit(0)

    db  = Database()
    pkm = db.get(cmd)
    if not pkm:
        print(f"❌ Pokémon '{cmd}' not found.")
        print("▶︎ Available examples:", ", ".join(db.list_names()[:10]), "…")
        sys.exit(1)

    print(f"► Applying theme: {pkm.name.title()} (#{pkm.id or 'XX'})")

    # 1) desktop wallpaper
    ok_wp = WallpaperAdapter.set(pkm.path)
    print("  Wallpaper:", "✔" if ok_wp else "✗")

    # 2) Windows Terminal
    if WindowsTerminalProvider.is_compatible():
        WindowsTerminalProvider.set_background_image(pkm.path)
        print("  Terminal :", "✔")
    else:
        print("  Terminal : ⚠️ not a Windows Terminal session")

    print("✔ Done!" if ok_wp else "✗ Completed with errors")

if __name__ == "__main__":
    main()