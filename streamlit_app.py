# app.py
import streamlit as st
from collections import deque
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# ---------------- Basics ----------------
st.set_page_config(page_title="Connect Dots Game", layout="wide")

# Minimal CSS — üst boşlukları azalt, yazı tipini sade tut
st.markdown("""
<style>
.main .block-container { padding-top: 0.6rem; padding-bottom: 0.6rem; }
h1 { margin: .2rem 0 .2rem 0; }
h3 { margin: .4rem 0 .2rem 0; }
hr { margin: .6rem 0 .4rem 0; }
</style>
""", unsafe_allow_html=True)

# ---------------- Game params (UPDATED) ----------------
ROWS = 8            # height
COLS = 10            # width
SPACING = 2.0        # distance between dots (bigger = more space)
DOT_SIZE = 8
LINE_WIDTH = 3
FIG_HEIGHT = 620

DOT_COLOR = "black"
LINE_COLOR = "green"
P1_FILL = "rgba(128, 0, 128, 0.35)"   # purple
P2_FILL = "rgba(255, 165, 0, 0.35)"   # orange

# ---------------- Helpers ----------------
def is_adjacent(p, q):
    (r1, c1), (r2, c2) = p, q
    return (abs(r1 - r2) == 1 and c1 == c2) or (abs(c1 - c2) == 1 and r1 == r2)

def canonical_edge(p, q):
    return tuple(sorted((p, q)))

def cell_edges_of(r, c):
    top    = canonical_edge((r, c), (r, c+1))
    bottom = canonical_edge((r+1, c), (r+1, c+1))
    left   = canonical_edge((r, c), (r+1, c))
    right  = canonical_edge((r, c+1), (r+1, c+1))
    return [top, right, bottom, left]

def neighbors_4(cell):
    r, c = cell
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        rr, cc = r+dr, c+dc
        if 0 <= rr < ROWS-1 and 0 <= cc < COLS-1:
            yield (rr, cc)

def bfs_components(cells):
    seen, comps = set(), []
    for start in cells:
        if start in seen: continue
        q = deque([start]); seen.add(start); comp = [start]
        while q:
            cur = q.popleft()
            for nb in neighbors_4(cur):
                if nb in cells and nb not in seen:
                    seen.add(nb); q.append(nb); comp.append(nb)
        comps.append(comp)
    return comps

def affected_cells_by_edge(p, q):
    (r1, c1), (r2, c2) = p, q
    cells = set()
    if r1 == r2:  # horizontal
        r = r1; cmin, cmax = sorted([c1, c2])
        if r-1 >= 0:   cells.add((r-1, cmin))
        if r < ROWS-1: cells.add((r, cmin))
    else:  # vertical
        c = c1; rmin, rmax = sorted([r1, r2])
        if c-1 >= 0:   cells.add((rmin, c-1))
        if c < COLS-1: cells.add((rmin, c))
    return {cell for cell in cells if 0 <= cell[0] < ROWS-1 and 0 <= cell[1] < COLS-1}

def total_possible_edges():
    return ROWS*(COLS-1) + (ROWS-1)*COLS

# ---------------- State ----------------
def init_state():
    st.session_state.edges = set()
    st.session_state.claimed = {}              # (r,c) -> 1/2
    st.session_state.current_player = 1
    st.session_state.scores = {1: 0, 2: 0}
    st.session_state.game_over = False
    st.session_state.selection = []            # [(r,c)]

if "edges" not in st.session_state:
    init_state()

TOTAL_EDGES = total_possible_edges()

# ---------------- Top row: Restart | Title | Scores ----------------
c_left, c_mid, c_right = st.columns([1, 2, 1])

with c_left:
    if st.button("🔁 Restart Game", use_container_width=True):
        init_state()
        st.rerun()

with c_mid:
    st.markdown("<h1>Connect Dots Game 👾</h1>", unsafe_allow_html=True)
    st.caption("Click two adjacent dots to draw a line. If you close at least one rectangle, you play again.")

with c_right:
    st.markdown("### Scores")
    st.write(f"🟣 **P1**: {st.session_state.scores[1]}")
    st.write(f"🟧 **P2**: {st.session_state.scores[2]}")

