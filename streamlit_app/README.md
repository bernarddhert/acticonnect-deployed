# ActiConnect — Employee Dashboard

A Streamlit dashboard built on top of `acticonnect.db`, designed for **individual
employees** to explore their own activity, health, achievements and social stats.

## Run it

From the project root (one level above this folder):

```bash
# 1. Make sure the SQLite DB exists
python load_to_sqlite.py

# 2. Install dashboard dependencies
pip install -r streamlit_app/requirements.txt

# 3. Launch
cd streamlit_app
streamlit run app.py
```

Then open <http://localhost:8501>.

## Structure

```
streamlit_app/
├── app.py                  # Home / personal dashboard
├── pages/                  # Additional pages (added incrementally)
├── utils/
│   ├── db.py               # Cached SQLite queries
│   ├── theme.py            # Logo-derived palette + plotly template + CSS
│   └── components.py       # KPI cards, hero, employee selector
├── .streamlit/config.toml  # Theme + server settings
├── requirements.txt
└── README.md
```

## Theme

Colours come from the ActiConnect logo:

| Token | Hex | Where it appears |
|---|---|---|
| `BLUE` | `#1E5BA8` | Primary — KPIs, links, charts |
| `GREEN` | `#5CB85C` | Activity / attendance |
| `GREEN_DARK` | `#2D7A3E` | Achievements, success states |
| `ORANGE` | `#F4A04F` | Energy / accents |

## Roadmap

- [x] Home (personal KPIs, weekly rhythm, recent + upcoming activities, achievements)
- [ ] My Activities (history, calendar heatmap, sport breakdown)
- [ ] My Health (steps, sleep, stress, energy, body metrics, comparison to org)
- [ ] Achievements & Leaderboard (full grid, rank-over-time)
- [ ] Challenges (active progress, completed, joinable)
- [ ] Social (friends, teams, joint activity feed)
- [ ] Insights (personal records, trends, peer comparisons)
