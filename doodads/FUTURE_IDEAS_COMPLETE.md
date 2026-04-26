# Sinkers 1945: Future Development & Ability Synergies

This document archives proposed tactical enhancements, unit archetypes, and atmospheric improvements to evolve the gameplay from standard naval combat into a high-stakes "Tactical Commander" experience.

---

## 🚀 1. Ability Synergy System (Combos)
The core evolution of the game focuses on "1 + 1 = 3" scenarios where unit sequences provide mechanical bonuses.

### A. The "Data-Link" Combo (Scout + Corvette)
* **Trigger:** Corvette attacks a tile revealed by a Scout within the last 3 turns.
* **Bonus:** 1.5x damage multiplier or immediate Scout cooldown reset.
* **Visual:** Pulsing SHD orange tracer trails and impact pulses.

### B. The "Overwhelm" Combo (Destroyer + Carrier)
* **Trigger:** Carrier strikes a 2x2 area recently targeted by a Destroyer Barrage.
* **Bonus:** 100% accuracy (removes random drift/miss chance) for the Carrier.

### C. The "Escort Shield" (Frigate + Capital Ship)
* **Trigger:** Frigate is positioned adjacent to a Carrier or Destroyer.
* **Bonus:** 30% chance for the Frigate to "intercept" an incoming AI shot.

---

## 🚢 2. New Unit: The "Huff-Duff" Frigate (RIV-45)
* **Role:** Radio Interception & Triangulation (SIGINT).
* **Ability:** **Radio Triangulation.** Highlights a 5x5 "Heat Map" where an enemy signature is detected.
* **Passive:** **Radio Silence.** Friendly ships in the vicinity have a lower chance of being spotted by AI Recon.

---

## 🎨 3. Atmospheric & UI Enhancements
* **Analog SHD Aesthetic:** Flickering green phosphor waves and Morse code static bursts.
* **Tactical Shake:** Subtle screen jitter when the player's flagship takes damage.
* **Session Reports:** Exporting the Admiral's Log to a `.txt` "Service Record" post-mission.

---

## 🌊 4. Submarine Logic: The "Sentinel Protocol"
Submarines act as Defensive Sentinels restricted to their respective home sectors.

* **Submerged State:** Invisible to standard scans; loses 10% Oxygen per turn.
* **Deep-Sea Sonar:** Provides a permanent 10x10 Heat Map via passive hydrophones.
* **Torpedo Intercept:** 40% chance to negate an AI attack within a 3-tile radius (reveals position).

---

## 🏝️ 5. Terrain & Archipelago System
* **Dead Zone Spawning:** Islands project a 2-block exclusion radius (5x5 area) where ships cannot spawn.
* **Topographic UI:** Zone marked with HUD-style contour lines.
* **Shared VFX:** Landmasses trigger smoke/sparks when hit to maintain Fog of War mystery.

---

## ✈️ 6. Cinematic Carrier Engagement (The Corsair Flyover)
* **Inbound:** Selecting the Carrier triggers a 5-plane V-formation of F4U Corsairs [AIR STRIKE READY].
* **Outbound:** 5th shot triggers an Echelon formation return flight [AIR STRIKE DONE].
* **Visuals:** Signature "Inverted Gull" wings with cyan HUD outlines.

---

## 🏗️ 7. Auxiliary Fleet & Battlefield Manipulation
* **The Minelayer:** Deploys "Steel Garden" mines to cancel AI turns.
* **The Heavy Cruiser:** "Main Battery Salvo" straight-line damage with heavy 6-turn cooldown.
* **The Hospital Ship:** Restores 1 HP; triggers "Morale Penalty" for AI if attacked.
* **The Recon Seaplane:** Drops flares to permanently lift Fog of War in a 3x3 zone.

---

## 🎯 8. Kinetic Targeting HUD
* **Kinetic Snap-to-Grid:** Crosshair bars lerp from a 40px gap to a 5px lock-on position upon tile hover.
* **Status Colors:** Cyan (Standard), Solid White (Hard Lock), Red (Invalid/Island).
* **Audio Hook:** Mechanical "clunk" sound upon animation completion.

---

## 🌫️ 9. Stealth, Sabotage & Fixed Intelligence
* **The Ghost Blockade Runner:** Deploys "Whiteout" smoke zones (3x3) for total untargetability.
* **The Heavy Monitor:** Snipes back rows without LoS; permanently revealed after firing.
* **The Commando Transport:** 1HP vessel that disables AI abilities upon reaching the midline.
* **Observation Balloon:** Static unit providing a permanent 90-degree vision cone.

---

## 📊 10. HUD Evolution: The "Unit Status Tray"
* **Status Indicators:** Icons for REVEALED, STEALTH ACTIVE, and SUPPRESSED.
* **Vision Shader:** "Flashlight" effect for line-of-sight units.

---

## 🏗️ 11. Vectorized Movement & Collision (Iron Tide Engine)
Transition from grid-snapping to smooth naval physics using float-based vectors.

* **Float Orientation:** 360° rotation using float forward vectors (math.cos/sin).
* **The Action Economy:** 1 Global Action per turn (Move OR Attack).
* **Turning Penalty:** Movement range is consumed by rotation (Angle Diff * Turn Cost).
* **Kinetic Collision (Rule 5/6):** Impact damage ignores evasion; stops all movement vectors instantly.
* **Visual Pathfinding:** A dashed trajectory line is drawn from the bow to the target tile.

---

## 🚜 12. "Strikers 1945" (Land Port Potential)
* **Concept:** Re-skinning naval logic into armor combat.
* **Terrain:** Buildings replace Islands; Mud replaces Deep Water.
* **Units:** M18 Hellcat (Corvette), M4 Sherman (Destroyer), Mobile Artillery (Carrier).
