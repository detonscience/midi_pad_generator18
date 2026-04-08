import random
import tkinter as tk
from tkinter import ttk, filedialog, font as tkfont
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
from PIL import Image, ImageTk
import os
import tempfile
import subprocess

# --------------------------
# NOTE SYSTEM
# --------------------------
NOTE_MAP = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
NOTE_NAMES = list(NOTE_MAP.keys())

def get_note_name(n):
    return NOTE_NAMES[n % 12]

def chord_name(chord):
    root = get_note_name(chord[0])
    return root + " chord"

MODES = {
    "ionian": [0,2,4,5,7,9,11],
    "dorian": [0,2,3,5,7,9,10],
    "phrygian": [0,1,3,5,7,8,10],
    "lydian": [0,2,4,6,7,9,11],
    "mixolydian": [0,2,4,5,7,9,10],
    "aeolian": [0,2,3,5,7,8,10],
    "locrian": [0,1,3,5,6,8,10],
    "harmonic_minor": [0,2,3,5,7,8,11],
    "melodic_minor": [0,2,3,5,7,9,11],
    "phrygian_dominant": [0,1,4,5,7,8,10],
    "double_harmonic": [0,1,4,5,7,8,11],
    "whole_tone": [0,2,4,6,8,10],
    "major_pentatonic": [0,2,4,7,9],
    "minor_pentatonic": [0,3,5,7,10],
    "enigmatic": [0,1,4,6,8,10,11],
}

PROGRESSIONS = {
    "standard": [[0, 5, 6, 4], [0, 3, 4, 6]],
    "ambient": [[0, 2, 5, 3], [0, 4, 2, 6]],
    "weird": [[0, 1, 6, 3], [2, 6, 1, 5]],

    "dark": [
        [0, 6, 5, 4],
        [0, 3, 6, 2],
        [0, 5, 3, 2],
    ],

    "dystopian": [
        [0, 1, 6, 2],
        [0, 6, 1, 5],
        [2, 1, 6, 0],
    ],

    "jazz": [
        [0, 2, 5, 1],
        [0, 4, 1, 5],
        [2, 5, 1, 4],
    ],

    "emotional": [
        [0, 4, 5, 3],
        [0, 3, 5, 4],
        [0, 5, 4, 3],
    ],

    "uplifting": [
        [0, 4, 5, 6],
        [0, 3, 4, 5],
        [0, 5, 6, 4],
    ],

    "sad": [
        [0, 3, 4, 3],
        [0, 5, 3, 4],
        [0, 2, 3, 1],
    ],

    "introspective": [
        [0, 3, 2, 3],
        [0, 5, 2, 4],
        [0, 2, 4, 3],
    ],

    "spacey": [
        [0, 2, 1, 5],
        [0, 6, 2, 5],
        [0, 1, 2, 6],
    ],

    "am/fmhead": [
        [0, 5, 2, 6],
        [0, 3, 5, 4],
        [0, 1, 5, 2],
        [0, 3, 2, 6],
    ],

    "boards_of_canada": [
        [0, 2, 4, 2],
        [0, 3, 5, 3],
        [0, 2, 5, 4],
    ],

    "autechre": [
        [0, 1, 5, 2],
        [0, 6, 2, 1],
        [0, 3, 1, 6],
    ],

    "bjork": [
        [0, 4, 1, 5],
        [0, 3, 6, 2],
        [0, 5, 1, 4],
    ],

    "alan_parsons_nucleus": [
        [0, 4, 2, 5],
        [0, 5, 3, 6],
        [0, 2, 4, 1],
    ],

    "gas": [
        [0, 5, 4, 5],
        [0, 5, 3, 5],
        [0, 4, 5, 4],
    ],

    "ross_154": [
        [0, 5, 3, 5],
        [0, 6, 5, 3],
        [0, 3, 5, 6],
    ],
}

# --------------------------
# CORE
# --------------------------
def build_scale(root, mode, octave):
    base = NOTE_MAP[root] + octave * 12
    return [base + i for i in MODES[mode]]

def get_scale_names(root, mode, octave):
    scale = build_scale(root, mode, octave)
    return " ".join(get_note_name(n) for n in scale)

