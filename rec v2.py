import tkinter as tk
import time
import threading
from pynput import mouse
from pynput.mouse import Controller
import ast  
from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import GlobalHotKeys
from pynput.mouse import Button

###################################
# GLOBALS
###################################

r = 1
recorded_events = []
recording = False
listener = None
speed = 1
stop_playback = False
hotkey_listener = None


###################################
# ASSIGN LOOP VALUE
###################################

def lopz():
    global r
    try:
        val = int(looper.get())
        if val <= 0:
            raise ValueError
        r = val
        loop_status.config(text=f"Assigned value: {val}")
    except ValueError:
        loop_status.config(text="Enter a valid number (> 0)")

###################################
# SHORTCUT HANDLERS
###################################

def shortcut_start_recording(event=None):
    start_recording()

def shortcut_stop_recording(event=None):
    stop_recording()

def shortcut_play_recording():
    play_recording()

def shortcut_stop_playback(event=None):
    global stop_playback
    stop_playback = True
    status_label.config(text="Playback stopped.")

###################################
# RECORDING CALLBACKS
###################################

def on_move(x, y):
    if recording:
        recorded_events.append({
            'type': 'move',
            'x': x,
            'y': y,
            'time': time.time()
        })

def on_click(x, y, button, pressed):
    if recording:
        recorded_events.append({
            'type': 'click',
            'button': str(button),
            'pressed': pressed,
            'x': x,
            'y': y,
            'time': time.time()
        })

def on_scroll(x, y, dx, dy):
    if recording:
        recorded_events.append({
            'type': 'scroll',
            'dx': dx,
            'dy': dy,
            'time': time.time()
        })
###################################
# KEYBOARD CALLBACKS
###################################

def on_key_press(key):
    if recording:
        recorded_events.append({
            'type': 'key_press',
            'key': str(key),
            'time': time.time()
        })

def on_key_release(key):
    if recording:
        recorded_events.append({
            'type': 'key_release',
            'key': str(key),
            'time': time.time()
        })

def stop_playback_global():
    global stop_playback
    stop_playback = True
    root.after(0, lambda: status_label.config(text="Playback stopped (Global)."))

def start_global_hotkeys():
    global hotkey_listener

    hotkey_listener = GlobalHotKeys({
        "<f6>": shortcut_start_recording,
        "<f7>": shortcut_stop_recording,
        "<f8>": shortcut_play_recording,
    })

    hotkey_listener.start()



###################################
# RECORD CONTROL
###################################

def start_recording():
    global recording, listener

    if recording:
        return

    if listener:
        listener.stop()
        listener = None

    recorded_events.clear()
    recording = True

    listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll)

    keyboard_listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release)

    listener.start()
    keyboard_listener.start()

    globals()['keyboard_listener'] = keyboard_listener

    status_label.config(text="Recording...")

def stop_recording():
    global recording, listener

    if not recording:
        return

    recording = False

    if 'keyboard_listener' in globals():
        keyboard_listener.stop()

    if listener:
        listener.stop()
        listener = None

    status_label.config(text="Recording stopped.")
hotkey_listener = None

def set_shortcut():
    global hotkey_listener

    user_input = shortcut_entry.get().lower().strip()

    if not user_input:
        shortcut_label.config(text="Enter a valid shortcut!")
        return

    try:
        # stop old listener
        if hotkey_listener:
            hotkey_listener.stop()

        def stop_playback_global():
            global stop_playback
            stop_playback = True
            root.after(0, lambda: status_label.config(
                text=f"Stopped by {user_input.upper()}"))

        # convert format (ctrl+2 → <ctrl>+2)
        keys = user_input.split('+')
        formatted = '+'.join([f"<{k}>" if k in ['ctrl','shift','alt'] else k for k in keys])

        from pynput.keyboard import GlobalHotKeys
        hotkey_listener = GlobalHotKeys({
            formatted: stop_playback_global
        })

        hotkey_listener.start()

        shortcut_label.config(text=f"Assigned: {user_input.upper()}")

    except:
        shortcut_label.config(text="Invalid shortcut format!")

###################################
# PLAYBACK
###################################

