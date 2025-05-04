import cv2
import mediapipe as mp
import pyautogui
import time

# Setup
cap = cv2.VideoCapture(1)
cap.set(3, 320)  # Very low width
cap.set(4, 180)  # Very low height

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, max_num_hands=1)

pyautogui.FAILSAFE = False

gesture_hold = {"label": None, "start_time": 0}
HOLD_DURATION = 0.01
last_cast_time = {}
cooldown_sec = 0

held_keys = {"w": False, "a": False, "q": False, "s": False, "d": False, "z": False}
spell_keys = {"1": False, "2": False, "3": False, "4": False}

swipe_cooldown = 1
last_swipe_time = 0
last_fist_time = 0

def is_finger_up(lm, tip, pip):
    return lm[pip].y - lm[tip].y > 0.015

def get_finger_states(lm):
    return {
        "thumb": lm[4].x > lm[3].x,
        "index": is_finger_up(lm, 8, 6),
        "middle": is_finger_up(lm, 12, 10),
        "ring": is_finger_up(lm, 16, 14),
        "pinky": is_finger_up(lm, 20, 18)
    }

def cast_spell(key, label):
    now = time.time()
    if key not in last_cast_time or (now - last_cast_time[key]) > cooldown_sec:
        pyautogui.press(key)
        last_cast_time[key] = now

def hold_key(key):
    if not held_keys[key]:
        pyautogui.keyDown(key)
        held_keys[key] = True

def release_key(key):
    if held_keys[key]:
        pyautogui.keyUp(key)
        held_keys[key] = False

def detect_hand(states, lm):
    global last_swipe_time, last_fist_time

    now = time.time()
    swipe_active = False
    for k in spell_keys: spell_keys[k] = False

    # Fist = release all keys
    curled = sum(1 for up in states.values() if not up)
    if curled >= 4 and now - last_fist_time > swipe_cooldown:
        last_fist_time = now
        for key in held_keys:
            pyautogui.keyUp(key)
            held_keys[key] = False
        gesture_hold["label"] = None
        return

    combo = frozenset(k for k, v in states.items() if v)

    # Swipe Up/Down with open palm
    if combo == frozenset(["thumb", "index", "middle", "ring", "pinky"]):
        current_y = lm[9].y
        if hasattr(detect_hand, "prev_y") and detect_hand.prev_y is not None:
            dy = current_y - detect_hand.prev_y
            if dy > 0.05 and now - last_swipe_time > swipe_cooldown:
                pyautogui.press("space")  # Jump
                last_swipe_time = now
                swipe_active = True
            elif dy < -0.05 and now - last_swipe_time > swipe_cooldown:
                pyautogui.press("ctrl")  # Roll
                last_swipe_time = now
                swipe_active = True
        detect_hand.prev_y = current_y

        if not swipe_active:
            hold_key("w")
        else:
            release_key("w")
    else:
        detect_hand.prev_y = None
        release_key("w")

    if swipe_active:
        return

    # Thumb + Index = hold Z
    if combo == frozenset(["thumb", "index"]):
        hold_key("z")
    else:
        release_key("z")

    # Thumb + Index + Middle = hold Q
    if combo == frozenset(["thumb", "index", "middle"]):
        hold_key("q")
    else:
        release_key("q")

    # Middle + Ring only = hold S
    if combo == frozenset(["middle", "ring"]):
        hold_key("s")
    else:
        release_key("s")

    # Only pinky = hold A
    if combo == frozenset(["pinky"]):
        hold_key("a")
    else:
        release_key("a")

    # Only thumb = hold D
    if combo == frozenset(["thumb"]):
        hold_key("d")
    else:
        release_key("d")

    # Spells
    if combo == frozenset(["index"]):
        spell_keys["1"] = True
    elif combo == frozenset(["index", "middle"]):
        spell_keys["2"] = True
    elif combo == frozenset(["index", "middle", "ring"]):
        spell_keys["3"] = True
    elif combo == frozenset(["thumb", "index", "middle", "ring"]):
        spell_keys["4"] = True

# Main loop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    now = time.time()

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark
            states = get_finger_states(lm)
            detect_hand(states, lm)

    for key, active in spell_keys.items():
        if active:
            if gesture_hold["label"] != key:
                gesture_hold["label"] = key
                gesture_hold["start_time"] = now
            elif now - gesture_hold["start_time"] >= HOLD_DURATION:
                cast_spell(key, f"Spell {key}")
                gesture_hold["label"] = None
        else:
            if gesture_hold["label"] == key:
                gesture_hold["label"] = None

    cv2.imshow("Spellcaster", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