def build_chord(scale, degree):
    needed = max(8, len(scale) * 3)
    s = []
    octave_shift = 0

    while len(s) < needed:
        for note in scale:
            s.append(note + octave_shift)
        octave_shift += 12

    degree = degree % len(scale)
    return [s[degree], s[degree+2], s[degree+4], s[degree+6]]

# --------------------------
# RADIOHEAD CHORD HELPERS
# --------------------------
def minor7(root):
    return [root, root+3, root+7, root+10]

def major7(root):
    return [root, root+4, root+7, root+11]


def is_minor_mode(mode_name):
    return mode_name in {
        "dorian", "phrygian", "aeolian", "locrian",
        "harmonic_minor", "melodic_minor", "minor_pentatonic"
    }


def normalize_chord(chord):
    return sorted(dict.fromkeys(chord))


def apply_chord_extensions(chord):
    chord = normalize_chord(chord)
    if not chord:
        return chord

    root = chord[0]

    if sus2_var.get() and len(chord) >= 2:
        chord[1] = root + 2
    elif sus4_var.get() and len(chord) >= 2:
        chord[1] = root + 5

    if omit3_var.get() and len(chord) >= 2:
        del chord[1]

    if omit5_var.get() and len(chord) >= 3:
        del chord[2]

    if add7_var.get():
        chord.append(root + (10 if is_minor_mode(mode_var.get()) else 11))

    if add9_var.get():
        chord.append(root + 14)

    return normalize_chord(chord)


def apply_voicing(chord):
    chord = normalize_chord(chord)
    if len(chord) < 2:
        return chord

    voicing = voicing_mode_var.get()
    voiced = chord[:]

    if voicing == "open":
        for i in range(1, len(voiced), 2):
            voiced[i] += 12
    elif voicing == "wide":
        for i in range(1, len(voiced)):
            voiced[i] += 12 if i < 3 else 24
    elif voicing == "high":
        for i in range(1, len(voiced)):
            voiced[i] += 12
    elif voicing == "low_cluster":
        for i in range(2, len(voiced)):
            voiced[i] -= 12

    return sorted(voiced)

def voice_lead_chord(chord, prev):
    if not prev:
        return sorted(chord)

    led = []
    for i, note in enumerate(chord):
        target = prev[i % len(prev)]
        candidates = [note - 24, note - 12, note, note + 12, note + 24]
        best = min(candidates, key=lambda x: abs(x - target))
        led.append(best)

    return sorted(led)

def build_special_chord(degree, prog_name, base, scale):
    if prog_name == "am/fmhead":
        if degree == 1:
            root = base + 1
            chord = major7(root)
        elif degree == 3:
            root = base + 5
            chord = minor7(root)
        else:
            chord = build_chord(scale, degree)

        if random.random() > 0.6:
            chord = [
                chord[0],
                chord[0] + random.choice([2, 5]),
                chord[2],
                chord[3]
            ]

        if random.random() > 0.7:
            chord.append(chord[0] + 1)

        return chord

    return build_chord(scale, degree)

def choose_progression_blocks(style_name, blocks, flow):
    patterns = PROGRESSIONS[style_name]

    if flow == "single":
        chosen = [random.choice(patterns)]
    elif flow == "sequence":
        start = random.randint(0, len(patterns) - 1)
        chosen = [patterns[(start + i) % len(patterns)] for i in range(blocks)]
    elif flow == "random":
        chosen = [random.choice(patterns) for _ in range(blocks)]
    else:
        idx = random.randint(0, len(patterns) - 1)
        chosen = []
        for _ in range(blocks):
            chosen.append(patterns[idx])
            move = random.choice(["stay", "next", "jump"])
            if move == "next":
                idx = (idx + 1) % len(patterns)
            elif move == "jump":
                idx = random.randint(0, len(patterns) - 1)

    return chosen

def generate_progression():
    chords = []

    root_name = root_var.get()
    octave = int(octave_var.get())
    mode = mode_var.get()
    prog_name = prog_var.get()
    blocks = int(progression_blocks_var.get())
    flow = progression_flow_var.get()

    base = NOTE_MAP[root_name] + octave * 12
    scale = build_scale(root_name, mode, octave)

    chosen_patterns = choose_progression_blocks(prog_name, blocks, flow)

    for pattern in chosen_patterns:
        for d in pattern:
            chord = build_special_chord(d, prog_name, base, scale)
            chord = apply_chord_extensions(chord)
            chord = voice_lead_chord(chord, chords[-1] if chords else None)
            chord = apply_voicing(chord)
            chords.append(chord)

    return chords

