# Connect Dots Game 👾 (Streamlit)

Interactive two-player “dots–lines–rectangles” game built with **Streamlit** + **Plotly**.
Players click two adjacent dots to draw a green line. If the new line closes at least one rectangle,
the same player immediately gets another turn. Closed rectangles are filled **purple (P1)** or **orange (P2)**.
Winner is the player with **more closed areas** when all lines are drawn.

## Demo (Local)
```bash
# 1) Create & activate a virtualenv (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run
streamlit run streamlit_app.py
