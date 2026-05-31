"""
Swinburne Hawthorn Campus Navigation UI
- Uses campus_map.png only (no cropped image needed)
- Routes follow manually-taught street / path / walkway nodes
- Glenferrie Station is the main reference point
- Supports commands like: navigate from Glenferrie Station to EN
"""

import os, re, math, time, datetime, threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance

# -------------------- BASIC SETTINGS --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_IMG_PATH = os.path.join(BASE_DIR, "campus_map.png")

W, H = 1400, 800
PANEL_W = 380
TOP_H = 58
MAP_W = W - PANEL_W
MAP_H = int((H - TOP_H) * 0.72)
CAM_H = H - TOP_H - MAP_H

MAP_RAW_W, MAP_RAW_H = 2048, 1620
CAMERA_ENABLED = False
mode = "night"
route_step = 0
_map_cache = None
_map_cache_size = None

# -------------------- COLOURS --------------------
THEMES = {
    "night": {
        "bg": "#0a0a0a", "bg2": "#111111", "bg3": "#1a1a1a", "card": "#1c1c1e",
        "border": "#2c2c2e", "text": "#ffffff", "text2": "#9a9aa0", "text3": "#5a5a60",
        "accent": "#0a84ff", "green": "#30d158", "warn": "#ff9f0a", "route_bg": "#001a44",
        "route_glow": "#0a64c9", "route": "#0a84ff",
    },
    "day": {
        "bg": "#f2f2f7", "bg2": "#ffffff", "bg3": "#e5e5ea", "card": "#ffffff",
        "border": "#c7c7cc", "text": "#000000", "text2": "#5f6368", "text3": "#8e8e93",
        "accent": "#007aff", "green": "#34c759", "warn": "#ff9500", "route_bg": "#cce0ff",
        "route_glow": "#72b7ff", "route": "#007aff",
    },
}

def T(k):
    return THEMES[mode][k]

# -------------------- MAP PIXEL HELPERS --------------------
def pc(px, py, mx, my, mw, mh):
    """Map raw 2048x1620 pixel coordinate to displayed canvas coordinate."""
    return int(mx + px / MAP_RAW_W * mw), int(my + py / MAP_RAW_H * mh)


def raw_distance(points):
    total = 0
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        total += math.hypot(x2 - x1, y2 - y1)
    # calibrated visually: about 12 raw pixels per metre on this map crop
    return max(25, int(total / 12))

# -------------------- BUILDING DATABASE --------------------
# Building list follows the uploaded Hawthorn campus map.
BUILDINGS = {
    "STN": "Glenferrie Station",
    "14W": "14 Wakefield Street", "16W": "16 Wakefield Street", "24G": "24 George Street",
    "1A": "Security", "660A": "The Junction",
    "GS": "George Swinburne Building", "TA": "TA Building", "SR": "SR Building",
    "SPS": "Swinburne Place South", "SPW": "Health Sciences", "FSHQ": "Future Students HQ",
    "TD": "TD Building", "TC": "TC Building", "TB": "TB Building", "AGSE": "AGSE",
    "AR": "Arts Building", "EN": "Engineering Building", "EW": "Engineering West",
    "AD": "Old Administration Building", "UN": "UN / Latelab", "LB": "Library", "BA": "Business & Arts",
    "ATR": "Atrium", "FS": "Innovation Hub / Design Factory", "SA": "Science Annexe",
    "AS": "Applied Sciences", "CH": "Chemistry Building", "ATC": "Advanced Technologies Centre",
    "AMDC": "Advanced Manufacturing and Design Centre", "IS": "IS Building", "AV": "Aviation Building",
}