def draw_visual(prog):
    canvas.delete("all")

    if not prog:
        return

    length = float(length_var.get())
    overlap = overlap_var.get()
    velocity = velocity_var.get()

    ticks = 480
    base = int(ticks * 4 * length)

    if pad_mode_var.get():
        total_steps = len(prog)
    else:
        total_steps = len(prog) * int(bars_var.get())

    total_ticks = max(base * total_steps, 1)
    canvas_width = int(canvas.cget("width"))
    canvas_height = int(canvas.cget("height"))
    pixels_per_tick = canvas_width / total_ticks

    time_cursor = 0
    chord_sequence = prog if pad_mode_var.get() else prog * int(bars_var.get())

    for chord in chord_sequence:
        durations = []

        for note in chord:
            if random_length_var.get():
                duration = int(base * random.uniform(0.3, 1.2))
            else:
                duration = base

            if independent_notes_var.get():
                offset = random.randint(0, int(ticks * 0.25))
            else:
                offset = 0

            x = int((time_cursor + offset) * pixels_per_tick)
            width = max(int(duration * pixels_per_tick), 2)
            y = canvas_height - (note * 2 % canvas_height)

            ratio = velocity / 127
            r = int(110 + (ratio * 70))
            g = int(140 + (ratio * 60))
            b = int(170 + (ratio * 55))
            color = f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"

            canvas.create_rectangle(x, y, x + width, y + 4, fill=color, outline="")
            durations.append(duration)

        release = int(max(durations) * (1 - overlap))
        time_cursor += max(release, 1)

# --------------------------
# GUI
# --------------------------
def generate():
    prog = generate_progression()
    state["prog"] = prog
    state["locks"] = [False] * len(prog)
    update_chord_selector()
    refresh_lock_button()
    draw_visual(prog)
    display_progression()


def display_progression():
    prog = state.get("prog", [])
    locks = state.get("locks", [False] * len(prog))
    selected_idx = get_selected_chord_index()

    chord_output.configure(state="normal")
    chord_output.delete("1.0", tk.END)

    for i, chord in enumerate(prog):
        marker = "> " if i == selected_idx else "  "
        lock_mark = "[L] " if i < len(locks) and locks[i] else ""
        chord_output.insert(tk.END, f"{marker}{i+1}. {lock_mark}{chord_name(chord)}\n")

    chord_output.configure(state="disabled")


def get_selected_chord_index():
    prog = state.get("prog", [])
    if not prog:
        return 0

    try:
        idx = int(selected_chord_var.get()) - 1
    except (TypeError, ValueError):
        idx = 0

    return max(0, min(idx, len(prog) - 1))


def update_chord_selector(*args):
    prog = state.get("prog", [])
    values = [str(i) for i in range(1, len(prog) + 1)]

    if values:
        selected_chord_var.set(selected_chord_var.get() if selected_chord_var.get() in values else values[0])
    else:
        selected_chord_var.set("")

    if "chord_selector" in globals():
        chord_selector.configure(values=values)
        chord_selector.configure(state="readonly" if values else "disabled")


def refresh_lock_button(*args):
    if "lock_button" not in globals():
        return

    prog = state.get("prog", [])
    locks = state.get("locks", [False] * len(prog))

    if not prog:
        lock_button.configure(text="◎ Lock")
        return

    idx = get_selected_chord_index()
    lock_button.configure(text="◉ Unlock" if idx < len(locks) and locks[idx] else "◎ Lock")


def toggle_selected_lock():
    prog = state.get("prog", [])
    if not prog:
        return

    locks = state.setdefault("locks", [False] * len(prog))
    idx = get_selected_chord_index()
    locks[idx] = not locks[idx]
    refresh_lock_button()
    display_progression()


def unlock_all_chords():
    prog = state.get("prog", [])
    if not prog:
        return

    state["locks"] = [False] * len(prog)
    refresh_lock_button()
    display_progression()


