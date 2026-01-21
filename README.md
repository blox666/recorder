from multiprocessing import Value
import tkinter as tk
import time
import threading
from pynput import mouse
from pynput.mouse import Controller
import ast

###################################
# GLOBALS
###################################

r = 1
recorded_events = []
recording = False
listener = None
speed = 1

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
            'x': x,
            'y': y,
            'button': str(button),
            'pressed': pressed,
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
        on_scroll=on_scroll
    )
    listener.start()

    status_label.config(text="Recording...")

def stop_recording():
    global recording, listener

    if not recording:
        return

    recording = False

    if listener:
        listener.stop()
        listener = None

    status_label.config(text="Recording stopped.")

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
        mouse_controller = Controller()
        root.after(0, lambda: status_label.config(text="Playing..."))

        for _ in range(r):
            prev_time = recorded_events[0]['time']

            for event in recorded_events:
                delay = max(0.0, (event['time'] - prev_time) / sp)
                time.sleep(delay)
                prev_time = event['time']

                try:
                    if event['type'] == 'move':
                        mouse_controller.position = (event['x'], event['y'])

                    elif event['type'] == 'click':
                        if "left" in event['button']:
                            btn = mouse.Button.left
                        else:
                            btn = mouse.Button.right

                        if event['pressed']:
                            mouse_controller.press(btn)
                        else:
                            mouse_controller.release(btn)

                    elif event['type'] == 'scroll':
                        mouse_controller.scroll(
                            event.get('dx', 0),
                            event.get('dy', 0)
                        )
                except:
                    pass

        root.after(0, lambda: status_label.config(text="Playback complete."))

    threading.Thread(target=run, daemon=True).start()

###################################
# GUI
###################################

root = tk.Tk()
root.title("Mouse Recorder & Player")
root.iconbitmap("topico.ico")
root.configure(bg="#0f0f0f")

FINAL_W, FINAL_H = 475, 520
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

root.bind("<F6>", shortcut_start_recording)
root.bind("<F7>", shortcut_stop_recording)

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
make_button(root, "Assign Loop", lopz).pack()

loop_status = make_label("No loop value assigned yet")
loop_status.pack(pady=6)

control_frame = tk.Frame(root, bg=BG)
control_frame.pack(pady=10)

make_button(control_frame, "● Record (F6)", start_recording).grid(row=0, column=0, padx=6)
make_button(control_frame, "■ Stop (F7)", stop_recording).grid(row=0, column=1, padx=6)
make_button(control_frame, "▶ Play", play_recording).grid(row=0, column=2, padx=6)

status_label = make_label("Ready.")
status_label.pack(pady=10)

entry_row = tk.Frame(root, bg=BG)
entry_row.pack(pady=10)

speed_col = tk.Frame(entry_row, bg=BG)
speed_col.pack(side="left", padx=20)

speedentry = tk.Entry(speed_col, insertbackground="white", bg="#1c1c1c", fg="#eaeaea", relief="flat", width=18)
speedentry.pack()

speedlabel = tk.Label(speed_col, text="Assigned speed: 1", bg=BG, fg=FG)
speedlabel.pack(pady=4)

save_col = tk.Frame(entry_row, bg=BG)
save_col.pack(side="left", padx=20)

saveentry = tk.Entry(save_col, insertbackground="white", bg="#1c1c1c", fg="#eaeaea", relief="flat", width=18)
saveentry.pack()

savelabel = tk.Label(save_col, text="Enter name to save", bg=BG, fg=FG)
savelabel.pack(pady=4)

button_row = tk.Frame(root, bg=BG)
button_row.pack(pady=2)

tk.Button(button_row, text="Assign", command=speeder, width=15, bg="#1c1c1c", fg="#eaeaea", relief="flat").pack(side="left", padx=20)
tk.Button(button_row, text="Save", command=saver, width=15, bg="#1c1c1c", fg="#eaeaea", relief="flat").pack(side="left", padx=20)
tk.Button(button_row, text="Load", command=loader, width=15, bg="#1c1c1c", fg="#eaeaea", relief="flat").pack(side="left", padx=20)

load_col = tk.Frame(entry_row, bg=BG)
load_col.pack(side="left", padx=20)

loadentry = tk.Entry(load_col, insertbackground="white", bg="#1c1c1c", fg="#eaeaea", relief="flat", width=18)
loadentry.pack()

loadlabel = tk.Label(load_col, text="Enter file name to load", bg=BG, fg=FG)
loadlabel.pack(pady=4)

root.mainloop()
