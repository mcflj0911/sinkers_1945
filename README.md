# Sinkers 1945: Strategic Intel

![image](https://github.com/mcflj0911/sinkers_1945/blob/main/doodads/splash.png)

**Sinkers 1945** is a high-fidelity, retro-styled naval strategy game built with Python and Pygame. It evolves the classic "Battleship" formula by adding unit-specific abilities, cooldown management, and an immersive atmospheric engine.

## 🌊 Dynamic Weather & Environment

The battlefield and HUD are rendered with a multi-layered environmental simulation:
* **Parallax Wind Streaks**: Semi-transparent wind particles drift across the board at higher speeds than the water.
* **Sector-Locked Clouds**: Atmospheric clouds are clipped to their respective fields (AI North / Player South) and flow in the direction of the local current.
* **Intel Weather Sync**: The Fleet Intel panel now features localized rain and lightning effects that synchronize across the multi-ship display area.
* **Naval Silhouettes**: All combat units (excluding the 1x1 Scout) feature a **triangular bow** to indicate orientation.
* **Ship Bobbing**: Operational units feature a time-based sinusoidal wobble to simulate ocean buoyancy.

## 🚢 Fleet Intelligence & Strike Profiles

The HUD now supports a dual-intel display, rendering high-resolution technical readouts for multiple flagship classes simultaneously in the right-hand log area.

| Unit | Role | Attack Pattern | Special Passive / Traits | Cooldown |
| :--- | :--- | :--- | :--- | :--- |
| **Scout** | Tactical Recon | **Area Scan** | **Wide-Band Sonar**: Reveals a massive 16x16 grid area. No projectile trail. | 6 Turns |
| **Corvette** | Harassment | **Precision Strike** | **Evasion Bypass**: Shells ignore the target's evasion chance. | 0 Turns |
| **Frigate** | Escort | **Double Tap** | **Twin Batteries**: Fires two shots per turn in a 2x1 or 1x2 area. | 2 Turns |
| **Destroyer** | Area Denial | **Barrage** | **Suppressive Fire**: Strikes 8 random coordinates in a 4x4 zone. | 4 Turns |
| **Carrier** | Force Multiplier | **Airstrike** | **Squadron Launch**: Deploys 5 planes to strike a 2x2 grid simultaneously. | 6 Turns |
| **Dreadnought** | Siege Platform | **Bombardment** | **Heavy Armor**: Absorbs the first 2 direct hits before taking hull damage. | 8 Turns |

## ⚡ Visual Identification (Active States)
When a unit's cooldown reaches 0, it emits a unique tactical aura to signify combat readiness:
* **Scout**: Rapid green sonar pings expanding from the hull.
* **Carrier**: Miniature squadron silhouettes circling the deck with afterburner trails.
* **Dreadnought**: A heavy red "Battery Charge" glow with counter-rotating orbital nodes and slow-moving kinetic shockwaves.
* **Escort Classes**: A pulsing golden ammunition icon indicating "Loaded" status.

## 🛠️ Controls

| Key/Action | Function |
| :--- | :--- |
| **Mouse Click** | Select Unit / Designate Strike Coordinates |
| **Hover** | View Unit Intel and Ability Patterns |
| **R** | Retreat (Surrender) or Restart from HQ |
| **Start Button** | Deploy Fleet |

## 📦 # Installation & Setup

### 1. Install Python
The game requires **Python 3.6** or higher. Download the installer for your operating system from the official Python website:
* **All Platforms:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
* **Recommended for Windows (3.6.8):** [Python 3.6.8 Download](https://www.python.org/downloads/release/python-368/)

> **Note:** During installation on Windows, ensure you check the box that says **"Add Python to PATH"**.

### 2. Install Dependencies
Open your terminal (macOS/Linux) or Command Prompt/PowerShell (Windows) and run the following command to install the required **Pygame Community Edition** library:
```bash
pip install pygame-ce
```

### 3. Verify Asset Structure
Ensure your project folder is organized as follows:
* `main.py`
* `doodads/` (Contains `ship.png`, `ship2.png`, `sonar.mp3`, `music.mp3`, etc.)

### 4. Run the Game
Navigate to your project directory in the terminal and execute the game using this command:
```bash
python main.py
```