# Novation Launchkey Mini MK4 – Decompiled & Patched MIDI Remote Script (PoC)

⚠️ **Unofficial / Experimental Project**  
This repository contains a manually decompiled, reconstructed, and partially patched version of the Ableton Live MIDI Remote Script for the **Novation Launchkey MK4** and **Launchkey Mini MK4** controllers.

This project exists purely for research, experimentation, and personal use.

---

## Repository Structure

This repository contains **two folders**, each serving a different purpose:

### 1. `default/`
This folder contains the **decompiled and reconstructed** version of the original Ableton-provided MIDI Remote Script.

- Decompiled from the compiled Python bytecode shipped with Ableton Live.
- Manually fixed and reconstructed where decompilation failed or produced incorrect results.
- Not a 100% perfect reconstruction — some logic had to be **rewritten and inferred**.
- All major modes were **manually tested** (keys, pads, scale mode, clip mode, etc.) to ensure basic functionality.
- Intended as a **reference baseline** and a starting point for further work.

### 2. `patched/`
This folder contains a **proof-of-concept (PoC) modification** based on the reconstructed script.

Currently implemented feature:

- **Clip Deletion in Clip Mode**
  - Enter **Clip Mode**
  - **Hold a Scene Trigger** for longer than **0.35 seconds**
  - Press the pad corresponding to the clip you want to delete
  - The clip is deleted

Notes:
- This is a **PoC**, not a finished feature.
- Timing thresholds and behavior may change.
- More patches and refinements may be added in the future.

---

## Installation

1. Locate your Ableton Live MIDI Remote Scripts directory.

   Typical paths:
   - **Windows**  
     `C:\ProgramData\Ableton\Live <version>\Resources\MIDI Remote Scripts\`
   - **macOS**  
     `/Applications/Ableton Live <version>.app/Contents/App-Resources/MIDI Remote Scripts/`

2. Copy the folders from this repository into that directory.

3. The scripts will appear in Ableton Live as:
   - **Launchkey MK4 patched**
   - **Launchkey Mini MK4 patched**

4. In Ableton Live:
   - Go to **Preferences → Link / MIDI**
   - Select the patched script matching your controller

No additional configuration is required.

---

## Important Disclaimers

- **No Ableton support**
  - Ableton does not support this script.
  - Do not contact Ableton regarding issues caused by this project.

- **No author support**
  - This repository is provided as-is.
  - Issues, questions, or breakage are your responsibility.

- **Not endorsed**
  - Not endorsed by Ableton, Novation, or any third party.

- **Use at your own risk**
  - This script can break with Ableton updates.
  - Bugs, crashes, or unexpected behavior are possible.
  - You are responsible for backups and recovery.

---

## Purpose of This Project

- Reverse-engineering and understanding Ableton MIDI Remote Scripts
- Experimenting with controller behavior beyond stock limitations
- Enabling features not provided by default
- Educational and research use

---

## License

No explicit license is provided.  
Use, modify, and distribute **at your own legal and technical risk**.

---

## Final Note

This is **experimental software**.  
If you rely on your controller in live or professional environments, **do not use this** without thorough testing.

Proceed carefully.