ALIASES = {
    "station": "STN", "glenferrie": "STN", "glenferrie station": "STN",
    "library": "LB", "lb": "LB", "student hq": "LB", "studenthq": "LB",
    "engineering": "EN", "engineering building": "EN", "en": "EN",
    "engineering west": "EW", "ew": "EW", "arts": "AR", "ar": "AR",
    "business": "BA", "business and arts": "BA", "business arts": "BA", "ba": "BA",
    "atrium": "ATR", "old admin": "AD", "old administration": "AD", "ad": "AD",
    "latelab": "UN", "un": "UN", "innovation hub": "FS", "fs": "FS",
    "george swinburne": "GS", "gs": "GS", "ta": "TA", "sr": "SR",
    "sps": "SPS", "spw": "SPW", "health sciences": "SPW",
    "atc": "ATC", "advanced technologies centre": "ATC", "advanced technologies center": "ATC",
    "chemistry": "CH", "ch": "CH", "applied sciences": "AS", "as": "AS",
    "amdc": "AMDC", "advanced manufacturing": "AMDC", "advanced manufacturing and design centre": "AMDC",
    "is": "IS", "is building": "IS", "aviation": "AV", "av": "AV",
    "agse": "AGSE", "tb": "TB", "tc": "TC", "td": "TD",
    "fshq": "FSHQ", "future students hq": "FSHQ", "security": "1A", "1a": "1A",
    "the junction": "660A", "junction": "660A", "660a": "660A",
    "science annexe": "SA", "sa": "SA", "14w": "14W", "16w": "16W", "24g": "24G",
}

# -------------------- WALKWAY / STREET NODE GRAPH --------------------
# Important: these are NOT building centres. They are entrance/path/street points on the visible map.
# The blue route follows these nodes, so it stays on paths and roads instead of cutting through buildings.
NODES = {
    # station and rail-side movement
    "STN_EXIT": (420, 850),
    "STN_EAST": (640, 850),
    "RAIL_PATH_W": (850, 825),
    "RAIL_PATH_C": (1070, 810),
    "JOHN_RAIL": (1288, 812),
    "WILLIAM_RAIL": (1605, 812),

    # Wakefield Street / north campus
    "GLEN_WAKE": (360, 445),
    "WAKE_W": (620, 445),
    "WAKE_FRED": (780, 445),
    "WAKE_GARDEN_W": (890, 435),
    "WAKE_GARDEN_C": (1030, 410),
    "WAKE_GS": (1090, 565),
    "GEORGE_CORNER": (1210, 610),
    "WAKE_WILLIAM": (1605, 610),

    # west/north buildings entrances
    "14W_ENT": (380, 520), "16W_ENT": (435, 520), "FSHQ_ENT": (270, 790), "ONE_A_ENT": (430, 720),
    "SPW_ENT": (570, 610), "SPS_ENT": (820, 610), "GS_ENT": (1050, 635), "TA_ENT": (1225, 515),
    "SR_ENT": (1195, 725), "AGSE_ENT": (1390, 650), "TB_ENT": (1495, 520),
    "TD_ENT": (1125, 250), "TC_ENT": (1440, 250),

    # central campus paths
    "CENTRAL_W": (800, 935),
    "EW_ENT": (735, 1010),
    "EN_WEST": (830, 1035),
    "EN_EAST": (965, 1035),
    "AR_ENT": (955, 930),
    "JOHN_CENTRAL": (1288, 930),
    "AD_ENT": (1180, 965),
    "ATRIUM_N": (1360, 940),
    "ATRIUM_C": (1360, 1020),
    "BA_ENT": (1460, 930),
    "LB_ENT": (1460, 1110),
    "UN_ENT": (1230, 1120),
    "FS_ENT": (1540, 1120),

    # south campus / Burwood Road
    "SOUTH_W": (760, 1195),
    "SA_ENT": (730, 1145),
    "AS_ENT": (730, 1310),
    "CH_ENT": (910, 1270),
    "ATC_W": (1030, 1180),
    "ATC_ENT": (1115, 1260),
    "BURWOOD_C": (1080, 1435),
    "BURWOOD_E": (1360, 1435),
    "AMDC_ENT": (1450, 1305),
    "IS_ENT": (1800, 1305),
    "AV_ENT": (1800, 1425),

    # George Street east buildings
    "GEORGE_ST": (1650, 960),
    "G24_ENT": (1875, 1030),
}

