"""ActiConnect — Persoonlijk Medewerkers-dashboard.

Gestructureerd rondom de drie pijlers uit het bedrijfsadvies:
    Vitaliteit · Verbondenheid · Activiteit

Starten vanuit de streamlit_app/ map:

    streamlit run app.py
"""

from __future__ import annotations

import html
import hashlib
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap voor Streamlit Community Cloud
# ---------------------------------------------------------------------------
# Op cloud-deploy bestaat acticonnect.db nog niet (te groot voor git).
# Bouw hem eenmalig op vanuit de meegeleverde CSV's voordat de app start.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DB_FILE = _REPO_ROOT / "acticonnect.db"
if not _DB_FILE.exists():
    subprocess.run(
        [sys.executable, "load_to_sqlite.py"],
        cwd=str(_REPO_ROOT),
        check=True,
    )

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import db, theme
from utils.components import hero, kpi_card, page_setup, section_header

# Behandel 2026-05-04 als "vandaag" — de laatste dag van de gesimuleerde dataset.
TODAY = pd.Timestamp("2026-05-04")
DAGEN_KORT = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
MAANDEN_KORT = ["jan", "feb", "mrt", "apr", "mei", "jun",
                "jul", "aug", "sep", "okt", "nov", "dec"]

AVATAR_PALET = [theme.BLUE, theme.GREEN, theme.ORANGE, theme.GREEN_DARK,
                theme.BLUE_LIGHT, "#8172B2", "#C44E52", "#937860"]


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
employee_id = page_setup("Mijn Dashboard")
if employee_id is None:
    st.stop()

emp        = db.get_employee(employee_id)
kpis       = db.personal_kpis(employee_id)
goals      = db.goal_progress(employee_id)
social     = db.social_summary(employee_id)
vit        = db.vitality_score(employee_id)
con        = db.connection_score(employee_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _f(v, default="—", fmt=None):
    if v is None or (isinstance(v, float) and (pd.isna(v) or np.isnan(v))):
        return default
    if fmt:
        try:
            return fmt.format(v)
        except (ValueError, TypeError):
            return default
    return v


def _delta_html(curr, prev) -> str:
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev) or prev == 0:
        return "vergeleken met vorige periode"
    diff = curr - prev
    pct = abs(diff / prev * 100)
    if diff > 0:
        return f"<span style='color:{theme.GREEN_DARK}; font-weight:600;'>▲ {pct:.0f}%</span> t.o.v. vorige periode"
    if diff < 0:
        return f"<span style='color:#C44E52; font-weight:600;'>▼ {pct:.0f}%</span> t.o.v. vorige periode"
    return f"<span style='color:{theme.MUTED};'>→ gelijk</span> t.o.v. vorige periode"


def _format_dutch_date(dt: pd.Timestamp) -> str:
    return f"{dt.day} {MAANDEN_KORT[dt.month-1]}"


def _avatar_html(name: str, size: int = 38) -> str:
    parts = (name or "?").split()
    initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper() if parts else "?"
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) if name else 0
    color = AVATAR_PALET[h % len(AVATAR_PALET)]
    return (
        f'<div style="width:{size}px; height:{size}px; border-radius:50%; '
        f'background:{color}; color:#fff; display:inline-flex; align-items:center; '
        f'justify-content:center; font-weight:700; font-size:{size*0.4:.0f}px; '
        f'flex-shrink:0; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">{html.escape(initials)}</div>'
    )


def _score_color(score: float | None) -> str:
    if score is None or pd.isna(score): return theme.MUTED
    if score >= 75: return theme.GREEN_DARK   # uitstekend
    if score >= 60: return theme.GREEN        # goed
    if score >= 40: return theme.ORANGE       # te verbeteren
    return theme.RED                           # aandacht nodig


def _score_class(score: float | None) -> str:
    """CSS-klasse voor KPI-card op basis van score (0-100)."""
    if score is None or pd.isna(score): return ""
    if score >= 75: return "blue"      # → primair oranje (de energie-kleur)
    if score >= 60: return "dark"      # → burnt deep-oranje
    if score >= 40: return "green"     # → amber/goud
    return "red"                        # → warm warning