def play_recording():
    global speed, r

    if not recorded_events:
        status_label.config(text="No events recorded.")
        return

    try:
        sp = float(speed)
        if sp <= 0:
            raise ValueError
    except:
        speedlabel.config(text="Enter a valid number!")
        return

    def run():
        global stop_playback
        stop_playback = False

        mouse_controller = Controller()
        keyboard_controller = KeyboardController()

        root.after(0, lambda: status_label.config(text="Playing..."))

        # initialize play loop display
        try:
            root.after(0, lambda: play_loop_var.set("0"))
        except Exception:
            pass

        for i in range(r):
            if stop_playback:
                break

            # update UI to show current loop number (1-based)
            try:
                root.after(0, lambda v=str(i+1): play_loop_var.set(v))
            except Exception:
                pass

            prev_time = recorded_events[0]['time']

            for event in recorded_events:
                if stop_playback:
                    break

                delay = max(0.0, (event['time'] - prev_time) / sp)
                time.sleep(delay)
                prev_time = event['time']

                try:
                    if event['type'] == 'move':
                        mouse_controller.position = (event['x'], event['y'])

                    elif event['type'] == 'click':
                        button_str = event['button']

                        # Convert string to actual button
                        if 'left' in button_str:
                            btn = Button.left
                        elif 'right' in button_str:
                            btn = Button.right
                        elif 'middle' in button_str:
                            btn = Button.middle

                        # Perform action
                        if event['pressed']:
                            mouse_controller.press(btn)
                        else:
                            mouse_controller.release(btn)

                    elif event['type'] == 'scroll':
                        mouse_controller.scroll(
                            event.get('dx', 0),
                            event.get('dy', 0)
                        )

                    elif event['type'] == 'key_press':
                        key = event['key']
                        try:
                            if "Key." in key:
                                key = key.replace("Key.", "")
                                keyboard_controller.press(getattr(keyboard.Key, key))
                            else:
                                keyboard_controller.press(key.strip("'"))
                        except:
                            pass

                    elif event['type'] == 'key_release':
                        key = event['key']
                        try:
                            if "Key." in key:
                                key = key.replace("Key.", "")
                                keyboard_controller.release(getattr(keyboard.Key, key))
                            else:
                                keyboard_controller.release(key.strip("'"))
                        except:
                            pass

                except:
                    pass

        # reset play loop display after finishing
        try:
            root.after(0, lambda: play_loop_var.set("0"))
        except Exception:
            pass

        if stop_playback:
            root.after(0, lambda: status_label.config(text="Playback stopped."))
        else:
            root.after(0, lambda: status_label.config(text="Playback complete."))

    threading.Thread(target=run, daemon=True).start()

###################################
# GUI
###################################

root = tk.Tk()
root.title("Mouse Recorder & Player")
try:
    root.iconbitmap("topico.ico")
except:
    pass
root.configure(bg="#0f0f0f")

FINAL_W, FINAL_H = 475, 550
START_W, START_H = 60, 40



root.update_idletasks()
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
cx = sw // 2
cy = sh // 2

root.geometry(f"{START_W}x{START_H}+{cx}+{cy}")
root.attributes("-alpha", 0.0)
root.resizable(False, False)

