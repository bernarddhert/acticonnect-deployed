"""Reusable UI components."""

from __future__ import annotations

import html
from typing import Literal

import streamlit as st

from utils import db, theme

KpiColor = Literal["blue", "green", "orange", "dark", "amber", "purple", "red"]


# ---------------------------------------------------------------------------
# Cards / chrome
# ---------------------------------------------------------------------------
def kpi_card(label: str, value: str | int | float, sub: str = "", color: KpiColor = "blue") -> None:
    st.markdown(
        f"""
        <div class="ac-kpi {color}">
            <div class="label">{html.escape(label)}</div>
            <div class="value">{html.escape(str(value))}</div>
            <div class="sub">{html.escape(sub) if sub else "&nbsp;"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, color: KpiColor = "blue") -> None:
    color_map = {
        "blue":   theme.BLUE,
        "green":  theme.GREEN,
        "orange": theme.ORANGE,
        "dark":   theme.GREEN_DARK,
        "amber":  theme.AMBER,
        "purple": theme.PURPLE,
        "red":    theme.RED,
    }
    bar = color_map[color]
    st.markdown(
        f"""
        <div class="ac-section">
            <span class="bar" style="background:{bar};"></span>
            <h3>{html.escape(title)}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(name: str, subtitle: str, stats: list[tuple[str, str]]) -> None:
    items = "".join(
        f'<div class="item"><div class="v">{html.escape(v)}</div>'
        f'<div class="l">{html.escape(l)}</div></div>'
        for l, v in stats
    )
    st.markdown(
        f"""
        <div class="ac-hero">
            <h1>Hi, {html.escape(name)}</h1>
            <div class="sub">{html.escape(subtitle)}</div>
            <div class="stat-strip">{items}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, color: Literal["blue", "green", "orange", "muted"] = "muted") -> str:
    cls = "" if color == "muted" else color
    return f'<span class="ac-pill {cls}">{html.escape(text)}</span>'


# ---------------------------------------------------------------------------
# Employee selector — used on every page via the sidebar
# ---------------------------------------------------------------------------
def employee_selector() -> int | None:
    """Render the org → employee picker in the sidebar.

    Returns the chosen employee_id, persisted across pages via session_state.
    """
    st.sidebar.markdown("### Bekijk als medewerker")

    orgs = db.list_organisations()
    org_options = ["Alle organisaties"] + orgs["org_name"].tolist()

    default_org_idx = st.session_state.get("ac_org_idx", 0)
    org_choice = st.sidebar.selectbox(
        "Organisatie",
        org_options,
        index=default_org_idx,
        key="ac_org_select",
    )
    st.session_state["ac_org_idx"] = org_options.index(org_choice)

    org_id = None
    if org_choice != "Alle organisaties":
        org_id = int(orgs.loc[orgs["org_name"] == org_choice, "org_id"].iloc[0])

    employees = db.list_employees(org_id)
    if employees.empty:
        st.sidebar.warning("Geen medewerkers in deze organisatie.")
        return None

    employees = employees.assign(
        display=lambda d: d["first_name"] + " " + d["last_name"]
                          + " — " + d["job_role"].fillna("")
    )

    prev_id = st.session_state.get("ac_employee_id")
    if prev_id in set(employees["employee_id"].tolist()):
        default_idx = int(employees.index[employees["employee_id"] == prev_id][0])
    else:
        default_idx = 0

    chosen_display = st.sidebar.selectbox(
        "Medewerker",
        employees["display"].tolist(),
        index=default_idx,
        key="ac_employee_select",
    )
    chosen_row = employees.loc[employees["display"] == chosen_display].iloc[0]
    employee_id = int(chosen_row["employee_id"])
    st.session_state["ac_employee_id"] = employee_id

    st.sidebar.caption(
        f"{chosen_row['org_name']}  ·  {chosen_row['dept_name'] or '—'}"
    )

    st.sidebar.divider()
    st.sidebar.caption("Wissel hier op elk moment van medewerker. Het hele dashboard wordt direct bijgewerkt.")

    return employee_id


# ---------------------------------------------------------------------------
# Page bootstrap — run at the top of every page script
# ---------------------------------------------------------------------------
def page_setup(page_title: str, icon: str | None = None) -> int | None:
    """Set page config, inject CSS, render employee selector.

    Returns the active employee_id (or None if no employees exist).
    """
    st.set_page_config(
        page_title=f"{page_title} · ActiConnect",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    theme.inject_css()
    return employee_selector()