def regenerate_unlocked_chords():
    old_prog = state.get("prog", [])
    if not old_prog:
        return

    locks = state.get("locks", [False] * len(old_prog))
    new_prog = generate_progression()

    if not new_prog:
        return

    if len(new_prog) < len(old_prog):
        repeats = (len(old_prog) // len(new_prog)) + 1
        new_prog = (new_prog * repeats)[:len(old_prog)]
    elif len(new_prog) > len(old_prog):
        new_prog = new_prog[:len(old_prog)]

    merged = []
    for i in range(len(old_prog)):
        merged.append(old_prog[i] if i < len(locks) and locks[i] else new_prog[i])

    state["prog"] = merged
    draw_visual(merged)
    refresh_lock_button()
    display_progression()

def build_filename():
    root = root_var.get()
    mode = mode_var.get()
    prog = prog_var.get()
    length = length_var.get()
    bars = bars_var.get()
    tempo = tempo_var.get()
    blocks = progression_blocks_var.get()
    flow = progression_flow_var.get()

    return f"{root}_{mode}_{prog}_{flow}_{voicing_mode_var.get()}_{blocks}blocks_{length}L_{bars}B_{tempo}BPM.mid"

def export():
    if "prog" not in state:
        return

    default_name = build_filename()

    path = filedialog.asksaveasfilename(
        defaultextension=".mid",
        initialfile=default_name
    )

    if path:
        export_midi(state["prog"], path)

def quick_export():
    if "prog" not in state:
        return

    filename = build_filename()
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, filename)

    export_midi(state["prog"], path)
    subprocess.run(["open", "-R", path])

def reset():
    state.clear()
    canvas.delete("all")
    update_chord_selector()
    refresh_lock_button()
    chord_output.configure(state="normal")
    chord_output.delete("1.0", tk.END)
    chord_output.configure(state="disabled")

def randomize():
    root_var.set(random.choice(NOTE_NAMES))
    mode_var.set(random.choice(list(MODES.keys())))
    prog_var.set(random.choice(list(PROGRESSIONS.keys())))
    octave_var.set(str(random.randint(2, 5)))
    length_var.set(random.choice(["1", "2", "4", "8", "16"]))
    bars_var.set(random.choice(["1", "2", "4", "8", "16"]))
    tempo_var.set(str(random.randint(70, 140)))
    progression_blocks_var.set(random.choice(["1", "2", "3", "4", "5", "6", "8", "12"]))
    progression_flow_var.set(random.choice(["single", "sequence", "random", "evolving"]))
    voicing_mode_var.set(random.choice(["close", "open", "wide", "high", "low_cluster"]))
    add7_var.set(random.choice([True, False]))
    add9_var.set(random.choice([True, False]))
    sus2_var.set(False)
    sus4_var.set(False)
    omit3_var.set(random.choice([True, False]))
    omit5_var.set(random.choice([True, False]))
    overlap_var.set(round(random.uniform(0.0, 0.6), 2))
    velocity_var.set(random.randint(50, 110))

    prog = generate_progression()
    state["prog"] = prog
    state["locks"] = [False] * len(prog)
    update_chord_selector()
    refresh_lock_button()
    draw_visual(prog)
    display_progression()

def update_scale_display(*args):
    scale_label.config(text=get_scale_names(root_var.get(), mode_var.get(), int(octave_var.get())))

# --------------------------
# APP
# --------------------------
app = tk.Tk()
app.configure(bg="#0d0f14")
app.option_add("*TCombobox*Listbox.background", "#1c212c")
app.option_add("*TCombobox*Listbox.foreground", "#e7ebf0")
app.option_add("*TCombobox*Listbox.selectBackground", "#313949")
app.option_add("*TCombobox*Listbox.selectForeground", "#e7ebf0")
app.title("MIDI Chord Generator")

window_width = 560
screen_height = app.winfo_screenheight()
screen_width = app.winfo_screenwidth()
max_window_height = max(screen_height - 120, 700)

