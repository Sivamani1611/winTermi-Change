# Pokémon Terminal Themes (Windows)

A Windows-only, single-file Python script to instantly apply a Pokémon wallpaper and update your Windows Terminal background (with auto-contrasting text) in one command.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

---

## 🚀 Features

- 🎨 **Wallpaper**  
  Sets your desktop wallpaper to any Pokémon image (Generations I–VI + Extras).

- 🖥️ **Windows Terminal**  
  Patches your `settings.json`:
  - Sets `backgroundImage` to the same Pokémon image.
  - Computes average image luminance (via [Pillow](https://python-pillow.org/)) and chooses **white** or **black** text for maximum contrast.
  - Removes any existing `colorScheme` override so your raw `foreground` is honored.

- 🔄 **Random themes**  
  `python terminalChange.py random`

- ❌ **Reset / Clear**  
  `python terminalChange.py clear` restores Windows Terminal to its default appearance.

- 🗂️ **Zero dependencies** beyond Python 3.8+ and Pillow.

---

## 📋 Prerequisites

- Windows 10 / 11
- [Windows Terminal](https://aka.ms/terminal) installed
- Python 3.8 or newer
- Pillow for image processing:
  ```bash
  pip install pillow
  ```

---

## 📥 Installation

1. **Clone or download** this repo:
   ```bash
   git clone https://github.com/sivamani1611/terminal-change.git
   cd terminal-change
   ```
2. **Copy** the original Pokémon data and images from [LazoVelko/Pokemon-Terminal](https://github.com/LazoVelko/Pokemon-Terminal):
   ```
   terminal-change/
   ├── terminalChange.py
   ├── Data/
   │   └── pokemon.txt
   └── Images/
       ├── Extra/
       ├── Generation I - Kanto/
       ├── Generation II - Johto/
       ├── … etc …
   ```
3. Install Pillow:
   ```bash
   pip install pillow
   ```

---

## 💻 Usage

```bash
# Apply a specific Pokémon theme by name
python terminalChange.py pikachu

# Apply by Pokédex ID
python terminalChange.py 25

# Apply a random theme
python terminalChange.py random

# Reset Windows Terminal overrides
python terminalChange.py clear
```

### Example Output

```text
► Applying theme: Pikachu (#025)
  Wallpaper: ✔
  Terminal : ✔
✔ Done!
```

> **Note**: After running, **close all** Windows Terminal windows and re-open to see the new background and text color.

---

## ⚙️ How It Works

1. **Loads** Pokémon metadata from `Data/pokemon.txt`.  
2. **Discovers** each image under the `Images/…` folder (Generations + Extra).  
3. **Sets** desktop wallpaper via Windows API (`SystemParametersInfoW`).  
4. **Calculates** average luminance with Pillow to determine light/dark text.  
5. **Reads** your Windows Terminal `settings.json` (removing comments).  
6. **Normalizes** `profiles` to ensure a `defaults` block.  
7. **Removes** any existing `colorScheme` override so new `foreground` is applied.  
8. **Writes** `backgroundImage` and computed `foreground` into `profiles.defaults`.  
9. **Saves** the JSON. Next Terminal launch will pick up the new theme.

---

## 📂 Project Structure

```
terminal-change/
├── terminalChange.py       # Single-file entry point
├── Data/
│   └── pokemon.txt         # Pokémon metadata (name, type, threshold)
└── Images/
    ├── Extra/              # Extra / fan-art images
    ├── Generation I - Kanto/
    ├── Generation II - Johto/
    └── … other generations
```

---

## 🤝 Contributing

- PRs welcome!  
- Please follow PEP 8 and include tests if adding logic.  
- Feel free to add support for custom themes, additional terminal emulators, or color palettes!

---

*Built upon the amazing [LazoVelko/Pokemon-Terminal](https://github.com/LazoVelko/Pokemon-Terminal) data and images.*