EDGES = [
    # rail/station spine
    ("STN_EXIT", "STN_EAST"), ("STN_EAST", "RAIL_PATH_W"), ("RAIL_PATH_W", "RAIL_PATH_C"),
    ("RAIL_PATH_C", "JOHN_RAIL"), ("JOHN_RAIL", "WILLIAM_RAIL"),

    # connect station to Wakefield Street through Glenferrie/Alfred side
    ("STN_EXIT", "FSHQ_ENT"), ("FSHQ_ENT", "ONE_A_ENT"), ("ONE_A_ENT", "WAKE_W"),
    ("WAKE_W", "WAKE_FRED"), ("WAKE_FRED", "WAKE_GARDEN_W"), ("WAKE_GARDEN_W", "WAKE_GARDEN_C"),
    ("WAKE_GARDEN_C", "WAKE_GS"), ("WAKE_GS", "GEORGE_CORNER"), ("GEORGE_CORNER", "WAKE_WILLIAM"),

    # north building access
    ("WAKE_W", "14W_ENT"), ("WAKE_W", "16W_ENT"), ("FSHQ_ENT", "14W_ENT"),
    ("WAKE_FRED", "SPW_ENT"), ("WAKE_FRED", "SPS_ENT"), ("WAKE_GS", "GS_ENT"),
    ("WAKE_GARDEN_C", "TA_ENT"), ("WAKE_GS", "SR_ENT"), ("WAKE_WILLIAM", "AGSE_ENT"),
    ("WAKE_WILLIAM", "TB_ENT"), ("WAKE_GARDEN_C", "TD_ENT"), ("WAKE_WILLIAM", "TC_ENT"),

    # central campus from rail spine
    ("RAIL_PATH_W", "CENTRAL_W"), ("CENTRAL_W", "EW_ENT"), ("CENTRAL_W", "EN_WEST"),
    ("EN_WEST", "EN_EAST"), ("EN_EAST", "AR_ENT"), ("AR_ENT", "JOHN_CENTRAL"),
    ("JOHN_RAIL", "JOHN_CENTRAL"), ("JOHN_CENTRAL", "ATRIUM_N"), ("ATRIUM_N", "ATRIUM_C"),
    ("ATRIUM_N", "BA_ENT"), ("ATRIUM_C", "LB_ENT"), ("ATRIUM_C", "FS_ENT"),
    ("JOHN_CENTRAL", "AD_ENT"), ("AD_ENT", "UN_ENT"), ("UN_ENT", "ATC_W"),

    # south campus
    ("CENTRAL_W", "SOUTH_W"), ("SOUTH_W", "SA_ENT"), ("SOUTH_W", "AS_ENT"), ("SOUTH_W", "CH_ENT"),
    ("CH_ENT", "ATC_W"), ("ATC_W", "ATC_ENT"), ("ATC_W", "BURWOOD_C"), ("BURWOOD_C", "BURWOOD_E"),
    ("BURWOOD_E", "AMDC_ENT"), ("AMDC_ENT", "IS_ENT"), ("IS_ENT", "AV_ENT"),

    # George Street / east
    ("WILLIAM_RAIL", "GEORGE_ST"), ("GEORGE_ST", "G24_ENT"), ("WAKE_WILLIAM", "WILLIAM_RAIL"),
]

BUILDING_NODE = {
    "STN": "STN_EXIT", "14W": "14W_ENT", "16W": "16W_ENT", "1A": "ONE_A_ENT", "FSHQ": "FSHQ_ENT", "660A": "STN_EXIT",
    "SPW": "SPW_ENT", "SPS": "SPS_ENT", "GS": "GS_ENT", "TA": "TA_ENT", "SR": "SR_ENT",
    "AGSE": "AGSE_ENT", "TB": "TB_ENT", "TC": "TC_ENT", "TD": "TD_ENT",
    "EW": "EW_ENT", "EN": "EN_EAST", "AR": "AR_ENT", "AD": "AD_ENT", "UN": "UN_ENT",
    "ATR": "ATRIUM_C", "BA": "BA_ENT", "LB": "LB_ENT", "FS": "FS_ENT", "SA": "SA_ENT",
    "AS": "AS_ENT", "CH": "CH_ENT", "ATC": "ATC_ENT", "AMDC": "AMDC_ENT", "IS": "IS_ENT", "AV": "AV_ENT", "24G": "G24_ENT",
}

