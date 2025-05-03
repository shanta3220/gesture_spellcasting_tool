# 🪄 Gesture Spellcasting Tool for Hogwarts Legacy

Cast spells in Hogwarts Legacy using real hand gestures detected from your webcam! This external tool lets you bind gestures like circles or open palms to spell keys (e.g., Fireball on `1`, Shield on `2`), adding a magical layer of control.

---

## 🧰 Requirements

- Python **3.10.x**
- Webcam (built-in or external)
- Windows PC with Hogwarts Legacy installed
- Game keybinds set to number keys (e.g., 1, 2, 3)

---

## 🧪 Python Dependencies

Install the following Python libraries inside your virtual environment:

```bash
pip install mediapipe opencv-python pyautogui
```

🛠️ Local Setup

1. Install Python 3.10 (if not already)

Download it from:
https://www.python.org/downloads/release/python-31011/

2. Create a Virtual Environment

# In Git Bash (adjust path if needed):

`"/c/Users/yourname/AppData/Local/Programs/Python/Python310/python.exe" -m venv venv310 `

# Activate it

`source venv310/Scripts/activate`

3. Install Dependencies
   `pip install mediapipe opencv-python pyautogui`

4. ▶️ Run the App

`python spellcaster.py`

Your webcam will activate. Perform gestures (e.g., draw a circle) to trigger key presses in-game. Make sure Hogwarts Legacy is in focus!
