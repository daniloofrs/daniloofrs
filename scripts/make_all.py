import os
import re
import urllib.request
import html
import datetime
from PIL import Image, ImageEnhance, ImageOps

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# 1. MAKE ASCII SVG (avi-ascii.svg)
# ==========================================
def generate_ascii_svg():
    print("[1/4] Generating avi-ascii.svg with Kenshin portrait...")
    src_path = os.path.join(REPO_DIR, "assets", "portrait.jpg")
    im = Image.open(src_path).convert("RGB")

    r, g, b = im.split()
    custom_gray = Image.blend(r, g, 0.4)
    custom_gray = ImageOps.autocontrast(custom_gray)
    custom_gray = ImageEnhance.Contrast(custom_gray).enhance(1.35)

    COLS = 100
    ROWS = 53
    CELL_W = 8
    CELL_H = 15
    RAMP = " .`:-=+*cs#%@"

    resized = custom_gray.resize((COLS, ROWS), Image.LANCZOS)
    px = resized.load()

    rows_txt = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = pow(px[x, y] / 255.0, 1.05)
            idx = int(lum * (len(RAMP) - 1) + 0.5)
            chars.append(RAMP[max(0, min(len(RAMP) - 1, idx))])
        rows_txt.append("".join(chars))

    PAD = 20
    TITLEBAR_H = 46
    STATUS_H = 46
    CHROME_FS = 22
    ART_W = COLS * CELL_W
    ART_H = ROWS * CELL_H
    CANVAS_W = 840
    CANVAS_H = 907

    BG = "#0d1117"
    BG2 = "#111722"
    FRAME = "#30363d"
    TITLE_TEXT = "#7d8590"
    INK = "#c9d1d9"
    CURSOR = "#c9d1d9"
    ROW_DUR = 0.11
    STAGGER = 0.11

    art_top = TITLEBAR_H + PAD * 0.35

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        '<defs><linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/>',
        f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#abg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*20}" cy="{TITLEBAR_H/2}" r="8" fill="{dot}"/>')
    p.append(
        f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + CHROME_FS*0.35:.1f}" fill="{TITLE_TEXT}" '
        f'font-size="{CHROME_FS}" text-anchor="middle">danilo@github: ~$ ./portrait.sh</text>'
    )

    font_size = CELL_H * 0.86
    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (
            f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" '
            f'lengthAdjust="spacing">{safe}</text>'
        )
        p.append(
            f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" '
            f'height="{CELL_H}" width="0"><animate attributeName="width" '
            f'from="0" to="{ART_W}" begin="{delay:.3f}s" dur="{ROW_DUR:.2f}s" '
            f'fill="freeze"/></rect></clipPath>'
        )
        p.append(f'<g clip-path="url(#r{ry})">{text}</g>')
        p.append(
            f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" '
            f'fill="{CURSOR}" opacity="0"><animate attributeName="x" '
            f'from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    line_y = TITLEBAR_H + ART_H + PAD * 0.35
    status_y = line_y + STATUS_H * 0.62
    prefix = "danilo@github:~$ whoami Danilo Fernandes "
    cursor_x = PAD + len(prefix) * CHROME_FS * 0.6
    p.append(f'<line x1="0" y1="{line_y:.1f}" x2="{CANVAS_W}" y2="{line_y:.1f}" stroke="{FRAME}"/>')
    p.append(
        f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="{CHROME_FS}">'
        f'danilo@github:~$ whoami <tspan fill="{INK}">Danilo Fernandes</tspan></text>'
    )
    p.append(
        f'<rect x="{cursor_x:.0f}" y="{status_y - CHROME_FS*0.8:.1f}" '
        f'width="{CHROME_FS*0.55:.0f}" height="{CHROME_FS*1.05:.0f}" fill="{INK}">'
        f'<animate attributeName="opacity" values="1;1;0;0" '
        f'keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>'
    )
    p.append("</svg>")

    out_path = os.path.join(REPO_DIR, "avi-ascii.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(p))
    print(f"[1/4] Wrote {out_path} ({CANVAS_W}x{CANVAS_H})")


# ==========================================
# 2. MAKE INFO CARD SVG (info-card.svg)
# ==========================================
def generate_info_card():
    print("[2/4] Generating info-card.svg...")
    BG = "#0d1117"
    BG2 = "#111722"
    FRAME = "#30363d"
    TITLE_TEXT = "#7d8590"
    KEY = "#39d353"
    VAL = "#c9d1d9"
    ACCENT = "#58a6ff"
    DIM = "#8b949e"
    BULLET = "#39d353"

    W, H = 620, 506
    PAD = 20
    PAD_X = 26
    LINE_H = 21
    TITLEBAR_H = 30
    STATUS_H = 30
    FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

    ROWS = [
        ("head", "danilo@github", ""),
        ("sep", "", ""),
        ("kv", "Role", "Data Engineer (Intern / Junior)"),
        ("kv", "Edu", "Computer Science Student"),
        ("kv", "Local", "João Pessoa, PB - Brazil"),
        ("kv", "Focus", "Pipelines, Ingestion & Modeling"),
        ("gap", "", ""),
        ("sec", "Stack", ""),
        ("kv", "Lang", "Python, SQL, Bash"),
        ("kv", "Database", "PostgreSQL (Relational Schemas)"),
        ("kv", "Infra", "Docker, Docker Compose, Linux, Git"),
        ("kv", "Automate", "n8n"),
        ("gap", "", ""),
        ("sec", "Highlights", ""),
        ("bullet", "REST API automated ingestion (Requests, psycopg)", ""),
        ("bullet", "Relational databases with Docker Compose volumes", ""),
        ("bullet", "Tabular data structuring & analytical SQL", ""),
    ]

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def anim(begin: float) -> str:
        return (
            f'<animate attributeName="opacity" from="0" to="1" dur="0.35s" '
            f'begin="{begin:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="8 0" to="0 0" dur="0.35s" begin="{begin:.2f}s" fill="freeze"/>'
        )

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}" font-size="13">',
        '<defs><linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/>',
        f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
        f'<circle cx="{PAD}" cy="{TITLEBAR_H/2}" r="5" fill="#ff5f56"/>',
        f'<circle cx="{PAD+16}" cy="{TITLEBAR_H/2}" r="5" fill="#ffbd2e"/>',
        f'<circle cx="{PAD+32}" cy="{TITLEBAR_H/2}" r="5" fill="#27c93f"/>',
        f'<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" text-anchor="middle" font-size="12">danilo@github: ~$ fastfetch</text>',
    ]

    y = 58
    i = 0
    for kind, a, b in ROWS:
        begin = 0.12 * i
        if kind == "gap":
            y += 8
            continue
        if kind == "sep":
            out.append(f'<g opacity="0"><text x="{PAD_X}" y="{y}" fill="{DIM}">----------------</text>{anim(begin)}</g>')
            y += LINE_H
            i += 1
            continue
        if kind == "head":
            out.append(f'<g opacity="0"><text x="{PAD_X}" y="{y}" fill="{ACCENT}" font-weight="bold">{esc(a)}</text>{anim(begin)}</g>')
            y += LINE_H
            i += 1
            continue
        if kind == "sec":
            out.append(f'<g opacity="0"><text x="{PAD_X}" y="{y}" fill="{ACCENT}" font-weight="bold">{esc("~ " + a)}</text>{anim(begin)}</g>')
            y += LINE_H
            i += 1
            continue
        if kind == "bullet":
            out.append(
                f'<g opacity="0">'
                f'<text x="{PAD_X}" y="{y}" fill="{BULLET}">&#8226;</text>'
                f'<text x="{PAD_X+16}" y="{y}" fill="{VAL}">{esc(a)}</text>'
                f'{anim(begin)}</g>'
            )
            y += LINE_H
            i += 1
            continue
        out.append(
            f'<g opacity="0">'
            f'<text x="{PAD_X}" y="{y}" fill="{KEY}" font-weight="bold">{esc(a)}</text>'
            f'<text x="{PAD_X+90}" y="{y}" fill="{VAL}">{esc(b)}</text>'
            f'{anim(begin)}</g>'
        )
        y += LINE_H
        i += 1

    line_y = H - STATUS_H
    status_y = line_y + 19
    prefix = "danilo@github:~$ fastfetch "
    cursor_x = PAD + len(prefix) * 13 * 0.6
    out.append(f'<line x1="0" y1="{line_y}" x2="{W}" y2="{line_y}" stroke="{FRAME}"/>')
    out.append(f'<text x="{PAD}" y="{status_y}" fill="{TITLE_TEXT}" font-size="13">danilo@github:~$ <tspan fill="{VAL}">fastfetch</tspan></text>')
    blink = '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
    out.append(f'<rect x="{cursor_x:.0f}" y="{status_y-12}" width="8" height="14" fill="{VAL}">{blink}</rect>')
    out.append("</svg>")

    out_path = os.path.join(REPO_DIR, "info-card.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"[2/4] Wrote {out_path} ({W}x{H})")


# ==========================================
# 3. MAKE CONTRIBUTIONS HEATMAP (contrib-heatmap.svg)
# ==========================================
def generate_heatmap_svg():
    print("[3/4] Fetching contributions & rendering heatmap...")
    url = "https://github.com/users/daniloofrs/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"})
    html_doc = urllib.request.urlopen(req).read().decode("utf-8")

    tooltips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', html_doc, re.DOTALL):
        cid = m.group(1)
        txt = m.group(2).strip()
        cm = re.search(r'(\d+)\s+contribution', txt)
        tooltips[cid] = int(cm.group(1)) if cm else 0

    days = []
    for cell in re.findall(r'<td[^>]*class="[^"]*ContributionCalendar-day[^"]*"[^>]*>', html_doc):
        dm = re.search(r'data-date="([^"]+)"', cell)
        lm = re.search(r'data-level="([^"]+)"', cell)
        im = re.search(r'id="([^"]+)"', cell)
        if dm and lm and im:
            date = dm.group(1)
            level = int(lm.group(1))
            cid = im.group(1)
            count = tooltips.get(cid, 0)
            days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}

    cur = longest = run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    for d in reversed(days):
        if d["count"] > 0:
            cur += 1
        else:
            break

    PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
    CELL = 12
    GAP = 3
    STEP = CELL + GAP
    PAD = 22
    LEFT_LABEL_W = 30
    TOP_LABEL_H = 20
    TITLEBAR_H = 30

    BG = "#0a0e14"
    BG2 = "#0d1420"
    FRAME = "#1f6feb"
    MUTED = "#7d8590"
    TEXT = "#e6edf3"
    ACCENT = "#22d3ee"
    GREEN = "#39d353"
    GOLD = "#f2cc60"

    COL_T = 0.018
    ROW_T = 0.045
    CELL_DUR = 0.42

    MONTHS_PT = ["jan", "fev", "mar", "abr", "mai", "jun",
                 "jul", "ago", "set", "out", "nov", "dez"]

    def level_for(count: int) -> int:
        if count == 0:
            return 0
        if count <= 5:
            return 1
        if count <= 15:
            return 2
        if count <= 30:
            return 3
        if count <= 50:
            return 4
        return 5

    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7
    grid, col = [], [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)

    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels, seen = [], set()
    for ci, column in enumerate(grid):
        for c in column:
            if c is None:
                continue
            date = datetime.date.fromisoformat(c[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                month_labels.append((ci, MONTHS_PT[date.month - 1]))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 88
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        '<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/>',
        f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" fill="none" stroke="{FRAME}" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]

    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    p.append(
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" '
        f'font-size="12" text-anchor="middle">danilo@github: ~/contributions --graph</text>'
    )

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        p.append(f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')

    for wi, wname in [(1, "Seg"), (3, "Qua"), (5, "Sex")]:
        y = grid_top + wi * STEP + CELL * 0.78
        p.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    h = CELL / 2
    for ci, column in enumerate(grid):
        cx = grid_left + ci * STEP + h
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            cy = grid_top + ri * STEP + h
            delay = ci * COL_T + ri * ROW_T
            word = "contribuição" if count == 1 else "contribuições"
            p.append(
                f'<g transform="translate({cx},{cy})">'
                f'<rect x="{-h}" y="{-h}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[lvl]}" opacity="0">'
                f'<title>{date_s}: {count} {word}</title>'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.3f}s" dur="0.09s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="scale" values="0.1;1.15;1" keyTimes="0;0.72;1" calcMode="spline" keySplines="0.22 1 0.36 1;0.33 0 0.66 1" begin="{delay:.3f}s" dur="{CELL_DUR:.2f}s" fill="freeze"/>'
                f'</rect></g>'
            )

    leg_y = grid_top + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 70)
    p.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Menos</text>')
    lx = leg_x + 8
    for color in PALETTE:
        p.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    p.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">Mais</text>')

    sep_y = leg_y + CELL + 14
    p.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

    rng_start, rng_end = days[0]["date"], days[-1]["date"]
    ly = sep_y + 24
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}" xml:space="preserve">'
             f'<tspan font-weight="700">{total:,}</tspan>'
             f'<tspan fill="{MUTED}"> contribuições no último ano</tspan></text>')
    p.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">{rng_start} &#8594; {rng_end}</text>')
    ly += 24
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}" xml:space="preserve">streak atual '
             f'<tspan fill="{ACCENT}" font-weight="700">{cur} dias</tspan>'
             f'<tspan fill="{MUTED}">   &#183;   recorde </tspan>'
             f'<tspan fill="{ACCENT}" font-weight="700">{longest} dias</tspan></text>')
    p.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">melhor dia <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> em {best["date"]}</text>')

    p.append("</svg>")
    out_path = os.path.join(REPO_DIR, "contrib-heatmap.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(p))
    print(f"[3/4] Wrote {out_path} ({n_cols} weeks, {total} contributions)")


# ==========================================
# 4. MAKE PROJECT CARDS (project-*.svg)
# ==========================================
def generate_project_cards():
    print("[4/4] Generating project window cards...")
    W, H = 415, 230
    PAD = 16
    TITLEBAR_H = 30
    FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    BG = "#0d1117"
    BG2 = "#111722"
    FRAME = "#30363d"
    TITLE_TEXT = "#7d8590"
    TEXT_COLOR = "#c9d1d9"
    ACCENT = "#38bdf8"
    GREEN = "#39d353"
    YELLOW = "#f2cc60"
    MUTED = "#8b949e"
    BADGE_BG = "#1f242c"

    # Card 1: api-data-fetcher
    card1 = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
  <defs>
    <linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG2}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="10" fill="url(#pbg)"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="{FRAME}"/>
  <line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>
  <circle cx="{PAD}" cy="{TITLEBAR_H/2}" r="4.5" fill="#ff5f56"/>
  <circle cx="{PAD+14}" cy="{TITLEBAR_H/2}" r="4.5" fill="#ffbd2e"/>
  <circle cx="{PAD+28}" cy="{TITLEBAR_H/2}" r="4.5" fill="#27c93f"/>
  <text x="{PAD+44}" y="{TITLEBAR_H/2 + 3.5}" fill="{TITLE_TEXT}" font-size="11">api-data-fetcher/main.py</text>
  <text x="{W-PAD}" y="{TITLEBAR_H/2 + 3.5}" fill="{GREEN}" font-size="10" text-anchor="end">● Docker UP</text>
  <text x="{PAD}" y="56" fill="{ACCENT}" font-size="15" font-weight="bold">API Data Fetcher</text>
  <text x="{PAD}" y="78" fill="{TEXT_COLOR}" font-size="11.5">Pipeline em Python consumindo cotações</text>
  <text x="{PAD}" y="95" fill="{TEXT_COLOR}" font-size="11.5">via API REST com persistência contínua</text>
  <text x="{PAD}" y="112" fill="{TEXT_COLOR}" font-size="11.5">em banco PostgreSQL e append em CSV.</text>
  <g transform="translate({PAD}, 128)">
    <rect width="185" height="22" rx="4" fill="{BADGE_BG}" stroke="{FRAME}" stroke-width="0.7"/>
    <text x="8" y="15" fill="{MUTED}" font-size="10.5">🐳 Docker: <tspan fill="{GREEN}">2 containers</tspan></text>
  </g>
  <g transform="translate({PAD+193}, 128)">
    <rect width="185" height="22" rx="4" fill="{BADGE_BG}" stroke="{FRAME}" stroke-width="0.7"/>
    <text x="8" y="15" fill="{MUTED}" font-size="10.5">💾 Volume: <tspan fill="{ACCENT}">pg_data</tspan></text>
  </g>
  <g transform="translate({PAD}, 162)">
    <rect x="0" width="58" height="20" rx="4" fill="{FRAME}"/>
    <text x="29" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">Python</text>
    <rect x="64" width="76" height="20" rx="4" fill="{FRAME}"/>
    <text x="102" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">PostgreSQL</text>
    <rect x="146" width="58" height="20" rx="4" fill="{FRAME}"/>
    <text x="175" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">Docker</text>
    <rect x="210" width="62" height="20" rx="4" fill="{FRAME}"/>
    <text x="241" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">psycopg</text>
  </g>
  <line x1="0" y1="{H-26}" x2="{W}" y2="{H-26}" stroke="{FRAME}"/>
  <text x="{PAD}" y="{H-10}" fill="{TITLE_TEXT}" font-size="10">git:(main) • utf-8</text>
  <text x="{W-PAD}" y="{H-10}" fill="{ACCENT}" font-size="10" text-anchor="end">Ver Repositório ➜</text>