def smooth_open(w=START_W, h=START_H, alpha=0.0):
    w += max(1, (FINAL_W - w) // 6)
    h += max(1, (FINAL_H - h) // 6)
    alpha += (1.0 - alpha) * 0.15

    x = cx - w // 2
    y = cy - h // 2

    root.geometry(f"{w}x{h}+{x}+{y}")
    root.attributes("-alpha", alpha)

    if w < FINAL_W or h < FINAL_H or alpha < 0.99:
        root.after(15, smooth_open, w, h, alpha)
    else:
        root.geometry(f"{FINAL_W}x{FINAL_H}+{cx - FINAL_W//2}+{cy - FINAL_H//2}")
        root.attributes("-alpha", 1.0)

smooth_open()

###################################
# SHORTCUTS
###################################
##
##root.bind_all("<F6>", shortcut_start_recording)
##
##root.bind_all("<F7>", shortcut_stop_recording)
##
##root.bind_all("<F8>", lambda event: play_recording())


###################################
# UI HELPERS
###################################

BG = "#0f0f0f"
FG = "#eaeaea"
BTN_BG = "#1c1c1c"
BTN_HOVER = "#2a2a2a"
ENTRY_BG = "#181818"
ACCENT = "#4da6ff"

FONT = ("Segoe UI", 10)
FONT_BTN = ("Segoe UI Semibold", 10)
FONT_TITLE = ("Segoe UI Semibold", 12)

def make_label(txt):
    return tk.Label(root, text=txt, bg=BG, fg=FG, font=FONT)

def make_title(txt):
    return tk.Label(root, text=txt, bg=BG, fg=ACCENT, font=FONT_TITLE)

def make_entry():
    return tk.Entry(root, bg=ENTRY_BG, fg=FG,
                    insertbackground=FG, relief="flat",
                    font=FONT, width=22)

def make_button(parent, txt, cmd):
    b = tk.Button(parent, text=txt, command=cmd,
                  bg=BTN_BG, fg=FG, font=FONT_BTN,
                  relief="flat", padx=12, pady=6)
    b.bind("<Enter>", lambda e: b.config(bg=BTN_HOVER))
    b.bind("<Leave>", lambda e: b.config(bg=BTN_BG))
    return b

def speeder():
    global speed
    try:
        get = int(speedentry.get())
        if get <= 0:
            raise ValueError
        speed = get
        speedlabel.config(text="Assigned speed: " + str(get))
    except:
        speedlabel.config(text="Enter a valid value")

def saver():
    name = str(saveentry.get())
    try:
        with open(name + ".mrp", "w") as f:
            for event in recorded_events:
                f.write(str(event) + "\n")
        savelabel.config(text=f"Recording saved as {name}.mrp")
    except:
        savelabel.config(text="Error saving file.")

def loader():
    global recorded_events
    name = str(loadentry.get())
    try:
        with open(name + ".mrp", "r") as f:
            recorded_events.clear()
            for line in f:
                recorded_events.append(ast.literal_eval(line.strip()))
        status_label.config(text=f"Loaded recording from {name}")
    except:
        status_label.config(text="Error loading file.")


###################################
# LAYOUT
###################################

make_title("Mouse Recorder & Player").pack(pady=10)

make_label("Loop count").pack()
looper = make_entry()
looper.pack(pady=4)
# readonly box to the right of the loop counter that shows the current
# number of loops being played (keeps layout unchanged)
play_loop_var = tk.StringVar(value="0")
play_loop_entry = tk.Entry(root, textvariable=play_loop_var,
                           state='readonly', justify='center', width=8,
                           bg=ENTRY_BG, fg=FG, readonlybackground=ENTRY_BG,
                           relief='flat', font=FONT)
play_loop_entry.pack(pady=4)
make_button(root, "Assign Loop", lopz).pack()

loop_status = make_label("No loop value assigned yet")
loop_status.pack(pady=6)

control_frame = tk.Frame(root, bg=BG)
control_frame.pack(pady=10)

make_button(control_frame, "● Record (F6)", start_recording).grid(row=0, column=0, padx=6)
make_button(control_frame, "■ Stop (F7)", stop_recording).grid(row=0, column=1, padx=6)
make_button(control_frame, "▶ Play (F8)", play_recording).grid(row=0, column=2, padx=6)

status_label = make_label("Ready.")
status_label.pack(pady=10)

# ================= ENTRY ROW =================
entry_row = tk.Frame(root, bg=BG)
entry_row.pack(pady=10)

# SPEED
speed_col = tk.Frame(entry_row, bg=BG)
speed_col.pack(side="left", padx=20)

speedentry = tk.Entry(speed_col, insertbackground="white",
                      bg="#1c1c1c", fg="#eaeaea",
                      relief="flat", width=18)
speedentry.pack()

tk.Button(speed_col, text="Assign",
          command=speeder,
          width=8, bg="#1c1c1c",
          fg="#eaeaea", relief="flat").pack(pady=3)

speedlabel = tk.Label(speed_col, text="Assigned speed: 1", bg=BG, fg=FG)
speedlabel.pack(pady=4)

# SAVE
save_col = tk.Frame(entry_row, bg=BG)
save_col.pack(side="left", padx=20)

saveentry = tk.Entry(save_col,
                     insertbackground="white",
                     bg="#1c1c1c",
                     fg="#eaeaea",
                     relief="flat",
                     width=18)
saveentry.pack()

tk.Button(save_col,
          text="Save",
          command=saver,
          width=10,
          bg="#1c1c1c",
          fg="#eaeaea",
          relief="flat").pack(pady=3)

savelabel = tk.Label(save_col,
                     text="Enter name to save",
                     bg=BG,
                     fg=FG)
savelabel.pack(pady=4)

# LOAD
load_col = tk.Frame(entry_row, bg=BG)
load_col.pack(side="left", padx=20)

loadentry = tk.Entry(load_col,
                     insertbackground="white",
                     bg="#1c1c1c",
                     fg="#eaeaea",
                     relief="flat",
                     width=18)
loadentry.pack()

tk.Button(load_col,
          text="Load",
          command=loader,
          width=10,
          bg="#1c1c1c",
          fg="#eaeaea",
          relief="flat").pack(pady=3)

loadlabel = tk.Label(load_col,
                     text="Enter file name to load",
                     bg=BG,
                     fg=FG)
loadlabel.pack(pady=4)

# SHORTCUT 

shortcut_row = tk.Frame(root, bg=BG)
shortcut_row.pack(pady=10)

tk.Button(shortcut_row, text="Set Shortcut",
          command=set_shortcut,
          width=15, bg="#1c1c1c",
          fg="#eaeaea", relief="flat").pack(pady=5)

shortcut_col = tk.Frame(shortcut_row, bg=BG)
shortcut_col.pack()

shortcut_entry = tk.Entry(shortcut_col, insertbackground="white",
                          bg="#1c1c1c", fg="#eaeaea",
                          relief="flat", width=20)
shortcut_entry.pack()

shortcut_label = tk.Label(shortcut_col,
                          text="Enter stop shortcut (e.g. ctrl+2) while playback",
                          bg=BG, fg=FG)
shortcut_label.pack(pady=4)

start_global_hotkeys()


root.mainloop()