x_pos = max((screen_width - window_width) // 2, 0)
y_pos = 40

app.geometry(f"{window_width}x{max_window_height}+{x_pos}+{y_pos}")
app.minsize(window_width, 700)
app.resizable(True, True)
app.columnconfigure(0, weight=1)
app.columnconfigure(1, weight=1)

# Load background image
bg_image_path = "/Users/detonscience/Pictures/IMG_3151(1).jpg"
bg_label = None
try:
    bg_image = Image.open(bg_image_path)
    bg_image = bg_image.resize((window_width, max_window_height))
    bg_image = bg_image.point(lambda p: p * 0.24)
    bg_photo = ImageTk.PhotoImage(bg_image)

    bg_label = tk.Label(app, image=bg_photo, bd=0)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    bg_label.lower()
except Exception as e:
    print("Background image not found or failed to load:", e)

state = {}

# --------------------------
# PANEL HELPER
# --------------------------
def setup_styles():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    bg_main = "#0d0f14"
    bg_panel = "#151922"
    bg_field = "#1c212c"
    fg_main = "#edf2f7"
    fg_muted = "#9aa6b2"
    border = "#313949"
    accent = "#8ecae6"
    accent_soft = "#7bdff2"
    accent_button = "#3a86ff"
    accent_button_active = "#5aa0ff"
    slider_trough = "#243041"
    slider_active = "#90e0ef"
    active = "#273041"

    style.configure(".", background=bg_main, foreground=fg_main)
    style.configure("TFrame", background=bg_panel)
    style.configure("TLabel", background=bg_panel, foreground=fg_main, font=("Helvetica", 10))
    style.configure("Section.TLabel", background=bg_panel, foreground=accent, font=("Helvetica", 9, "bold"))
    style.configure("Value.TLabel", background=bg_panel, foreground=accent_soft, font=("Helvetica", 10, "bold"))

    style.configure(
        "TButton",
        background=accent_button,
        foreground="#f7fbff",
        borderwidth=0,
        focusthickness=0,
        focuscolor=accent_button,
        padding=(10, 7),
        relief="flat"
    )
    style.map(
        "TButton",
        background=[("active", accent_button_active), ("pressed", active)],
        foreground=[("disabled", "#606774")]
    )

    style.configure(
        "TCombobox",
        fieldbackground=bg_field,
        background=bg_field,
        foreground=fg_main,
        bordercolor=border,
        lightcolor=border,
        darkcolor=border,
        arrowcolor=accent,
        padding=6,
        relief="flat"
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", bg_field)],
        background=[("readonly", bg_field)],
        foreground=[("readonly", fg_main)],
        selectbackground=[("readonly", bg_field)],
        selectforeground=[("readonly", fg_main)]
    )

    style.configure(
        "TEntry",
        fieldbackground=bg_field,
        foreground=fg_main,
        bordercolor=border,
        lightcolor=border,
        darkcolor=border,
        padding=6,
        relief="flat"
    )

    style.configure(
        "TCheckbutton",
        background=bg_panel,
        foreground=fg_main,
        font=("Helvetica", 10),
        indicatorcolor=bg_field,
        indicatordiameter=12,
        padding=2
    )
    style.map(
        "TCheckbutton",
        background=[("active", bg_panel)],
        foreground=[("disabled", "#606774")]
    )

    style.configure(
        "Horizontal.TScale",
        background=bg_panel,
        troughcolor=slider_trough,
        bordercolor=bg_panel,
        lightcolor=slider_active,
        darkcolor=slider_active
    )


def create_panel(parent):
    frame = tk.Frame(
        parent,
        bg="#151922",
        bd=0,
        highlightbackground="#3a4457",
        highlightthickness=1
    )
    return frame

setup_styles()

root_var = tk.StringVar(value="C")
mode_var = tk.StringVar(value="aeolian")
prog_var = tk.StringVar(value="ambient")
octave_var = tk.StringVar(value="4")
length_var = tk.StringVar(value="2")
bars_var = tk.StringVar(value="4")
tempo_var = tk.StringVar(value="120")
progression_blocks_var = tk.StringVar(value="4")
progression_flow_var = tk.StringVar(value="evolving")
voicing_mode_var = tk.StringVar(value="close")
selected_chord_var = tk.StringVar(value="1")
add7_var = tk.BooleanVar(value=False)
add9_var = tk.BooleanVar(value=False)
sus2_var = tk.BooleanVar(value=False)
sus4_var = tk.BooleanVar(value=False)
omit3_var = tk.BooleanVar(value=False)
omit5_var = tk.BooleanVar(value=False)
overlap_var = tk.DoubleVar(value=0.3)
velocity_var = tk.IntVar(value=80)
pad_mode_var = tk.BooleanVar(value=False)
random_length_var = tk.BooleanVar(value=False)
independent_notes_var = tk.BooleanVar(value=False)

# --------------------------
# BASS GENERATOR VARS
# --------------------------
bass_enabled_var = tk.BooleanVar(value=False)
bass_style_var = tk.StringVar(value="root")
bass_octave_var = tk.StringVar(value="-1")

root_var.trace_add("write", update_scale_display)
mode_var.trace_add("write", update_scale_display)
selected_chord_var.trace_add("write", lambda *args: (refresh_lock_button(), display_progression()))

 # --------------------------
musical_panel = create_panel(app)
musical_panel.grid(row=0, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
ttk.Label(musical_panel, text="◈  HARMONY", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8,2))

ttk.Label(musical_panel, text="Root").grid(row=1, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(musical_panel, textvariable=root_var, values=NOTE_NAMES, state="readonly").grid(row=1, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(musical_panel, text="Mode").grid(row=2, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(musical_panel, textvariable=mode_var, values=list(MODES.keys()), state="readonly").grid(row=2, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(musical_panel, text="Progression").grid(row=3, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(musical_panel, textvariable=prog_var, values=list(PROGRESSIONS.keys()), state="readonly").grid(row=3, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(musical_panel, text="Prog Blocks").grid(row=4, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(
    musical_panel,
    textvariable=progression_blocks_var,
    values=["1", "2", "3", "4", "5", "6", "8", "12", "16"],
    state="readonly"
).grid(row=4, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(musical_panel, text="Prog Flow").grid(row=5, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(
    musical_panel,
    textvariable=progression_flow_var,
    values=["single", "sequence", "random", "evolving"],
    state="readonly"
).grid(row=5, column=1, padx=6, pady=4, sticky="ew")


ttk.Label(musical_panel, text="Voicing").grid(row=6, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(
    musical_panel,
    textvariable=voicing_mode_var,
    values=["close", "open", "wide", "high", "low_cluster"],
    state="readonly"
).grid(row=6, column=1, padx=6, pady=4, sticky="ew")

ttk.Checkbutton(musical_panel, text="Add 7th", variable=add7_var).grid(row=7, column=0, padx=6, pady=2, sticky="w")
ttk.Checkbutton(musical_panel, text="Add 9th", variable=add9_var).grid(row=7, column=1, padx=6, pady=2, sticky="w")
ttk.Checkbutton(musical_panel, text="Sus2", variable=sus2_var).grid(row=8, column=0, padx=6, pady=2, sticky="w")
ttk.Checkbutton(musical_panel, text="Sus4", variable=sus4_var).grid(row=8, column=1, padx=6, pady=2, sticky="w")
ttk.Checkbutton(musical_panel, text="Omit 3rd", variable=omit3_var).grid(row=9, column=0, padx=6, pady=2, sticky="w")
ttk.Checkbutton(musical_panel, text="Omit 5th", variable=omit5_var).grid(row=9, column=1, padx=6, pady=2, sticky="w")

 # --------------------------
timing_panel = create_panel(app)
timing_panel.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
ttk.Label(timing_panel, text="◌  MOTION", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8,2))

ttk.Label(timing_panel, text="Length").grid(row=1, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(timing_panel, textvariable=length_var, values=["1", "2", "4", "8", "16"], state="readonly").grid(row=1, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(timing_panel, text="Bars").grid(row=2, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(timing_panel, textvariable=bars_var, values=["1", "2", "4", "8", "16"], state="readonly").grid(row=2, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(timing_panel, text="Tempo").grid(row=3, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(timing_panel, textvariable=tempo_var, values=[str(i) for i in range(60, 181)], state="readonly").grid(row=3, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(timing_panel, text="Overlap").grid(row=4, column=0, padx=6, pady=4, sticky="ew")
ttk.Scale(
    timing_panel,
    from_=0,
    to=0.9,
    orient="horizontal",
    variable=overlap_var,
    command=lambda v: draw_visual(state.get("prog", []))
).grid(row=4, column=1, padx=6, pady=4, sticky="ew")

 # --------------------------
expression_panel = create_panel(app)
expression_panel.grid(row=2, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
ttk.Label(expression_panel, text="△  SHAPE", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8,2))

ttk.Label(expression_panel, text="Velocity").grid(row=1, column=0, padx=6, pady=4, sticky="ew")

velocity_frame = ttk.Frame(expression_panel)
velocity_frame.grid(row=1, column=1, padx=6, pady=4, sticky="ew")

velocity_scale = ttk.Scale(
    velocity_frame,
    from_=40,
    to=127,
    orient="horizontal",
    variable=velocity_var,
    command=lambda v: update_velocity_display(v)
)
velocity_scale.pack(side="left", fill="x", expand=True)

velocity_label = ttk.Label(velocity_frame, text=str(velocity_var.get()), width=4, style="Value.TLabel")
velocity_label.pack(side="right")

ttk.Checkbutton(
    expression_panel,
    text="Pad Mode (Evolving)",
    variable=pad_mode_var,
    command=lambda: draw_visual(state.get("prog", []))
).grid(row=2, column=0, columnspan=2, padx=6, pady=4, sticky="ew")

ttk.Checkbutton(
    expression_panel,
    text="Random Note Length",
    variable=random_length_var,
    command=lambda: draw_visual(state.get("prog", []))
).grid(row=3, column=0, columnspan=2, padx=6, pady=4, sticky="ew")

ttk.Checkbutton(
    expression_panel,
    text="Independent Notes",
    variable=independent_notes_var,
    command=lambda: draw_visual(state.get("prog", []))
).grid(row=4, column=0, columnspan=2, padx=6, pady=4, sticky="ew")

 # --------------------------
bass_panel = create_panel(app)
bass_panel.grid(row=3, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
ttk.Label(bass_panel, text="▣  BASS", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8,2))

ttk.Checkbutton(bass_panel, text="Enable Bass", variable=bass_enabled_var).grid(row=1, column=0, columnspan=2, padx=6, pady=4, sticky="ew")

ttk.Label(bass_panel, text="Style").grid(row=2, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(bass_panel, textvariable=bass_style_var, values=["root", "octave", "dub", "groove"], state="readonly").grid(row=2, column=1, padx=6, pady=4, sticky="ew")

ttk.Label(bass_panel, text="Octave").grid(row=3, column=0, padx=6, pady=4, sticky="ew")
ttk.Combobox(bass_panel, textvariable=bass_octave_var, values=["-2", "-1", "0"], state="readonly").grid(row=3, column=1, padx=6, pady=4, sticky="ew")

 # --------------------------
output_panel = create_panel(app)
output_panel.grid(row=4, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
ttk.Label(output_panel, text="◎  OUTPUT", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8,2))

ttk.Label(output_panel, text="Scale").grid(row=1, column=0, padx=6, pady=4, sticky="ew")
scale_label = ttk.Label(output_panel, text="", style="Value.TLabel")
scale_label.grid(row=1, column=1, padx=6, pady=4, sticky="ew")
update_scale_display()

ttk.Label(output_panel, text="Chord").grid(row=2, column=0, padx=6, pady=4, sticky="ew")
chord_selector = ttk.Combobox(output_panel, textvariable=selected_chord_var, values=["1"], state="disabled")
chord_selector.grid(row=2, column=1, padx=6, pady=4, sticky="ew")

lock_button = ttk.Button(output_panel, text="◎ Lock", command=toggle_selected_lock)
lock_button.grid(row=3, column=0, padx=6, pady=2, sticky="ew")
ttk.Button(output_panel, text="◇ Unlock All", command=unlock_all_chords).grid(row=3, column=1, padx=6, pady=2, sticky="ew")
ttk.Button(output_panel, text="↻ Regen Unlocked", command=regenerate_unlocked_chords).grid(row=4, column=0, columnspan=2, padx=6, pady=2, sticky="ew")

chord_output = tk.Text(
    output_panel,
    height=5,
    width=30,
    bg="#1c212c",
    fg="#e7ebf0",
    insertbackground="#e7ebf0",
    bd=0,
    highlightthickness=1,
    highlightbackground="#3a4457",
    relief="flat",
    font=("Helvetica", 10)
)
chord_output.grid(row=5, column=0, columnspan=2, padx=6, pady=4, sticky="ew")
chord_output.configure(state="disabled")

canvas = tk.Canvas(output_panel, width=360, height=60, bg="#161a20", highlightthickness=1, highlightbackground="#3a4457", bd=0)
canvas.grid(row=6, column=0, columnspan=2, padx=6, pady=6, sticky="ew")

 # --------------------------
button_panel = create_panel(app)
button_panel.grid(row=5, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
ttk.Label(button_panel, text="▶  ACTIONS", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8,2))

ttk.Button(button_panel, text="▶ Generate", command=generate).grid(row=1, column=0, columnspan=2, padx=6, pady=2, sticky="ew")
ttk.Button(button_panel, text="⇩ Export", command=export).grid(row=2, column=0, padx=6, pady=2, sticky="ew")
ttk.Button(button_panel, text="⤓ Quick", command=quick_export).grid(row=2, column=1, padx=6, pady=2, sticky="ew")
ttk.Button(button_panel, text="↺ Reset", command=reset).grid(row=3, column=0, columnspan=2, padx=6, pady=2, sticky="ew")
ttk.Button(button_panel, text="✦ Randomize", command=randomize).grid(row=4, column=0, columnspan=2, padx=6, pady=2, sticky="ew")

def update_velocity_display(v):
    velocity_label.config(text=str(int(float(v))))
    draw_visual(state.get("prog", []))

# Lift all widgets above background
for child in app.winfo_children():
    try:
        if bg_label is None or child != bg_label:
            child.lift()
    except Exception:
        pass

app.update_idletasks()
required_height = app.winfo_reqheight() + 20
required_width = app.winfo_reqwidth() + 20
final_height = min(required_height, screen_height - 40)
final_width = max(window_width, required_width)
x_pos = max((screen_width - final_width) // 2, 0)
y_pos = 20
app.geometry(f"{final_width}x{final_height}+{x_pos}+{y_pos}")

# --------------------------
# BASS GENERATOR
# --------------------------
def generate_bass(prog):
    bass_notes = []

    for chord in prog:
        root = chord[0] + (int(bass_octave_var.get()) * 12)

        if bass_style_var.get() == "root":
            bass_notes.append([root])
        elif bass_style_var.get() == "octave":
            bass_notes.append([root, root + 12])
        elif bass_style_var.get() == "dub":
            bass_notes.append([root])
        elif bass_style_var.get() == "groove":
            bass_notes.append([root])

    return bass_notes

# --------------------------
# MIDI EXPORT
# --------------------------
def export_midi(prog, path):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    bass_track = None
    if bass_enabled_var.get():
        bass_track = MidiTrack()
        mid.tracks.append(bass_track)

    track.append(MetaMessage('set_tempo', tempo=bpm2tempo(int(tempo_var.get()))))
    if bass_track:
        bass_track.append(MetaMessage('set_tempo', tempo=bpm2tempo(int(tempo_var.get()))))

    ticks = 480
    length = float(length_var.get())
    base = int(ticks * 4 * length)

    chord_sequence = prog if pad_mode_var.get() else prog * int(bars_var.get())

    for chord in chord_sequence:
        for note in chord:
            track.append(Message('note_on', note=note, velocity=velocity_var.get(), time=0))

        if random_length_var.get():
            durations = [int(base * random.uniform(0.3, 1.2)) for _ in chord]
        else:
            durations = [base for _ in chord]

        if bass_track:
            bass_notes = generate_bass([chord])[0]
            for note in bass_notes:
                bass_track.append(Message('note_on', note=note, velocity=int(velocity_var.get() * 0.8), time=0))

        if independent_notes_var.get():
            pairs = sorted(list(zip(durations, chord)), key=lambda x: x[0])
            prev = 0
            for dur, note in pairs:
                delta = dur - prev
                track.append(Message('note_off', note=note, velocity=0, time=delta))
                prev = dur
        else:
            for i, note in enumerate(chord):
                dur = durations[i]
                track.append(Message('note_off', note=note, velocity=0, time=dur if i == 0 else 0))

        if bass_track:
            for i, note in enumerate(bass_notes):
                bass_track.append(Message('note_off', note=note, velocity=0, time=durations[0] if i == 0 else 0))

    mid.save(path)

app.mainloop()