def _score_label(score: float | None) -> str:
    if score is None or pd.isna(score): return "—"
    if score >= 75: return "Uitstekend"
    if score >= 60: return "Goed"
    if score >= 40: return "Te verbeteren"
    return "Aandacht nodig"


def _gauge(value: float, title: str, color: str, height: int = 240) -> go.Figure:
    # number_valueformat zorgt dat decimalen netjes worden afgerond (72.5 ipv 72.4999...).
    # Suffix '/ 100' weggelaten en font verkleind zodat de score nooit afgekapt wordt
    # in een smalle kolom (kwam voor bij twee-cijferige + decimaal waarden).
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=value or 0,
        number={"valueformat": ".1f", "font": {"size": 32, "color": theme.INK}},
        gauge={
            "axis":  {"range": [0, 100], "tickwidth": 1, "tickcolor": theme.BORDER},
            "bar":   {"color": color, "thickness": 0.8},
            "bgcolor": theme.SURFACE_ALT,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],   "color": "#FCE7E7"},
                {"range": [40, 60],  "color": theme.ORANGE_PALE},
                {"range": [60, 75],  "color": theme.GREEN_PALE},
                {"range": [75, 100], "color": "#B6E3B6"},
            ],
            "threshold": {"line": {"color": theme.INK, "width": 3}, "thickness": 0.85, "value": value or 0},
        },
        title={"text": f"<b>{title}</b>", "font": {"size": 14, "color": theme.INK}},
    )).update_layout(height=height, margin=dict(t=40, b=20, l=20, r=20))


# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
hero_stats = [
    ("Punten",       _f(kpis.get("total_points"), fmt="{:,.0f}")),
    ("Rang",         f"#{int(kpis['rank_in_org'])}" if kpis.get("rank_in_org") else "—"),
    ("Reeks",        f"{int(kpis.get('streak_weeks') or 0)} wk"),
    ("Prestaties",   _f(kpis.get("achievements_earned"), fmt="{:.0f}")),
    ("Connecties",   _f(social.get("friends"), fmt="{:.0f}")),
    ("Teams",        _f(social.get("teams"),   fmt="{:.0f}")),
]
hero(
    name=f"{emp.get('first_name', '')}",
    subtitle=(
        f"{emp.get('job_role', '')} · {emp.get('dept_name') or 'Geen afdeling'} · "
        f"{emp.get('org_name', '')} · {emp.get('office_city') or '—'}"
    ),
    stats=hero_stats,
)