# Human style instructions from Glenferrie Station.
ROUTES_FROM_STATION = {
    "GS": ["Exit Glenferrie Station.", "Cross toward Wakefield Street.", "Walk east along Wakefield Street.", "George Swinburne Building is on the right."],
    "TA": ["Exit Glenferrie Station.", "Go to Wakefield Street.", "Walk east past George Swinburne Building.", "TA Building is just beside GS."],
    "SR": ["Exit Glenferrie Station.", "Walk east along Wakefield Street.", "Pass GS and enter the path behind it.", "SR Building is behind GS."],
    "AR": ["Exit Glenferrie Station.", "Walk east through the central campus path.", "Continue toward the Arts and Engineering cluster.", "Arts Building is before Engineering."],
    "EN": ["Exit Glenferrie Station.", "Walk east through the central campus path.", "Pass EW / AR area.", "Engineering Building is behind Arts."],
    "LB": ["Exit Glenferrie Station.", "Walk east through the central campus path.", "Continue toward the Atrium.", "Library is on the south side of the Atrium."],
    "BA": ["Exit Glenferrie Station.", "Walk east through the central campus path.", "Continue past the Atrium.", "Business and Arts is beside the Library."],
    "ATC": ["Exit Glenferrie Station.", "Walk south toward Burwood Road.", "Turn east and follow Burwood Road / internal path.", "ATC is on the north side of Burwood Road."],
    "AMDC": ["Exit Glenferrie Station.", "Walk south toward Burwood Road.", "Follow Burwood Road east past ATC.", "AMDC is further east, below the Library."],
    "AS": ["Exit Glenferrie Station.", "Walk south toward Burwood Road.", "Enter the south-west campus area.", "Applied Sciences is west of Chemistry and ATC."],
    "CH": ["Exit Glenferrie Station.", "Walk south toward Burwood Road.", "Follow the path beside ATC.", "Chemistry is next to ATC."],
    "AGSE": ["Exit Glenferrie Station.", "Walk east along Wakefield Street.", "Continue past George Corner.", "AGSE is near William Street."],
    "TC": ["Exit Glenferrie Station.", "Walk east along Wakefield Street.", "Continue toward the north-east campus block.", "TC is north of TB."],
    "TD": ["Exit Glenferrie Station.", "Walk east along Wakefield Street.", "Continue toward Wakefield Gardens.", "TD is beside Swinburne College."],
}

