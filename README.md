# 🚀 SnapRoute

**SnapRoute** is a premium, ultra-lightweight, 100% portable screen crop utility for Windows built in PyQt6. It provides seamless on-screen text recognition (OCR) and smart routing, allowing you to instantly copy text/images to your clipboard or search them via Google Search and Google Lens.

---

## ✨ Features

* ** Butter-Smooth Cinematic Opacity Animations:** Hardware-accelerated fade-in/fade-out effects for the screen overlay and HUD, ensuring a highly polished desktop experience.
* ** Smart Routing HUD:** 
  * **`🖼️ Search Image`**: Instantly uploads your cropped graphic to a secure, ephemeral host and opens Google Lens reverse visual search.
  * **`📝 Search Text`**: Performs a standard Google text search for extracted words (only enabled when readable characters are detected).
  * **`📋 Dynamic Copy`**: Automatically swaps between **Copy Text** and **Copy Image** depending on the region's content.
* ** Zero-Jitter Static Design:** The HUD uses a stable, fixed-coordinate layout to ensure buttons never slide or jump out from under your cursor during asynchronous background processing.
* ** Unblocked Multi-Host Image Pipeline:** Sequentially uploads to Uguu.se, Catbox.moe, and Pixeldrain.com with custom User-Agent headers to bypass ISP blocks and firewall restrictions globally.
* ** 100% Portable:** Zero installation or external dependencies. Tesseract-OCR is fully compiled and bundled directly inside a single standalone executable.
* ** High-DPI Scaling Guard:** Automatic logical-to-physical display scaling correction, ensuring pixel-perfect crops on high-resolution, multi-monitor Windows environments.

---

## 🛠️ Tech Stack

* **GUI Framework:** PyQt6
* **OCR Engine:** Tesseract OCR (portable bundle)
* **API Interactions:** `urllib.request` (built-in standard library, zero dependencies)
* **Global Hotkey:** `keyboard` & thread-safe event queue polling

---

## 🚀 Quick Start (Running from Source)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/SnapRoute.git
   cd SnapRoute
   ```

2. Install dependencies:
   ```bash
   pip install PyQt6 pytesseract pyperclip keyboard Pillow pandas
   ```

3. Ensure Tesseract-OCR is installed on your machine (or edit the `tesseract_cmd` path in `box_search.py` to point to your binary):
   * Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

4. Run the utility:
   ```bash
   python main.py
   ```

---

## 📦 How to Build the Standalone `.exe`

To package everything (including the portable Tesseract OCR binary) into a single, redistributable executable, run PyInstaller:

```powershell
pyinstaller.exe --clean --noconsole --onefile --add-data "C:\Program Files\Tesseract-OCR;tesseract" --name="SnapRoute" main.py
```

The compiled standalone executable will be located in the `dist/` directory.

---

## 📝 Shortcuts & Controls

* **Trigger Capture:** `Ctrl + Shift + S` (Global background hook)
* **Cancel Capture:** `Escape` key
* **Exit Daemon:** Right-click the neon green target icon in your System Tray and select **Quit**.