# Turn banner
turn_color = "#800080" if st.session_state.current_player == 1 else "#ffa500"
turn_text  = "Player 1's Turn" if st.session_state.current_player == 1 else "Player 2's Turn"
st.markdown(f"<h3 style='text-align:center;color:{turn_color};'>{turn_text}</h3>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- Game logic ----------------
def try_add_line(p, q):
    if not is_adjacent(p, q):
        st.toast("Dots must be orthogonally adjacent.", icon="⚠️")
        return
    e = canonical_edge(p, q)
    if e in st.session_state.edges:
        st.toast("This line is already drawn.", icon="⚠️")
        return

    st.session_state.edges.add(e)

    candidate_cells = affected_cells_by_edge(p, q)
    newly_closed = set()
    for (rr, cc) in candidate_cells:
        if (rr, cc) in st.session_state.claimed:
            continue
        if all(ed in st.session_state.edges for ed in cell_edges_of(rr, cc)):
            newly_closed.add((rr, cc))

    gained = 0
    if newly_closed:
        comps = bfs_components(newly_closed)
        gained = len(comps)
        for cell in newly_closed:
            st.session_state.claimed[cell] = st.session_state.current_player
        st.session_state.scores[st.session_state.current_player] += gained
        st.toast(f"Closed {gained} area(s)! You play again.", icon="✅")
    else:
        st.session_state.current_player = 2 if st.session_state.current_player == 1 else 1

    if len(st.session_state.edges) == TOTAL_EDGES:
        st.session_state.game_over = True

# ---------------- Figure (with bigger spacing & less chrome) ----------------
xs, ys, texts = [], [], []
for r in range(ROWS):
    for c in range(COLS):
        xs.append(c * SPACING)
        ys.append(-r * SPACING)
        texts.append(f"({r},{c})")

fig = go.Figure()

# Dots (clickable)
fig.add_trace(go.Scatter(
    x=xs, y=ys, mode='markers',
    marker=dict(size=DOT_SIZE, color=DOT_COLOR),
    hoverinfo='text', text=texts, showlegend=False
))

# Filled cells
for (rr, cc), owner in st.session_state.claimed.items():
    x0, x1 = cc*SPACING, (cc+1)*SPACING
    y1, y0 = -rr*SPACING, -(rr+1)*SPACING
    fill = P1_FILL if owner == 1 else P2_FILL
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(width=0), fillcolor=fill, layer="below")

# Edges
for e in st.session_state.edges:
    (r1, c1), (r2, c2) = e
    fig.add_shape(type="line",
                  x0=c1*SPACING, y0=-r1*SPACING, x1=c2*SPACING, y1=-r2*SPACING,
                  line=dict(color=LINE_COLOR, width=LINE_WIDTH))

# Highlight first selected dot
if len(st.session_state.selection) == 1:
    (sr, sc) = st.session_state.selection[0]
    fig.add_trace(go.Scatter(
        x=[sc*SPACING], y=[-sr*SPACING], mode="markers",
        marker=dict(size=DOT_SIZE+6, symbol="circle-open", line=dict(width=2)),
        showlegend=False, hoverinfo="skip"
    ))

# Axes & layout (mode bar kapalı)
x_margin = SPACING * 0.6
y_margin = SPACING * 0.6
fig.update_xaxes(visible=False, range=[-x_margin, (COLS-1)*SPACING + x_margin])
fig.update_yaxes(visible=False, range=[-(ROWS-1)*SPACING - y_margin, y_margin], scaleanchor="x", scaleratio=1)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=FIG_HEIGHT, plot_bgcolor="white", clickmode="event+select")

# plotly_events ile render + click yakalama
events = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=FIG_HEIGHT,
    override_width="100%",
    # Çoğu sürümde destekli: modebar'ı gizlemek için
    # (desteklenmiyorsa kaldırılabilir)
)

# Click handling
if not st.session_state.game_over and events:
    evt = events[-1]
    idx = evt.get("pointIndex", None)
    curve = evt.get("curveNumber", None)
    if idx is not None and curve == 0:
        r = idx // COLS
        c = idx % COLS
        clicked = (r, c)
        if len(st.session_state.selection) == 0:
            st.session_state.selection = [clicked]
        else:
            first = st.session_state.selection[0]
            second = clicked
            if first != second:
                try_add_line(first, second)
            st.session_state.selection = []
        st.rerun()

# Winner banner
if st.session_state.game_over:
    if st.session_state.scores[1] > st.session_state.scores[2]:
        st.markdown("<h3 style='text-align:center;color:#800080;'>Player 1 is the Winner!</h3>", unsafe_allow_html=True)
    elif st.session_state.scores[2] > st.session_state.scores[1]:
        st.markdown("<h3 style='text-align:center;color:#ffa500;'>Player 2 is the Winner!</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='text-align:center;'>Draw!</h3>", unsafe_allow_html=True)