st.markdown(
    "<div style='color:" + theme.MUTED + "; margin: -10px 0 18px 4px; font-size: 0.92rem;'>"
    "Jouw persoonlijke overzicht van <b style='color:" + theme.GREEN_DARK + "'>vitaliteit</b>, "
    "<b style='color:" + theme.BLUE + "'>verbondenheid</b> en "
    "<b style='color:" + theme.ORANGE + "'>activiteit</b> op het werk.</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# KPI strip — 6 cards: 2 composite scores + 4 standard
# ---------------------------------------------------------------------------
section_header("Jouw ActiConnect-scores", color="orange")

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    # Vitaliteit -> groen (gezondheid)
    score_v = vit.get("score_total")
    st.markdown(
        f"""
        <div class="ac-kpi green">
            <div class="label">Vitaliteit</div>
            <div class="value">{_f(score_v, fmt="{:.0f}")}<span style="font-size:0.9rem; color:{theme.MUTED}; font-weight:500;"> / 100</span></div>
            <div class="sub" style="color:{_score_color(score_v)}; font-weight:700;">{_score_label(score_v)}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with c2:
    # Verbondenheid -> blauw (sociaal)
    score_c = con.get("score_total")
    st.markdown(
        f"""
        <div class="ac-kpi blue">
            <div class="label">Verbondenheid</div>
            <div class="value">{_f(score_c, fmt="{:.0f}")}<span style="font-size:0.9rem; color:{theme.MUTED}; font-weight:500;"> / 100</span></div>
            <div class="sub" style="color:{_score_color(score_c)}; font-weight:700;">{_score_label(score_c)}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with c3:
    # Activiteiten -> oranje (energie/actie)
    delta = _delta_html(kpis.get("attended_30d"), kpis.get("attended_30d_prev"))
    st.markdown(
        f"""
        <div class="ac-kpi orange">
            <div class="label">Activiteiten · 30 dagen</div>
            <div class="value">{_f(kpis.get("attended_30d"), fmt="{:.0f}")}</div>
            <div class="sub">{delta}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with c4:
    # Actieve minuten -> groen (beweging)
    week_min    = kpis.get("active_minutes_week") or 0
    weekly_goal = goals.get("weekly_goal") or 0
    pct         = (week_min / weekly_goal * 100) if weekly_goal else 0
    st.markdown(
        f"""
        <div class="ac-kpi green">
            <div class="label">Actieve min · week</div>
            <div class="value">{_f(week_min, fmt="{:.0f}")}</div>
            <div class="sub">{pct:.0f}% van doel ({int(weekly_goal)} min)</div>
        </div>""",
        unsafe_allow_html=True,
    )

with c5:
    # Calorieen -> oranje (energie/vuur)
    kpi_card(
        "Calorieën · 30 d",
        _f(kpis.get("calories_30d"), fmt="{:,.0f}"),
        sub="kcal verbrand",
        color="orange",
    )

with c6:
    # Rang -> amber (prestatie/goud)
    rank   = kpis.get("rank_in_org")
    org_sz = kpis.get("org_size") or 0
    pctl   = (1 - (rank / org_sz)) * 100 if (rank and org_sz) else None
    sub_lbl = f"beter dan {pctl:.0f}% van {int(org_sz)} collega's" if pctl is not None else f"{int(org_sz)} collega's"
    kpi_card(
        "Rang in organisatie",
        f"#{int(rank)}" if rank else "—",
        sub=sub_lbl,
        color="amber",
    )


# ===========================================================================
# TABS
# ===========================================================================
tab_vitaliteit, tab_verbondenheid, tab_patronen, tab_records = st.tabs([
    "Vitaliteit",
    "Verbondenheid",
    "Mijn sport",
    "Prestaties",
])


# ===========================================================================
# TAB 1 — VITALITEIT
# ===========================================================================
with tab_vitaliteit:
    section_header("Jouw Vitaliteits-score", color="green")
    cv1, cv2 = st.columns([1, 1.3])
    with cv1:
        # Gauge horizontaal centreren binnen de kolom via geneste columns
        _, gauge_box, _ = st.columns([1, 6, 1])
        with gauge_box:
            st.plotly_chart(_gauge(vit.get("score_total") or 0, "Vitaliteit", _score_color(vit.get("score_total"))),
                            use_container_width=True)
    with cv2:
        # Logische kleuren per sub-metric:
        #   Beweging → groen (gezondheid), Energie → oranje (energie),
        #   Slaap → blauw (rust), Stress → paars (mentaal)
        sub_scores = [
            ("Beweging", "green",  vit.get("score_movement"), f"gemiddeld {(vit.get('active_min_avg') or 0):.0f} min/week"),
            ("Energie",  "orange", vit.get("score_energy"),   f"gemiddeld {(vit.get('energy_avg') or 0):.1f} / 10"),
            ("Slaap",    "blue",   vit.get("score_sleep"),    f"gemiddeld {(vit.get('sleep_avg') or 0):.1f} u/nacht"),
            ("Stress",   "purple", vit.get("score_stress"),   f"gemiddeld {(vit.get('stress_avg') or 0):.1f} / 10 (lager = beter)"),
        ]
        for i in range(0, 4, 2):
            cc = st.columns(2)
            for c, (lbl, cls, val, sub) in zip(cc, sub_scores[i:i+2]):
                with c:
                    c.markdown(
                        f"""
                        <div class="ac-kpi {cls}">
                            <div class="label">{lbl}</div>
                            <div class="value" style="font-size:1.5rem;">{(val or 0):.0f}<span style="font-size:0.8rem; color:{theme.MUTED}; font-weight:500;"> / 100</span></div>
                            <div class="sub">{sub}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    # ---------- Trends ----------
    section_header("Gezondheidstrends — wekelijkse metingen", color="blue")
    trends = db.health_trends(employee_id)
    if trends.empty:
        st.info("Nog geen wekelijkse gezondheidsmetingen.")
    else:
        trends["week_start_date"] = pd.to_datetime(trends["week_start_date"])
        trends = trends.sort_values("week_start_date")

        # Energie & stress dual line
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trends["week_start_date"], y=trends["energy"],
                                 name="Energie (1-10)", mode="lines+markers",
                                 line=dict(color=theme.GREEN_DARK, width=2.5),
                                 marker=dict(size=7)))
        fig.add_trace(go.Scatter(x=trends["week_start_date"], y=trends["stress"],
                                 name="Stress (1-10, lager beter)", mode="lines+markers",
                                 line=dict(color="#C44E52", width=2.5, dash="dash"),
                                 marker=dict(size=7)))
        fig.update_layout(height=300, yaxis=dict(range=[0, 10], title="Score"),
                          margin=dict(t=20, b=30), title="Energie vs. stress")
        st.plotly_chart(fig, use_container_width=True)

        # Steps + sleep + RHR row
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            fig = px.line(trends, x="week_start_date", y="steps", title="Dagelijkse stappen",
                          labels={"week_start_date": "", "steps": "Stappen"})
            fig.update_traces(line_color=theme.BLUE, mode="lines+markers")
            fig.update_layout(height=240, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig = px.line(trends, x="week_start_date", y="sleep_hours", title="Slaap (uren)",
                          labels={"week_start_date": "", "sleep_hours": "Uren"})
            fig.update_traces(line_color=theme.ORANGE, mode="lines+markers")
            fig.update_layout(height=240, margin=dict(t=40, b=20),
                              yaxis=dict(range=[0, 10]))
            st.plotly_chart(fig, use_container_width=True)
        with col_c:
            fig = px.line(trends, x="week_start_date", y="resting_hr", title="Rusthartslag (bpm)",
                          labels={"week_start_date": "", "resting_hr": "bpm"})
            fig.update_traces(line_color="#8172B2", mode="lines+markers")
            fig.update_layout(height=240, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # ---------- Vergelijking met organisatie ----------
    section_header("Snel inzicht — verschil t.o.v. organisatie", color="dark")
    cmp = db.org_comparison(employee_id)
    if cmp.empty:
        st.info("Nog niet genoeg data voor een vergelijking.")
    else:
        diff_cols = st.columns(len(cmp))
        for col, (_, row) in zip(diff_cols, cmp.iterrows()):
            me_v, org_v = row["me"], row["org"]
            if pd.isna(me_v) or pd.isna(org_v) or org_v == 0:
                col.markdown(
                    f"""<div class="ac-kpi"><div class="label">{html.escape(row['metric'])}</div>
                    <div class="value" style="font-size:1.1rem;">—</div>
                    <div class="sub">geen data</div></div>""",
                    unsafe_allow_html=True)
                continue
            diff_pct = (me_v - org_v) / org_v * 100
            # Voor stress: lager is beter — kleur omdraaien
            inverted = "stress" in row["metric"].lower()
            beter_dan_org = (diff_pct < 0) if inverted else (diff_pct > 0)
            cls = "green" if beter_dan_org else ("red" if abs(diff_pct) >= 10 else "amber")
            arrow = "▲" if diff_pct > 0 else ("▼" if diff_pct < 0 else "→")
            col.markdown(
                f"""
                <div class="ac-kpi {cls}">
                    <div class="label">{html.escape(row['metric'])}</div>
                    <div class="value" style="font-size:1.2rem;">{me_v:,.1f}</div>
                    <div class="sub" style="font-weight:700;">
                        {arrow} {abs(diff_pct):.0f}% vs. org ({org_v:,.1f})
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )


# ===========================================================================
# TAB 4 — VERBONDENHEID (NIEUW — kernpijler ActiConnect)
# ===========================================================================
with tab_verbondenheid:
    section_header("Jouw Verbondenheids-score", color="blue")
    cc1, cc2 = st.columns([1, 1.3])
    with cc1:
        # Gauge horizontaal centreren binnen de kolom via geneste columns
        _, gauge_box, _ = st.columns([1, 6, 1])
        with gauge_box:
            st.plotly_chart(_gauge(con.get("score_total") or 0, "Verbondenheid", _score_color(con.get("score_total"))),
                            use_container_width=True)
    with cc2:
        # Logische kleuren:
        #   Sociale connectie → blauw (sociaal),  Trainingspartners → groen (samen actief),
        #   Connecties → blauw,  Teams → oranje (groepsenergie)
        sub_scores = [
            ("Sociale connectie", "blue",   con.get("score_social"),
             f"gem. {(con.get('social_avg') or 0):.1f}/5 in feedback"),
            ("Trainingspartners", "green",  con.get("score_partners"),
             f"{int(con.get('unique_partners') or 0)} unieke collega's"),
            ("Connecties",        "blue",   con.get("score_friends"),
             f"{int(con.get('friends') or 0)} vrienden"),
            ("Teams",             "orange", con.get("score_teams"),
             f"{int(con.get('teams') or 0)} teams"),
        ]
        for i in range(0, 4, 2):
            cc = st.columns(2)
            for c, (lbl, cls, val, sub) in zip(cc, sub_scores[i:i+2]):
                with c:
                    c.markdown(
                        f"""
                        <div class="ac-kpi {cls}">
                            <div class="label">{lbl}</div>
                            <div class="value" style="font-size:1.5rem;">{(val or 0):.0f}<span style="font-size:0.8rem; color:{theme.MUTED}; font-weight:500;"> / 100</span></div>
                            <div class="sub">{sub}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    # ---------- Trainingspartners (key insight) ----------
    section_header("Met wie sport je het vaakst?", color="blue")
    partners = db.training_partners(employee_id, limit=10)
    if partners.empty:
        st.info("Nog niet samen met collega's gesport.")
    else:
        rows_html = []
        max_sessies = int(partners["sessies_samen"].max())
        for _, p in partners.iterrows():
            naam = p.get("naam") or "—"
            role = p.get("job_role") or ""
            dept = p.get("dept_name") or "—"
            sessies = int(p.get("sessies_samen") or 0)
            sporten = int(p.get("verschillende_sporten") or 0)
            bar_pct = (sessies / max_sessies * 100) if max_sessies else 0
            rows_html.append(f"""
                <div class="ac-row">
                    <div style="display:flex; align-items:center; gap:12px; flex:1;">
                        {_avatar_html(naam, 38)}
                        <div>
                            <div class="title">{html.escape(naam)}</div>
                            <div class="meta">{html.escape(role)} · {html.escape(dept)}</div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="width:120px; height:8px; background:{theme.SURFACE_ALT}; border-radius:4px;">
                            <div style="width:{bar_pct}%; height:100%; background:{theme.BLUE}; border-radius:4px;"></div>
                        </div>
                        <div style="text-align:right; min-width:90px;">
                            <div style="font-weight:700; color:{theme.INK};">{sessies}× samen</div>
                            <div style="font-size:0.72rem; color:{theme.MUTED};">{sporten} sporten</div>
                        </div>
                    </div>
                </div>
            """)
        st.markdown("".join(rows_html), unsafe_allow_html=True)

    # ---------- Sociale connectie trend ----------
    section_header("Sociale-verbondenheid trend", color="blue")
    sc = db.social_connection_trend(employee_id)
    if sc.empty or len(sc) < 2:
        st.info("Niet genoeg feedback om een trend te tonen.")
    else:
        sc["week_start"] = pd.to_datetime(sc["week_start"])
        sc = sc.sort_values("week_start")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sc["week_start"], y=sc["social"],
                                 name="Sociale connectie (1-5)", mode="lines+markers",
                                 line=dict(color=theme.BLUE, width=2.5),
                                 marker=dict(size=7)))
        fig.update_layout(height=320, margin=dict(t=20, b=30),
                          yaxis=dict(title="Score (1-5)", range=[0, 5]),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ---------- Verbondenheid per sport ----------
    section_header("Bij welke sport voel je je het meest verbonden?", color="blue")
    cps = db.connection_per_sport(employee_id)
    if cps.empty:
        st.info("Nog niet genoeg feedback per sport om dit te laten zien. "
                "Vul feedback in na minstens 2 activiteiten per sport.")
    else:
        fig = go.Figure(go.Bar(
            x=cps["gem_verbondenheid"],
            y=cps["sport"],
            orientation="h",
            marker_color=theme.BLUE,
            text=[f"{v:.1f}" for v in cps["gem_verbondenheid"]],
            textposition="outside",
            textfont=dict(size=12, color=theme.INK),
            customdata=cps["aantal_feedbacks"],
            hovertemplate="<b>%{y}</b><br>Gemiddelde verbondenheid: %{x:.2f}/5"
                          "<br>Gebaseerd op %{customdata} feedbacks<extra></extra>",
        ))
        fig.update_layout(
            height=max(260, 50 * len(cps) + 80),
            xaxis=dict(title="Gemiddelde verbondenheid (1-5)", range=[0, 5.5]),
            yaxis=dict(autorange="reversed"),
            margin=dict(t=40, b=40, l=20, r=60),
            bargap=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# TAB 3 — MIJN SPORT
# ===========================================================================
with tab_patronen:
    # ---------- Sport categorieën ----------
    section_header("Sport-categorieën — diversificatie", color="orange")
    cats = db.category_breakdown(employee_id)
    if cats.empty:
        st.info("Nog geen activiteiten.")
    else:
        cat_nl = {"Cardio": "Cardio", "Strength": "Kracht", "Mind": "Mind", "Racket": "Racket",
                  "Team": "Team", "Water": "Water", "Outdoor": "Buiten"}
        cats["category_nl"] = cats["category"].map(cat_nl).fillna(cats["category"])

        cat1, cat2 = st.columns([1, 1.3])
        with cat1:
            fig = px.pie(cats, names="category_nl", values="sessies", hole=0.55,
                         color_discrete_sequence=theme.CATEGORICAL)
            fig.update_traces(textposition="inside", textinfo="label+percent",
                              hovertemplate="<b>%{label}</b><br>%{value} sessies<extra></extra>")
            fig.update_layout(height=300, margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with cat2:
            disp = cats[["category_nl", "sessies", "totaal_min", "totaal_kcal"]].copy()
            disp.columns = ["Categorie", "Sessies", "Totaal min", "Totaal kcal"]
            st.dataframe(disp, use_container_width=True, hide_index=True,
                         column_config={
                             "Sessies":     st.column_config.ProgressColumn(format="%d", min_value=0,
                                                                            max_value=int(disp["Sessies"].max())),
                             "Totaal min":  st.column_config.NumberColumn(format="%d"),
                             "Totaal kcal": st.column_config.NumberColumn(format="%d"),
                         })

    # ---------- Sport breakdown ----------
    sports = db.sport_breakdown(employee_id)
    if not sports.empty:
        section_header("Sport-overzicht", color="blue")
        disp = sports.copy()
        disp["avg_duration_min"] = disp["avg_duration_min"].round(0)
        disp["total_calories"]   = disp["total_calories"].astype(int)
        disp.columns = ["Sport", "Categorie", "Sessies", "Gem. duur (min)", "Totaal kcal"]
        st.dataframe(disp, use_container_width=True, hide_index=True, height=320,
                     column_config={
                         "Sessies": st.column_config.ProgressColumn("Sessies", format="%d",
                             min_value=0, max_value=int(disp["Sessies"].max())),
                         "Totaal kcal": st.column_config.NumberColumn("Totaal kcal", format="%d"),
                     })

    # ---------- Wanneer train je ----------
    section_header("Wanneer train je?", color="green")
    pat1, pat2, pat3 = st.columns([1.1, 1.1, 1])
    with pat1:
        hod = db.hour_of_day_pattern(employee_id)
        all_hours = pd.DataFrame({"hour": range(0, 24)})
        hod = all_hours.merge(hod, on="hour", how="left").fillna(0)
        fig = px.bar(hod, x="hour", y="attended_count", title="Per uur van de dag",
                     labels={"hour": "Uur", "attended_count": "Sessies"})
        fig.update_traces(marker_color=theme.BLUE,
                          hovertemplate="%{x}:00<br>%{y:.0f} sessies<extra></extra>")
        fig.update_layout(height=260, margin=dict(t=40, b=30), showlegend=False)
        fig.update_xaxes(dtick=2)
        st.plotly_chart(fig, use_container_width=True)
    with pat2:
        dow = db.day_of_week_pattern(employee_id)
        all_dow = pd.DataFrame({"dow": range(0, 7)})
        dow = all_dow.merge(dow, on="dow", how="left").fillna(0)
        # SQLite strftime('%w') = 0=Zo..6=Za → omzetten naar Ma-Zo
        dow_map = {0: "Zo", 1: "Ma", 2: "Di", 3: "Wo", 4: "Do", 5: "Vr", 6: "Za"}
        dow["dow_name"] = dow["dow"].map(dow_map)
        order = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
        dow["dow_name"] = pd.Categorical(dow["dow_name"], categories=order, ordered=True)
        dow = dow.sort_values("dow_name")
        weekend_mask = dow["dow_name"].isin(["Za", "Zo"])
        fig = px.bar(dow, x="dow_name", y="attended_count", title="Per dag van de week",
                     labels={"dow_name": "", "attended_count": "Sessies"})
        fig.update_traces(marker_color=[theme.ORANGE if w else theme.GREEN for w in weekend_mask],
                          hovertemplate="%{x}<br>%{y:.0f} sessies<extra></extra>")
        fig.update_layout(height=260, margin=dict(t=40, b=30), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with pat3:
        io = db.indoor_outdoor_split(employee_id)
        if not io.empty:
            fig = px.pie(io, names="setting", values="sessies", title="Binnen vs. buiten",
                         hole=0.5, color_discrete_sequence=[theme.BLUE_LIGHT, theme.GREEN])
            fig.update_layout(height=260, margin=dict(t=40, b=20), showlegend=True,
                              legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig, use_container_width=True)

    # ---------- Top venues ----------
    section_header("Favoriete locaties", color="orange")
    venues = db.top_venues(employee_id, limit=8)
    if venues.empty:
        st.info("Nog geen locatie-data.")
    else:
        venues = venues.copy()
        venues["Setting"] = venues["indoor"].map({1: "Binnen", 0: "Buiten"})
        disp = venues[["name", "city", "venue_type", "Setting", "rating", "visits"]]
        disp.columns = ["Locatie", "Stad", "Type", "Setting", "Rating", "Bezoeken"]
        st.dataframe(disp, use_container_width=True, hide_index=True,
                     column_config={
                         "Rating":   st.column_config.NumberColumn(format="%.1f"),
                         "Bezoeken": st.column_config.ProgressColumn(format="%d", min_value=0,
                                                                      max_value=int(disp["Bezoeken"].max())),
                     })


# ===========================================================================
# TAB 4 — PRESTATIES
# ===========================================================================
with tab_records:
    # ---------- Prestaties galerij ----------
    section_header("Prestatie-galerij", color="amber")
    all_ach = db.all_achievements(employee_id)
    if all_ach.empty:
        st.info("Nog geen prestaties beschikbaar.")
    else:
        tier_styles = {
            "brons":   ("#FBE7CF", "#A85B16", "#CD7F32"),
            "zilver":  ("#EDEDED", "#5C5C5C", "#A8A8A8"),
            "goud":    ("#FBF1CC", "#7A5E0E", "#D4AF37"),
            "platina": ("#D8F1F5", "#236A78", "#5BC0DE"),
        }
        tier_nl = {"brons": "Brons", "zilver": "Zilver", "goud": "Goud", "platina": "Platina"}
        for i in range(0, len(all_ach), 4):
            cols = st.columns(4)
            for col, (_, row) in zip(cols, all_ach.iloc[i:i+4].iterrows()):
                tier = (row.get("tier") or "").lower()
                bg, label_clr, border_clr = tier_styles.get(tier, (theme.BLUE_BG, theme.BLUE, theme.BLUE))
                earned = bool(row["earned"])
                if not earned:
                    bg = "#F1F5F9"
                    label_clr = theme.MUTED
                    border_clr = theme.BORDER_DARK
                opacity = "1" if earned else "0.65"
                badge = "[behaald]" if earned else "[nog niet]"
                date_line = (
                    f"<em>Behaald op {_format_dutch_date(pd.to_datetime(row['earned_date']))} "
                    f"{pd.to_datetime(row['earned_date']).year}</em>"
                    if earned and pd.notna(row.get("earned_date")) else
                    "<em>Nog niet behaald</em>"
                )
                col.markdown(
                    f"""
                    <div class="ac-kpi" style="background:{bg}; border-left: 6px solid {border_clr}; opacity:{opacity}; min-height:140px;">
                        <div class="label" style="color:{label_clr};">{badge} {tier_nl.get(tier, 'Tier')} · {int(row['points'])} pt</div>
                        <div class="value" style="font-size:1rem;">{html.escape(str(row['name']))}</div>
                        <div class="sub">{html.escape(str(row['description']))}<br>{date_line}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )


