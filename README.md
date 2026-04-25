# Sinker 1945: Strategic Intel

**Sinker 1945** is a high-fidelity, retro-styled naval strategy game built with Python and Pygame. It evolves the classic "Battleship" formula by adding unit-specific abilities, cooldown management, and an AI that features reactive tactical logic and "thinking" simulations.

## 🚢 Fleet Intelligence & Attack Patterns

Strategic success depends on understanding your fleet's strike capabilities, cooldowns, and their ability to evade enemy fire.

### 1. Scout (Reconnaissance)
* **Role**: Tactical Intel.
* **Attack Pattern**: **Area Scan**. Reveals a massive 16x16 grid area to strip away the Fog of War.
* **Ammo**: 1.
* **Evasion Stat**: **0%** (Highly vulnerable).
* **Cooldown**: 6 Turns.
* **Strategy**: Use early to locate high-value targets like the Carrier.

### 2. Destroyer (Area Denial)
* **Role**: Multi-target Strike.
* **Attack Pattern**: **Cross Pattern (+)**. Strikes the center target and the four adjacent tiles (Up, Down, Left, Right).
* **Ammo**: 1.
* **Evasion Stat**: **15%**.
* **Cooldown**: 4 Turns.
* **Strategy**: Best used when you suspect a cluster of small ships or to finish off a unit that has moved slightly.

### 3. Carrier (Heavy Strike)
* **Role**: Capital Ship / Heavy Damage.
* **Attack Pattern**: **2x2 Carpet Bomb**. Strikes a square block of 4 tiles simultaneously.
* **Ammo**: 5.
* **Evasion Stat**: **8%**.
* **Cooldown**: 6 Turns.
* **Strategy**: Provides the highest damage output in a single turn. Devastating if a unit's location is confirmed.

### 4. Frigate (Escort Strike)
* **Role**: Medium Support.
* **Attack Pattern**: **2x2 Square**. Similar to the Carrier but with reduced ammo capacity.
* **Ammo**: 2.
* **Evasion Stat**: **20%**.
* **Cooldown**: 2 Turns.
* **Strategy**: Highly versatile with a short cooldown, allowing for frequent harassment of enemy lines.

### 5. Corvette (Precision Strike)
* **Role**: Rapid Response.
* **Attack Pattern**: **1x1 Precise**. A single, highly accurate shot.
* **Ammo**: 1.
* **Evasion Stat**: **40%** (Highest mobility).
* **Cooldown**: 0 Turns (Always Ready).
* **Strategy**: Your most reliable unit for surgical strikes once a target is revealed.

## 🚀 Key Features

* **Tactical AI**:
    * **Strategic Repositioning**: The AI has a 30% chance to move its ships during its turn to evade your next strike.
    * **Simulated Thinking**: Includes a random pause (0.4s to 0.9s) between turns where the AI "analyzes tactics" with a pulsing visual indicator in the side panel.
* **Dynamic Visuals**: Real-time ocean rendering with parallax scrolling, Fog of War mechanics, and `BurningPixel` impact animations.
* **Admiral's Log**: A real-time combat log tracking every move, strike, and evasion during the mission.
* **Scoring System**: Performance-based scoring that considers hit efficiency and fleet survival.

## 🛠️ Controls

| Key/Action | Function |
| :--- | :--- |
| **Mouse Click** | Select Unit / Designate Strike Coordinates |
| **Hover** | View Unit Intel and Ability Patterns |
| **R** | Retreat (Surrender) or Restart from HQ |
| **Start Button** | Deploy Fleet |

## 📦 Installation & Setup

1.  **Prerequisites**:
    * Python 3.x
    * Pygame library (`pip install pygame`)

2.  **Asset Structure**:
    Ensure the following files are in a folder named `doodads/` within the root directory:
    * **Audio**: `sonar.mp3`, `shot_1.mp3`, `shot_2.mp3`, `plane.mp3`, `bell.mp3`, `start.mp3`, `move.mp3`, `music.mp3`.
    * **Visuals**: `splash.png`.

3.  **Run the Game**:
    ```bash
    python main.py
    ```
