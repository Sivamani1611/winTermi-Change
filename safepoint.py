#!/usr/bin/env python3
"""
terminalChange.py - Windows-only Pokémon theme applier

Usage:
    python terminalChange.py <pokemon_name_or_id|random>
"""

import os
import sys
import random
import json
import ctypes
import re
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Pokémon Database (copied/adapted)
# ──────────────────────────────────────────────────────────────────────────────

class Pokemon:
    def __init__(self, identifier, name, region, path, pkmn_type,
                 pkmn_type_secondary, dark_threshold):
        self.id       = identifier    # "025" or None for extras
        self.name     = name.lower()
        self.region   = region
        self.path     = path          # full path to .jpg
        self.type1    = pkmn_type
        self.type2    = pkmn_type_secondary
        self.dark_th  = float(dark_threshold)

    def __str__(self):
        return f"{self.id or '---'} {self.name.title()} @ {self.path}"

class Database:
    POKEMON_TYPES = (
      'normal','fire','fighting','water','flying','grass','poison','electric',
      'ground','psychic','rock','ice','bug','dragon','ghost','dark','steel','fairy'
    )

    def __init__(self):
        self._list = []
        self._by_name = {}
        self.base = Path(__file__).parent
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
        with txt.open(encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                parts = line.strip().split()
                if not parts: continue
                name, dark_th, t1 = parts[0], parts[1], parts[2]
                t2 = parts[3] if len(parts)>3 else ""
                rid = f"{idx:03}"
                region = self._determine_region(idx)
                img = self._determine_folder(region) / f"{rid}.jpg"
                img_path = str(img) if img.exists() else None
                poke = Pokemon(rid, name, region, img_path, t1, t2, dark_th)
                self._register(poke)

    def _load_extra(self):
        extra_dir = self.base / "Images" / "Extra"
        if not extra_dir.exists(): return
        for fn in extra_dir.iterdir():
            if fn.suffix.lower() != ".jpg": continue
            name = fn.stem.lower()
            parent = self._by_name.get(name.split('-')[0])
            region = parent.region if parent else None
            t1 = parent.type1 if parent else ""
            t2 = parent.type2 if parent else ""
            dt = parent.dark_th if parent else 0.5
            poke = Pokemon(None, name, region, str(fn), t1, t2, dt)
            self._register(poke)

    def _register(self, p:Pokemon):
        self._list.append(p)
        self._by_name[p.name] = p

    def get(self, key):
        k = str(key).lower()
        if k == "random":
            return random.choice(self._list)
        if k.isdigit():
            return next((p for p in self._list if p.id==f"{int(k):03}"), None)
        return self._by_name.get(k)

    def list_names(self):
        return [p.name.title() for p in sorted(self._list, key=lambda x: x.name)]

# ──────────────────────────────────────────────────────────────────────────────
# WindowsTerminalProvider (inlined)
# ──────────────────────────────────────────────────────────────────────────────

class WindowsTerminalProvider:
    """Sets Windows Terminal backgroundImage via editing settings.json"""

    @staticmethod
    def comment_remover(text: str) -> str:
        def replacer(m):
            s = m.group(0)
            if s.startswith('/') : return " "
            return s
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL|re.MULTILINE
        )
        return re.sub(pattern, replacer, text)

    @staticmethod
    def set_background_image(path: str):
        fp = os.environ['LOCALAPPDATA'] + \
             r'\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'
        with open(fp, 'r+', encoding='utf8') as jf:
            raw = jf.read()
            data = json.loads(WindowsTerminalProvider.comment_remover(raw))

            # normalize profiles to dict if needed
            profs = data.get('profiles')
            if isinstance(profs, list):
                data['profiles'] = {'defaults': {}, 'list': profs}
                profs = data['profiles']

            defaults = profs.get('defaults', {})
            if path is None and 'backgroundImage' in defaults:
                defaults.pop('backgroundImage')
            else:
                defaults['backgroundImage'] = path

            # write back
            jf.seek(0)
            json.dump(data, jf, indent=4, ensure_ascii=False)
            jf.truncate()

    @staticmethod
    def is_compatible() -> bool:
        return 'WT_SESSION' in os.environ

    @staticmethod
    def change_terminal(path: str):
        WindowsTerminalProvider.set_background_image(path)

    @staticmethod
    def clear():
        WindowsTerminalProvider.set_background_image(None)

    def __str__(self):
        return "Windows Terminal"

# ──────────────────────────────────────────────────────────────────────────────
# Wallpaper adapter
# ──────────────────────────────────────────────────────────────────────────────

class WallpaperAdapter:
    @staticmethod
    def set(path: str) -> bool:
        if not path or not Path(path).exists():
            print("  ⚠️ image not found:", path)
            return False
        SPI = 20
        try:
            return bool(ctypes.windll.user32.SystemParametersInfoW(
                SPI, 0, str(Path(path).absolute()), 3))
        except Exception as e:
            print("  ❌ Wallpaper error:", e)
            return False

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        print("Usage: python terminalChange.py <pokemon_name_or_id|random>")
        sys.exit(1)

    key = sys.argv[1]
    db  = Database()
    pkm = db.get(key)
    if not pkm:
        print(f"❌ Pokémon '{key}' not found.")
        print("▶︎ Available:", ", ".join(db.list_names()[:10]), "…")
        sys.exit(1)

    name = pkm.name.title()
    print(f"► Applying theme: {name} (#{pkm.id or 'XX'})")

    # 1) set desktop wallpaper
    w = WallpaperAdapter.set(pkm.path)
    print("  Wallpaper:", "✔" if w else "✗")

    # 2) set terminal backgroundImage
    if WindowsTerminalProvider.is_compatible():
        WindowsTerminalProvider.change_terminal(pkm.path)
        print("  Terminal  :", "✔")
    else:
        print("  Terminal  : ⚠️ not a Windows Terminal session")

    print("✔ Done!" if w else "✗ Done with errors")

if __name__ == "__main__":
    main()