# -------------------- ROUTE ENGINE --------------------
def normalise_place(text):
    if text is None:
        return None
    t = re.sub(r"[^a-zA-Z0-9 ]+", " ", str(text).lower()).strip()
    t = re.sub(r"\s+", " ", t)
    if t.upper() in BUILDINGS:
        return t.upper()
    if t in ALIASES:
        return ALIASES[t]
    for alias, code in sorted(ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", t):
            return code
    return None


def parse_command(text):
    t = text.lower().strip()
    m = re.search(r"from\s+(.+?)\s+to\s+(.+)$", t)
    if m:
        return normalise_place(m.group(1)), normalise_place(m.group(2))
    m = re.search(r"to\s+(.+?)\s+from\s+(.+)$", t)
    if m:
        return normalise_place(m.group(2)), normalise_place(m.group(1))
    m = re.search(r"(?:navigate|go|take me|guide me).*?to\s+(.+)$", t)
    if m:
        return FROM_B, normalise_place(m.group(1))
    return FROM_B, normalise_place(t)


def build_graph():
    g = {n: [] for n in NODES}
    for a, b in EDGES:
        ax, ay = NODES[a]; bx, by = NODES[b]
        w = math.hypot(bx - ax, by - ay)
        g[a].append((b, w))
        g[b].append((a, w))
    return g

GRAPH = build_graph()


def shortest_nodes(start, end):
    if start not in GRAPH or end not in GRAPH:
        return []
    dist = {start: 0}
    prev = {}
    unseen = set(GRAPH.keys())
    while unseen:
        cur = min(unseen, key=lambda n: dist.get(n, float("inf")))
        if cur == end or dist.get(cur, float("inf")) == float("inf"):
            break
        unseen.remove(cur)
        for nb, w in GRAPH[cur]:
            nd = dist[cur] + w
            if nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                prev[nb] = cur
    if end not in dist:
        return []
    path = [end]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return list(reversed(path))


def route_text_steps(from_code, to_code, metres):
    if from_code == "STN" and to_code in ROUTES_FROM_STATION:
        texts = ROUTES_FROM_STATION[to_code]
    else:
        texts = [
            f"Start at {BUILDINGS.get(from_code, from_code)}.",
            "Follow the highlighted campus walkway.",
            "Stay on the visible path and avoid crossing through buildings.",
            f"Arrive at {BUILDINGS.get(to_code, to_code)}."
        ]
    steps = []
    for i, txt in enumerate(texts):
        if i == 0:
            dist, icon, sub = "Start", "▲", "Begin navigation"
        elif i == len(texts) - 1:
            dist, icon, sub = "Arrive", "⬛", "Destination ahead"
        else:
            dist, icon, sub = f"{max(20, metres // max(1, len(texts)-1))}m", "▲", "Follow street/path"
            low = txt.lower()
            if "left" in low or "west" in low: icon = "◄"
            if "right" in low or "east" in low: icon = "►"
        steps.append({"dist": dist, "icon": icon, "main": txt, "sub": sub})
    return steps


def build_route(from_code, to_code):
    from_code = normalise_place(from_code) or from_code
    to_code = normalise_place(to_code) or to_code
    if from_code not in BUILDING_NODE or to_code not in BUILDING_NODE:
        return None
    start_node = BUILDING_NODE[from_code]
    end_node = BUILDING_NODE[to_code]
    node_path = shortest_nodes(start_node, end_node)
    if not node_path:
        return None
    points = [NODES[n] for n in node_path]
    metres = raw_distance(points)
    eta = max(1, math.ceil(metres / 80))
    steps = route_text_steps(from_code, to_code, metres)
    return points, steps, f"{eta} min", f"{metres}m", from_code, to_code, node_path

# -------------------- GLOBAL ROUTE STATE --------------------
FROM_B, TO_B = "STN", "EN"
_route = build_route(FROM_B, TO_B)
ROUTE_POINTS, STEPS, ETA, TOTAL, FROM_B, TO_B, ROUTE_NODE_NAMES = _route
STATUS_MSG = "Station reference mode: routes follow taught walkways"

# -------------------- UI FUNCTIONS --------------------
def rr(c, x1, y1, x2, y2, r=10, fill="#000", outline=None):
    outline = outline or fill
    c.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline=outline)
    c.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline=outline)
    c.create_oval(x1, y1, x1+2*r, y1+2*r, fill=fill, outline=outline)
    c.create_oval(x2-2*r, y1, x2, y1+2*r, fill=fill, outline=outline)
    c.create_oval(x1, y2-2*r, x1+2*r, y2, fill=fill, outline=outline)
    c.create_oval(x2-2*r, y2-2*r, x2, y2, fill=fill, outline=outline)


def apply_route(from_code, to_code, announce=False):
    global FROM_B, TO_B, ROUTE_POINTS, STEPS, ETA, TOTAL, route_step, STATUS_MSG, ROUTE_NODE_NAMES
    r = build_route(from_code, to_code)
    if not r:
        STATUS_MSG = f"Unknown route: {from_code} → {to_code}"
        return False
    ROUTE_POINTS, STEPS, ETA, TOTAL, FROM_B, TO_B, ROUTE_NODE_NAMES = r
    route_step = 0
    STATUS_MSG = f"Route uses {len(ROUTE_POINTS)} walkway/street nodes"
    from_var.set(FROM_B); to_var.set(TO_B)
    if announce:
        speak_step(0)
    return True


def handle_dropdown(event=None):
    apply_route(from_var.get(), to_var.get())


def handle_command(event=None):
    f, t = parse_command(command_var.get())
    if not f: f = FROM_B
    if not t:
        global STATUS_MSG
        STATUS_MSG = "Try: navigate from Glenferrie Station to EN"
        return
    apply_route(f, t, announce=True)


