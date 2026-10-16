# Empire: Four Kingdoms — Robber Baron Attack Bot
## A Python Automation Learning Project

---

## 📁 Project Structure

```
empire_bot/
├── main.py                      ← START HERE — runs the bot
├── config.py                    ← All settings (edit this)
├── bot/
│   ├── adb.py                   ← Controls LDPlayer via ADB
│   ├── screen.py                ← Image recognition (OpenCV)
│   └── attack_bot.py            ← Robber Baron attack logic
├── tools/
│   └── capture_template.py      ← Helper to capture button images
├── assets/                      ← Put your template images here
│   ├── map_button.png
│   ├── robber_baron_icon.png
│   ├── attack_button.png
│   └── send_troops_button.png
└── logs/
    └── attack_log.txt           ← Created automatically
```

---

## ⚡ Quick Start (Step by Step)

### Step 1: Enable ADB in LDPlayer
1. Open LDPlayer
2. Click the **Settings** icon (gear icon on the right panel)
3. Go to **Other Settings**
4. Enable **ADB debugging**
5. Note the ADB port (usually `5555`)

### Step 2: Find your ADB path
LDPlayer installs ADB here:
```
C:\LDPlayer\LDPlayer9\adb.exe
```
Update `ADB_PATH` in `config.py` if yours is different.

### Step 3: Connect ADB
Open PowerShell and run:
```powershell
C:\LDPlayer\LDPlayer9\adb.exe connect 127.0.0.1:5555
C:\LDPlayer\LDPlayer9\adb.exe devices
```
You should see `emulator-5554` or similar. Update `DEVICE_ID` in `config.py`.

### Step 4: Install Python Libraries
```powershell
pip install opencv-python pillow numpy
```
✅ Already done!

### Step 5: Capture Template Images
Run the capture tool to save images of game buttons:
```powershell
cd C:\Users\Aditya Mohite\.gemini\antigravity\scratch\empire_bot
python tools/capture_template.py
```
It will guide you through capturing:
- World Map button
- Robber Baron castle icon
- Attack button
- Send troops button

### Step 6: Run the Bot!
```powershell
python main.py
```

---

## 🔧 Configuration (config.py)

| Setting | Default | Description |
|---------|---------|-------------|
| `ADB_PATH` | LDPlayer path | Path to adb.exe |
| `DEVICE_ID` | `emulator-5554` | Your emulator's ADB ID |
| `ATTACK_INTERVAL_SECONDS` | `120` | Seconds between attack rounds |
| `MAX_ATTACKS_PER_SESSION` | `30` | Safety limit on total attacks |
| `CONFIDENCE_THRESHOLD` | `0.8` | OpenCV match sensitivity (0.0–1.0) |

---

## 🧪 Testing Each Module

Test ADB connection alone:
```powershell
python bot/adb.py
```

Test image detection alone:
```powershell
python bot/screen.py
```

Run full bot:
```powershell
python main.py
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ADB not found` | Update `ADB_PATH` in config.py |
| `Emulator NOT found` | Run `adb connect 127.0.0.1:5555` first |
| `Image not found` | Lower `CONFIDENCE_THRESHOLD` to `0.7` |
| Bot clicks wrong place | Re-capture the template image (tighter crop) |
| Bot too fast | Increase `ATTACK_POPUP_WAIT` in config.py |

---

## 📚 What You Learned

- **ADB** — Android Debug Bridge for emulator control
- **OpenCV Template Matching** — finding images within images
- **State Machines** — structuring bot decision logic
- **Python Modules** — organizing code into files
- **Logging** — recording bot activity

---

> ⚠️ **Note**: This is an educational project. Using bots in live games may violate the game's Terms of Service.
