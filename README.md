# Novation Launchkey MK4 – Decompiled & Patched MIDI Remote Script

⚠️ **Unofficial / Experimental Project**

This repository contains a manually decompiled, reconstructed, and patched version of the Ableton Live MIDI Remote Script for the **Novation Launchkey MK4** and **Launchkey Mini MK4** controllers.

This project exists for research, experimentation, and personal use.

---

## 📁 Repository Structure

This repository contains two main directories:

### `default/`
The **decompiled and reconstructed** version of the original Ableton-provided MIDI Remote Script.

- Decompiled from compiled Python bytecode shipped with Ableton Live
- Manually fixed and reconstructed where decompilation failed
- Not a 100% perfect reconstruction — some logic was rewritten and inferred
- All major modes were manually tested (keys, pads, scale mode, clip mode, etc.)
- Intended as a **reference baseline** for further development

### `patched/`
A **proof-of-concept modification** based on the reconstructed script.

**Current Features:**
- **Clip Deletion in Clip Mode**
  - Enter Clip Mode
  - Hold a Scene Trigger button for 0.35+ seconds to enable delete mode
  - Press the pad corresponding to the clip you want to delete
  - The clip is deleted

**Notes:**
- This is a PoC, not a finished feature
- Timing thresholds and behavior may change
- More patches and refinements may be added in the future

---

## 🚀 Installation

1. **Locate your Ableton Live MIDI Remote Scripts directory:**

   **Windows:**
   ```
   C:\ProgramData\Ableton\Live <version>\Resources\MIDI Remote Scripts\
   ```

   **macOS:**
   ```
   /Applications/Ableton Live <version>.app/Contents/App-Resources/MIDI Remote Scripts/
   ```

2. **Copy the folders** from this repository into that directory.

3. **In Ableton Live:**
   - Go to **Preferences → Link / MIDI**
   - Select the patched script matching your controller:
     - **Launchkey MK4 patched** (for 25, 37, 49, or 61 key models)
     - **Launchkey Mini MK4 patched** (for Mini model)

No additional configuration required.

---

## ⚠️ Important Disclaimers

### No Support
- **Ableton does not support this script** — do not contact Ableton regarding issues
- **No author support** — this repository is provided as-is
- **Not endorsed** by Ableton, Novation, or any third party

### Use at Your Own Risk
- This script can break with Ableton updates
- Bugs, crashes, or unexpected behavior are possible
- You are responsible for backups and recovery
- **Do not use in live or professional environments without thorough testing**

---

## 🎯 Project Purpose

- Reverse-engineering and understanding Ableton MIDI Remote Scripts
- Experimenting with controller behavior beyond stock limitations
- Enabling features not provided by default
- Educational and research use

---

## 📄 License

No explicit license is provided.  
Use, modify, and distribute **at your own legal and technical risk**.

---

## ⚡ Quick Start

1. Clone or download this repository
2. Copy the `patched/` folder contents to your Ableton MIDI Remote Scripts directory
3. Restart Ableton Live
4. Select the patched script in Preferences → Link / MIDI
5. Test thoroughly before using in production

---

**This is experimental software. Proceed carefully.**