def speak(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def speak_step(i=None):
    i = route_step if i is None else i
    if 0 <= i < len(STEPS):
        threading.Thread(target=speak, args=(STEPS[i]["main"],), daemon=True).start()


def draw_left():
    canvas.create_rectangle(0, 0, PANEL_W, H, fill=T("bg2"), outline="")
    canvas.create_rectangle(PANEL_W-1, 0, PANEL_W, H, fill=T("border"), outline="")
    step = STEPS[min(route_step, len(STEPS)-1)]
    rr(canvas, 12, 18, PANEL_W-12, 210, r=18, fill=T("card"), outline=T("card"))
    rr(canvas, 24, 32, 120, 55, r=10, fill=T("accent"))
    canvas.create_text(72, 43, text=f"NEXT  {step['dist']}", fill="white", font=("Helvetica", 10, "bold"))
    arrow = {"▲": "↑", "◄": "←", "►": "→", "⬛": "●"}.get(step["icon"], "↑")
    canvas.create_text(70, 125, text=arrow, fill=T("accent"), font=("Helvetica", 78, "bold"))
    canvas.create_text(140, 112, text=step["main"], fill=T("text"), font=("Helvetica", 13, "bold"), anchor="w", width=220)
    canvas.create_text(140, 170, text=step["sub"], fill=T("text2"), font=("Helvetica", 10), anchor="w", width=220)

    y = 225
    canvas.create_rectangle(0, y, PANEL_W, y+58, fill=T("bg3"), outline="")
    canvas.create_text(PANEL_W//4, y+18, text=ETA, fill=T("text"), font=("Helvetica", 22, "bold"))
    canvas.create_text(PANEL_W//4, y+42, text="ETA", fill=T("text2"), font=("Helvetica", 10))
    canvas.create_rectangle(PANEL_W//2, y+8, PANEL_W//2+1, y+50, fill=T("border"), outline="")
    canvas.create_text(PANEL_W*3//4, y+18, text=TOTAL, fill=T("green"), font=("Helvetica", 22, "bold"))
    canvas.create_text(PANEL_W*3//4, y+42, text="Distance", fill=T("text2"), font=("Helvetica", 10))

    y += 72
    rr(canvas, 12, y, PANEL_W-12, y+54, r=12, fill=T("card"))
    canvas.create_oval(22, y+13, 45, y+39, fill=T("green"), outline="")
    canvas.create_text(33, y+26, text="▼", fill="white", font=("Helvetica", 11, "bold"))
    canvas.create_text(58, y+16, text="Destination", fill=T("text2"), font=("Helvetica", 9), anchor="w")
    canvas.create_text(58, y+35, text=f"{BUILDINGS[TO_B]} ({TO_B})", fill=T("text"), font=("Helvetica", 11, "bold"), anchor="w")

    y += 72
    canvas.create_text(16, y, text="ALL STEPS", fill=T("text3"), font=("Helvetica", 9, "bold"), anchor="w")
    y += 18
    for i, s in enumerate(STEPS):
        active = i == route_step
        canvas.create_rectangle(0, y, PANEL_W, y+61, fill=T("card") if active else T("bg2"), outline="")
        if active:
            canvas.create_rectangle(0, y, 4, y+61, fill=T("accent"), outline="")
        canvas.create_text(26, y+25, text=s["icon"], fill=T("accent") if active else T("text3"), font=("Helvetica", 13, "bold"))
        canvas.create_text(55, y+19, text=s["main"], fill=T("text") if active else T("text2"), font=("Helvetica", 9, "bold" if active else "normal"), anchor="w", width=285)
        canvas.create_text(PANEL_W-16, y+20, text=s["dist"], fill=T("accent") if active else T("text3"), font=("Helvetica", 9, "bold"), anchor="e")
        canvas.create_rectangle(55, y+60, PANEL_W, y+61, fill=T("border"), outline="")
        y += 62

    canvas.create_rectangle(0, H-52, PANEL_W, H, fill=T("bg3"), outline="")
    canvas.create_text(20, H-28, text=datetime.datetime.now().strftime("%H:%M"), fill=T("text"), font=("Helvetica", 17, "bold"), anchor="w")
    canvas.create_text(125, H-30, text=f"📍 {BUILDINGS[FROM_B]}", fill=T("text2"), font=("Helvetica", 9), anchor="w")
    canvas.create_text(125, H-14, text=STATUS_MSG, fill=T("text3"), font=("Helvetica", 8), anchor="w")
    rr(canvas, PANEL_W-72, H-44, PANEL_W-10, H-10, r=10, fill=T("accent"))
    canvas.create_text(PANEL_W-41, H-27, text="🎤", font=("Helvetica", 16), fill="white")


def draw_topbar():
    canvas.create_rectangle(PANEL_W, 0, W, TOP_H, fill=T("card"), outline="")
    canvas.create_rectangle(PANEL_W, TOP_H-1, W, TOP_H, fill=T("border"), outline="")
    x = PANEL_W + 16
    canvas.create_text(x, 29, text=FROM_B, fill=T("accent"), font=("Helvetica", 15, "bold"), anchor="w")
    canvas.create_text(x+52, 29, text="→", fill=T("text2"), font=("Helvetica", 14), anchor="w")
    canvas.create_text(x+72, 29, text=TO_B, fill=T("green"), font=("Helvetica", 15, "bold"), anchor="w")
    canvas.create_text(x+118, 29, text=f"{BUILDINGS[FROM_B]} → {BUILDINGS[TO_B]}", fill=T("text2"), font=("Helvetica", 10), anchor="w")
    dn = "☀ Day" if mode == "night" else "🌙 Night"
    rr(canvas, W-155, 8, W-70, 48, r=10, fill="#2c2c2e" if mode == "night" else "#e5e5ea", outline=T("accent"))
    canvas.create_text(W-112, 29, text=dn, fill=T("text"), font=("Helvetica", 11, "bold"))
    rr(canvas, W-68, 9, W-8, 48, r=9, fill=T("accent"))
    canvas.create_text(W-38, 24, text=ETA, fill="white", font=("Helvetica", 10, "bold"))
    canvas.create_text(W-38, 39, text=TOTAL, fill="white", font=("Helvetica", 9))


def draw_map(mx, my, mw, mh):
    global _map_cache, _map_cache_size
    if _map_cache is None or _map_cache_size != (mw, mh, mode):
        try:
            raw = Image.open(MAP_IMG_PATH).resize((mw, mh), Image.LANCZOS)
            if mode == "night":
                raw = ImageEnhance.Brightness(raw).enhance(0.78)
                raw = ImageEnhance.Color(raw).enhance(0.85)
            _map_cache = ImageTk.PhotoImage(raw)
            _map_cache_size = (mw, mh, mode)
        except Exception as e:
            canvas.create_rectangle(mx, my, mx+mw, my+mh, fill=T("bg3"), outline="")
            canvas.create_text(mx+mw//2, my+mh//2, text=f"campus_map.png not found\n{MAP_IMG_PATH}", fill=T("text2"), font=("Helvetica", 12))
            return
    canvas.create_image(mx, my, image=_map_cache, anchor="nw")

    # badge
    rr(canvas, mx+8, my+8, mx+205, my+30, r=6, fill=T("card"))
    canvas.create_text(mx+15, my+19, text="SWINBURNE HAWTHORN CAMPUS", fill=T("text2"), font=("Helvetica", 8, "bold"), anchor="w")

    pts = [pc(x, y, mx, my, mw, mh) for x, y in ROUTE_POINTS]
    # glow and route
    for width, col in [(13, T("route_bg")), (8, T("route_glow")), (4, T("route"))]:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            canvas.create_line(x1, y1, x2, y2, fill=col, width=width, capstyle="round", joinstyle="round")

    # small arrow markers along line
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        mx2, my2 = (x1+x2)//2, (y1+y2)//2
        ang = math.atan2(y2-y1, x2-x1)
        size = 7
        p1 = (mx2 + math.cos(ang)*size, my2 + math.sin(ang)*size)
        p2 = (mx2 + math.cos(ang+2.5)*size, my2 + math.sin(ang+2.5)*size)
        p3 = (mx2 + math.cos(ang-2.5)*size, my2 + math.sin(ang-2.5)*size)
        canvas.create_polygon(*p1, *p2, *p3, fill="white", outline="")

    # start / end markers
    sx, sy = pts[0]; ex, ey = pts[-1]
    canvas.create_oval(sx-10, sy-10, sx+10, sy+10, fill=T("accent"), outline="white", width=2)
    canvas.create_text(sx, sy, text="A", fill="white", font=("Helvetica", 8, "bold"))
    canvas.create_oval(ex-10, ey-10, ex+10, ey+10, fill=T("green"), outline="white", width=2)
    canvas.create_text(ex, ey, text="B", fill="white", font=("Helvetica", 8, "bold"))

    # current position pulse follows route step proportionally
    idx = min(route_step, len(pts)-1)
    cx, cy = pts[idx]
    pulse = int(11 + abs(math.sin(time.time()*3))*5)
    canvas.create_oval(cx-pulse, cy-pulse, cx+pulse, cy+pulse, outline=T("accent"), width=2)
    canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill=T("accent"), outline="white", width=2)

    # compass
    ccx, ccy, cr = mx+mw-28, my+54, 24
    canvas.create_oval(ccx-cr, ccy-cr, ccx+cr, ccy+cr, fill=T("card"), outline=T("border"))
    canvas.create_text(ccx, ccy-cr-8, text="N", fill=T("accent"), font=("Helvetica", 8, "bold"))
    canvas.create_polygon(ccx, ccy-cr+5, ccx-7, ccy, ccx, ccy-4, ccx+7, ccy, fill=T("accent"))
    canvas.create_polygon(ccx, ccy+cr-5, ccx-7, ccy, ccx, ccy+4, ccx+7, ccy, fill="#ff453a")


def draw_camera(cx, cy, cw, ch):
    canvas.create_rectangle(cx, cy, cx+cw, cy+ch, fill="#101010", outline="")
    canvas.create_text(cx+cw//2, cy+ch//2-8, text="📷", fill=T("text3"), font=("Helvetica", 24))
    canvas.create_text(cx+cw//2, cy+ch//2+24, text="Camera feed disabled for map testing", fill=T("text3"), font=("Helvetica", 11))
    rr(canvas, cx+10, cy+10, cx+70, cy+34, r=6, fill="#cc0000")
    canvas.create_text(cx+40, cy+22, text="● LIVE", fill="white", font=("Helvetica", 9, "bold"))
    step = STEPS[min(route_step, len(STEPS)-1)]
    canvas.create_rectangle(cx, cy+ch-34, cx+cw, cy+ch, fill=T("bg2"), outline="")
    canvas.create_text(cx+cw//2, cy+ch-17, text=step["main"], fill=T("text"), font=("Helvetica", 11, "bold"))


def toggle_mode():
    global mode, _map_cache
    mode = "day" if mode == "night" else "night"
    _map_cache = None


def on_click(e):
    global route_step
    if e.x >= W-160 and e.y <= TOP_H:
        toggle_mode()
        return
    if e.x < PANEL_W and e.y > H-52:
        route_step = (route_step + 1) % len(STEPS)
        speak_step(route_step)


def update():
    canvas.delete("all")
    canvas.create_rectangle(0, 0, W, H, fill=T("bg"), outline="")
    draw_left()
    draw_topbar()
    draw_map(PANEL_W, TOP_H, MAP_W, MAP_H)
    draw_camera(PANEL_W, TOP_H + MAP_H, MAP_W, CAM_H)
    root.after(50, update)

# -------------------- TK SETUP --------------------
root = tk.Tk()
root.title("Campus Navigation — Swinburne Hawthorn")
root.geometry(f"{W}x{H}")
root.resizable(False, False)
canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0)
canvas.pack()
canvas.bind("<Button-1>", on_click)

codes = sorted(BUILDINGS.keys())
from_var = tk.StringVar(value=FROM_B)
to_var = tk.StringVar(value=TO_B)
command_var = tk.StringVar(value="navigate from Glenferrie Station to EN")

from_box = ttk.Combobox(root, textvariable=from_var, values=codes, width=8, state="readonly")
to_box = ttk.Combobox(root, textvariable=to_var, values=codes, width=8, state="readonly")
cmd_box = ttk.Entry(root, textvariable=command_var, width=42)
go_btn = ttk.Button(root, text="Go", command=handle_command)

from_box.place(x=PANEL_W+320, y=16)
to_box.place(x=PANEL_W+405, y=16)
cmd_box.place(x=PANEL_W+495, y=16)
go_btn.place(x=PANEL_W+800, y=14, width=60, height=30)
from_box.bind("<<ComboboxSelected>>", handle_dropdown)
to_box.bind("<<ComboboxSelected>>", handle_dropdown)
cmd_box.bind("<Return>", handle_command)

root.protocol("WM_DELETE_WINDOW", root.destroy)
update()
root.mainloop()
