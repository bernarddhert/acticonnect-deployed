"""ActiConnect-thema — oranje brand-kleur + logische multi-color palette.

Kleuren worden semantisch ingezet:
  - **Oranje** : brand, energie, calorieën, hero
  - **Groen** : gezondheid, vitaliteit, beweging, activiteit
  - **Blauw** : verbondenheid, sociaal, slaap (rust)
  - **Amber** : prestaties, punten, beloningen (goud)
  - **Paars** : mentaal welzijn, stress
  - **Rood**  : waarschuwingen / lage scores
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------------------
# Palet — oranje brand + ondersteunende logische kleuren
# ---------------------------------------------------------------------------
# Brand / Energie (oranje)
ORANGE        = "#E8731D"   # hoofdkleur — hero, energie, calorieën
ORANGE_LIGHT  = "#FFA94D"
ORANGE_PALE   = "#FFD4A3"
ORANGE_BG     = "#FFF3E5"
ORANGE_DEEP   = "#B84A0E"

# Gezondheid / Vitaliteit / Beweging (groen)
GREEN         = "#3FA34D"   # vitaliteit, beweging
GREEN_DARK    = "#2D7A3E"   # premium / records
GREEN_PALE    = "#DDF1DD"
GREEN_BG      = "#E8F5E5"

# Verbondenheid / Sociaal / Rust (blauw)
BLUE          = "#2C6FB5"   # connectie, sociaal
BLUE_LIGHT    = "#4A90D9"
BLUE_PALE     = "#DCE8F5"
BLUE_BG       = "#E8F0FA"

# Prestaties / Goud (amber)
AMBER         = "#E0A422"   # achievements, punten
AMBER_BG      = "#FCEFC9"
AMBER_DEEP    = "#A37419"

# Mentaal / Stress (paars)
PURPLE        = "#7B5EA7"
PURPLE_BG     = "#ECE5F5"
PURPLE_DEEP   = "#523F75"

# Warning (rood)
RED           = "#C73E1D"
RED_BG        = "#FCDDD3"

# Neutralen (warm, om met oranje te harmoniëren)
INK           = "#1F1611"   # warm donkerbruin (bijna zwart)
INK_LIGHT     = "#3D2E22"
MUTED         = "#7A6B5C"   # warme muted
BORDER        = "#EAE2D6"   # licht beige
BORDER_DARK   = "#CFC2AC"
SURFACE       = "#FFFFFF"
SURFACE_ALT   = "#FBF7F1"   # heel licht cream

# Plotly categorische kleuren — visueel onderscheidend per metric-categorie
CATEGORICAL = [
    ORANGE,       # primair brand
    GREEN,        # vitaliteit
    BLUE,         # verbondenheid
    AMBER,        # prestaties
    PURPLE,       # mentaal
    GREEN_DARK,   # records
    ORANGE_LIGHT, # licht oranje
    BLUE_LIGHT,   # licht blauw
    "#937860",    # warm bruin
    "#D4AF37",    # goud
]
SEQUENTIAL_BLUE  = ["#DCE8F5", "#A8C3E0", "#6E9DD0", BLUE,  "#143E72"]
SEQUENTIAL_GREEN = ["#DDF1DD", "#A6D9A6", GREEN,    GREEN_DARK, "#1F5A2C"]
SEQUENTIAL_ORANGE = [ORANGE_BG, ORANGE_PALE, ORANGE_LIGHT, ORANGE, ORANGE_DEEP]


# ---------------------------------------------------------------------------
# Plotly-template
# ---------------------------------------------------------------------------
def _build_template() -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, system-ui, sans-serif", color=INK, size=13),
            colorway=CATEGORICAL,
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            margin=dict(l=40, r=20, t=50, b=40),
            xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, ticks="outside",
                       tickcolor=BORDER, showline=False),
            yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, ticks="outside",
                       tickcolor=BORDER, showline=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        bgcolor="rgba(0,0,0,0)"),
            title=dict(font=dict(size=15, color=INK, family="Inter, system-ui, sans-serif"),
                       x=0, xanchor="left"),
            hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font_size=12,
                            font_family="Inter, system-ui, sans-serif"),
        )
    )


pio.templates["acticonnect"] = _build_template()
pio.templates.default = "acticonnect"


# ---------------------------------------------------------------------------
# CSS — logische kleuren per variant, geen gradients
# ---------------------------------------------------------------------------
_CUSTOM_CSS = f"""
<style>
  :root {{
    --ac-orange:     {ORANGE};
    --ac-orange-bg:  {ORANGE_BG};
    --ac-green:      {GREEN};
    --ac-green-dark: {GREEN_DARK};
    --ac-green-bg:   {GREEN_BG};
    --ac-blue:       {BLUE};
    --ac-blue-bg:    {BLUE_BG};
    --ac-amber:      {AMBER};
    --ac-amber-bg:   {AMBER_BG};
    --ac-purple:     {PURPLE};
    --ac-purple-bg:  {PURPLE_BG};
    --ac-red:        {RED};
    --ac-red-bg:     {RED_BG};
    --ac-ink:        {INK};
    --ac-ink-light:  {INK_LIGHT};
    --ac-muted:      {MUTED};
    --ac-border:     {BORDER};
    --ac-surface-alt: {SURFACE_ALT};
  }}

  /* App-achtergrond een hint cream */
  .stApp {{ background-color: {SURFACE_ALT}; }}

  /* Layout */
  .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }}
  h1, h2, h3 {{ color: var(--ac-ink); letter-spacing: -0.01em; }}
  h1 {{ font-weight: 700; }}

  /* ============================================================
     KPI CARDS — solide gekleurd per logische categorie
     ============================================================ */
  .ac-kpi {{
    border-radius: 14px;
    padding: 18px 20px;
    height: 100%;
    border: 1.5px solid transparent;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    position: relative;
    overflow: hidden;
  }}
  .ac-kpi:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(31, 22, 17, 0.10);
  }}
  .ac-kpi .label {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 700;
    margin-bottom: 6px;
  }}
  .ac-kpi .value {{
    font-size: 1.95rem;
    font-weight: 800;
    line-height: 1.05;
    color: var(--ac-ink);
  }}
  .ac-kpi .sub {{
    font-size: 0.78rem;
    margin-top: 8px;
    color: var(--ac-ink-light);
  }}

  /* Oranje - energie, calorieen, brand */
  .ac-kpi.orange {{
    background: {ORANGE_BG};
    border-left: 6px solid {ORANGE};
  }}
  .ac-kpi.orange .label {{ color: {ORANGE_DEEP}; }}

  /* Groen - gezondheid, vitaliteit, beweging */
  .ac-kpi.green {{
    background: {GREEN_BG};
    border-left: 6px solid {GREEN};
  }}
  .ac-kpi.green .label {{ color: {GREEN_DARK}; }}

  /* Blauw - verbondenheid, sociaal */
  .ac-kpi.blue {{
    background: {BLUE_BG};
    border-left: 6px solid {BLUE};
  }}
  .ac-kpi.blue .label {{ color: {BLUE}; }}

  /* Donkergroen - premium, records */
  .ac-kpi.dark {{
    background: {GREEN_PALE};
    border-left: 6px solid {GREEN_DARK};
  }}
  .ac-kpi.dark .label {{ color: {GREEN_DARK}; }}

  /* Amber - prestaties, punten */
  .ac-kpi.amber {{
    background: {AMBER_BG};
    border-left: 6px solid {AMBER};
  }}
  .ac-kpi.amber .label {{ color: {AMBER_DEEP}; }}

  /* Paars - mentaal, stress */
  .ac-kpi.purple {{
    background: {PURPLE_BG};
    border-left: 6px solid {PURPLE};
  }}
  .ac-kpi.purple .label {{ color: {PURPLE_DEEP}; }}

  /* Rood - warning, lage scores */
  .ac-kpi.red {{
    background: {RED_BG};
    border-left: 6px solid {RED};
  }}
  .ac-kpi.red .label {{ color: {RED}; }}

  /* Neutraal (default) */
  .ac-kpi:not(.blue):not(.green):not(.orange):not(.dark):not(.amber):not(.purple):not(.red) {{
    background: #FFFFFF;
    border: 1.5px solid var(--ac-border);
    border-left: 6px solid var(--ac-muted);
  }}

  /* ============================================================
     SECTION HEADER — verticale balk in passende kleur
     ============================================================ */
  .ac-section {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 26px 0 14px 0;
  }}
  .ac-section .bar {{
    width: 5px;
    height: 28px;
    border-radius: 3px;
  }}
  .ac-section h3 {{
    margin: 0;
    font-size: 1.12rem;
    font-weight: 700;
    color: var(--ac-ink);
  }}

  /* ============================================================
     PILLS / CHIPS — solide gekleurd
     ============================================================ */
  .ac-pill {{
    display: inline-block;
    padding: 4px 11px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    background: {SURFACE_ALT};
    color: var(--ac-muted);
    border: 1px solid var(--ac-border);
  }}
  .ac-pill.blue   {{ background: {BLUE};   color: #FFFFFF; border: none; }}
  .ac-pill.green  {{ background: {GREEN};  color: #FFFFFF; border: none; }}
  .ac-pill.orange {{ background: {ORANGE}; color: #FFFFFF; border: none; }}
  .ac-pill.amber  {{ background: {AMBER};  color: {INK};   border: none; }}
  .ac-pill.purple {{ background: {PURPLE}; color: #FFFFFF; border: none; }}
  .ac-pill.red    {{ background: {RED};    color: #FFFFFF; border: none; }}

  /* ============================================================
     ACTIVITY ROWS — linker rand in oranje (brand)
     ============================================================ */
  .ac-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    border: 1px solid var(--ac-border);
    border-radius: 10px;
    margin-bottom: 8px;
    background: #FFFFFF;
    border-left-width: 4px;
    border-left-color: {ORANGE};
  }}
  .ac-row .title {{ font-weight: 700; color: var(--ac-ink); font-size: 0.95rem; }}
  .ac-row .meta  {{ font-size: 0.8rem; color: var(--ac-muted); margin-top: 3px; }}

  /* ============================================================
     HERO — solide oranje (de brand)
     ============================================================ */
  .ac-hero {{
    background: {ORANGE};
    color: #FFFFFF;
    border-radius: 16px;
    padding: 26px 30px;
    margin-bottom: 18px;
    border: 1.5px solid {ORANGE};
    position: relative;
    overflow: hidden;
  }}
  .ac-hero::before {{
    content: "";
    position: absolute;
    top: -40px;
    right: -40px;
    width: 200px;
    height: 200px;
    background: {ORANGE_LIGHT};
    border-radius: 50%;
    opacity: 0.45;
  }}
  .ac-hero::after {{
    content: "";
    position: absolute;
    bottom: -30px;
    right: 80px;
    width: 100px;
    height: 100px;
    background: {AMBER};
    border-radius: 50%;
    opacity: 0.55;
  }}
  .ac-hero h1 {{ color: #FFFFFF; margin: 0 0 6px 0; font-size: 1.85rem; position: relative; z-index: 1; }}
  .ac-hero .sub {{ color: rgba(255,255,255,0.94); font-size: 0.95rem; position: relative; z-index: 1; }}
  .ac-hero .stat-strip {{
    display: flex; gap: 28px; margin-top: 18px; flex-wrap: wrap;
    position: relative; z-index: 1;
  }}
  .ac-hero .stat-strip .item .v {{ font-size: 1.45rem; font-weight: 800; color: #FFFFFF; }}
  .ac-hero .stat-strip .item .l {{
    font-size: 0.72rem;
    color: rgba(255,255,255,0.88);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
  }}

  /* ============================================================
     CALLOUT
     ============================================================ */
  .ac-callout {{
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 18px;
    color: var(--ac-ink);
    font-size: 0.92rem;
    border-left: 5px solid;
  }}
  .ac-callout.green  {{ background: {GREEN_BG};  border-left-color: {GREEN_DARK}; }}
  .ac-callout.blue   {{ background: {BLUE_BG};   border-left-color: {BLUE}; }}
  .ac-callout.orange {{ background: {ORANGE_BG}; border-left-color: {ORANGE}; }}
  .ac-callout.purple {{ background: {PURPLE_BG}; border-left-color: {PURPLE}; }}

  /* ============================================================
     TABS — actief tab krijgt oranje highlight (brand)
     ============================================================ */
  div[data-baseweb="tab-list"] {{
    border-bottom: 2px solid {BORDER};
    gap: 4px;
  }}
  button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--ac-muted) !important;
    font-weight: 600 !important;
    padding: 10px 16px !important;
    border-radius: 8px 8px 0 0 !important;
  }}
  button[data-baseweb="tab"][aria-selected="true"] {{
    background: {ORANGE_BG} !important;
    color: {ORANGE_DEEP} !important;
  }}
  div[data-baseweb="tab-highlight"] {{ background-color: {ORANGE} !important; height: 3px !important; }}

  /* ============================================================
     SIDEBAR
     ============================================================ */
  section[data-testid="stSidebar"] {{
    background: {SURFACE_ALT};
    border-right: 1px solid {BORDER};
  }}
  section[data-testid="stSidebar"] .stSelectbox label {{
    font-weight: 700;
    color: var(--ac-ink);
  }}

  /* ============================================================
     Data tables
     ============================================================ */
  div[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}

  /* ============================================================
     Mobiel (≤ 640 px): KPI-cards, gauges en titels compacter
     ============================================================ */
  @media (max-width: 640px) {{
    .ac-kpi {{
      padding: 12px 10px !important;
      min-height: unset !important;
    }}
    .ac-kpi .value {{
      font-size: 1.4rem !important;
    }}
    .ac-kpi .label {{
      font-size: 0.68rem !important;
      letter-spacing: 0.04em !important;
    }}
    .ac-kpi .sub {{
      font-size: 0.72rem !important;
    }}

    /* Hero-banner stats kleiner */
    .ac-hero .ac-hero-stat-value {{ font-size: 1.1rem !important; }}
    .ac-hero .ac-hero-stat-label {{ font-size: 0.65rem !important; }}
    .ac-hero h1 {{ font-size: 1.4rem !important; }}

    /* Section-headers kleiner */
    .ac-section-header {{ font-size: 1.05rem !important; }}

    /* Plotly gauges en charts: extra padding eraf */
    div[data-testid="stPlotlyChart"] {{ margin: 0 -8px; }}

    /* Tabel-rijen iets compacter */
    .ac-row {{ padding: 10px 12px !important; }}
    .ac-row .title {{ font-size: 0.85rem !important; }}
    .ac-row .meta {{ font-size: 0.72rem !important; }}

    /* DataFrame: kleine lettergrootte zodat meer past */
    div[data-testid="stDataFrame"] {{ font-size: 0.78rem !important; }}
  }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)