</svg>"""

    # Card 2: jp-public-spending-etl
    card2 = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
  <defs>
    <linearGradient id="pbg2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG2}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="10" fill="url(#pbg2)"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="{FRAME}"/>
  <line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>
  <circle cx="{PAD}" cy="{TITLEBAR_H/2}" r="4.5" fill="#ff5f56"/>
  <circle cx="{PAD+14}" cy="{TITLEBAR_H/2}" r="4.5" fill="#ffbd2e"/>
  <circle cx="{PAD+28}" cy="{TITLEBAR_H/2}" r="4.5" fill="#27c93f"/>
  <text x="{PAD+44}" y="{TITLEBAR_H/2 + 3.5}" fill="{TITLE_TEXT}" font-size="11">jp-public-spending-etl/etl.py</text>
  <text x="{W-PAD}" y="{TITLEBAR_H/2 + 3.5}" fill="{YELLOW}" font-size="10" text-anchor="end">● Em Dev</text>
  <text x="{PAD}" y="56" fill="{ACCENT}" font-size="15" font-weight="bold">Gastos Públicos - JP</text>
  <text x="{PAD}" y="78" fill="{TEXT_COLOR}" font-size="11.5">Pipeline ETL para higienização e modelagem</text>
  <text x="{PAD}" y="95" fill="{TEXT_COLOR}" font-size="11.5">relacional dos gastos públicos de João</text>
  <text x="{PAD}" y="112" fill="{TEXT_COLOR}" font-size="11.5">Pessoa (PB) estruturado para SQL rápido.</text>
  <g transform="translate({PAD}, 128)">
    <rect width="185" height="22" rx="4" fill="{BADGE_BG}" stroke="{FRAME}" stroke-width="0.7"/>
    <text x="8" y="15" fill="{MUTED}" font-size="10.5">🏛️ Fonte: <tspan fill="{YELLOW}">Dados Abertos</tspan></text>
  </g>
  <g transform="translate({PAD+193}, 128)">
    <rect width="185" height="22" rx="4" fill="{BADGE_BG}" stroke="{FRAME}" stroke-width="0.7"/>
    <text x="8" y="15" fill="{MUTED}" font-size="10.5">📐 Schema: <tspan fill="{ACCENT}">Star Schema</tspan></text>
  </g>
  <g transform="translate({PAD}, 162)">
    <rect x="0" width="58" height="20" rx="4" fill="{FRAME}"/>
    <text x="29" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">Python</text>
    <rect x="64" width="58" height="20" rx="4" fill="{FRAME}"/>
    <text x="93" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">Pandas</text>
    <rect x="128" width="76" height="20" rx="4" fill="{FRAME}"/>
    <text x="166" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">PostgreSQL</text>
    <rect x="210" width="58" height="20" rx="4" fill="{FRAME}"/>
    <text x="239" y="14" fill="{TEXT_COLOR}" font-size="10" text-anchor="middle">Docker</text>
  </g>
  <line x1="0" y1="{H-26}" x2="{W}" y2="{H-26}" stroke="{FRAME}"/>
  <text x="{PAD}" y="{H-10}" fill="{TITLE_TEXT}" font-size="10">git:(main) • utf-8</text>
  <text x="{W-PAD}" y="{H-10}" fill="{ACCENT}" font-size="10" text-anchor="end">Ver Repositório ➜</text>
</svg>"""

    p1 = os.path.join(REPO_DIR, "project-api-fetcher.svg")
    p2 = os.path.join(REPO_DIR, "project-jp-spending.svg")
    with open(p1, "w", encoding="utf-8") as f:
        f.write(card1)
    with open(p2, "w", encoding="utf-8") as f:
        f.write(card2)
    print(f"[4/4] Wrote {p1} and {p2}")


if __name__ == "__main__":
    generate_ascii_svg()
    generate_info_card()
    generate_heatmap_svg()
    generate_project_cards()
    print("All SVG assets generated successfully!")
