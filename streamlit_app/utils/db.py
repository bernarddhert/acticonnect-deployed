"""SQLite-toegangslaag met gecachete read-only queries (Nederlandstalig schema)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[2] / "acticonnect.db"

# Dataset eindigt op 2026-05-04 — behandel als "vandaag".
VANDAAG_SQL = "'2026-05-04'"
VANDAAG_TS = pd.Timestamp("2026-05-04")


@st.cache_resource(show_spinner=False)
def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Kon {DB_PATH} niet vinden. Voer eerst `python load_to_sqlite.py` uit."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(show_spinner=False, ttl=3600)
def query(sql: str, params: tuple | dict | None = None) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(sql, conn, params=params or ())


# ===========================================================================
# Lookup-tabellen
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def list_organisations() -> pd.DataFrame:
    return query("""
        SELECT organisatie_id AS org_id, organisatie_naam AS org_name
        FROM organisaties ORDER BY organisatie_naam
    """)


@st.cache_data(show_spinner=False, ttl=3600)
def list_employees(org_id: int | None = None) -> pd.DataFrame:
    base = """
        SELECT m.medewerker_id AS employee_id,
               m.voornaam      AS first_name,
               m.achternaam    AS last_name,
               m.email,
               m.organisatie_id AS org_id,
               o.organisatie_naam AS org_name,
               a.afdeling_naam   AS dept_name,
               m.functie         AS job_role
        FROM medewerkers m
        JOIN organisaties o ON o.organisatie_id = m.organisatie_id
        LEFT JOIN afdelingen a ON a.afdeling_id = m.afdeling_id
    """
    if org_id is None:
        return query(base + " ORDER BY m.voornaam, m.achternaam")
    return query(base + " WHERE m.organisatie_id = ? ORDER BY m.voornaam, m.achternaam",
                 (int(org_id),))


@st.cache_data(show_spinner=False, ttl=3600)
def get_employee(employee_id: int) -> dict:
    sql = """
        SELECT m.medewerker_id AS employee_id,
               m.voornaam   AS first_name,
               m.achternaam AS last_name,
               m.email,
               m.geslacht   AS gender,
               m.geboortedatum AS date_of_birth,
               m.functie    AS job_role,
               m.werkwijze  AS work_mode,
               m.indienst_datum AS hire_date,
               m.aanmeld_datum  AS signup_date,
               m.laatste_login  AS last_login_date,
               m.is_actief      AS is_active,
               m.notificatie_voorkeur AS notification_pref,
               m.privacy_niveau       AS privacy_level,
               o.organisatie_naam AS org_name,
               a.afdeling_naam    AS dept_name,
               k.stad             AS office_city,
               p.lengte_cm     AS height_cm,
               p.gewicht_kg    AS weight_kg,
               p.fitness_niveau AS fitness_level,
               p.hoofddoel      AS primary_goal,
               p.weekdoel_minuten AS weekly_goal_minutes,
               p.voorkeurstijd  AS preferred_time,
               p.bio,
               p.profiel_volledig_pct AS profile_completed_pct
        FROM medewerkers m
        JOIN organisaties o ON o.organisatie_id = m.organisatie_id
        LEFT JOIN afdelingen a ON a.afdeling_id = m.afdeling_id
        LEFT JOIN kantoorlocaties k ON k.kantoor_id = m.kantoor_id
        LEFT JOIN medewerker_profielen p ON p.medewerker_id = m.medewerker_id
        WHERE m.medewerker_id = ?
    """
    df = query(sql, (int(employee_id),))
    return df.iloc[0].to_dict() if len(df) else {}


# ===========================================================================
# Headline KPIs
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=600)
def personal_kpis(employee_id: int) -> dict:
    sql = f"""
        WITH med AS (SELECT medewerker_id, organisatie_id FROM medewerkers WHERE medewerker_id = ?),
        bijgewoond AS (
            SELECT COUNT(*) AS n FROM deelnames
            WHERE medewerker_id = ? AND bijgewoond = 1
        ),
        bijgewoond_30 AS (
            SELECT COUNT(*) AS n FROM deelnames d
            JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
            WHERE d.medewerker_id = ? AND d.bijgewoond = 1
              AND a.geplande_tijd >= date({VANDAAG_SQL}, '-30 days')
        ),
        bijgewoond_30_prev AS (
            SELECT COUNT(*) AS n FROM deelnames d
            JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
            WHERE d.medewerker_id = ? AND d.bijgewoond = 1
              AND a.geplande_tijd >= date({VANDAAG_SQL}, '-60 days')
              AND a.geplande_tijd <  date({VANDAAG_SQL}, '-30 days')
        ),
        laatste_dash AS (
            SELECT totaal_punten, rang_in_org, reeks_weken, snapshot_datum
            FROM dashboard_dagelijks
            WHERE medewerker_id = ?
            ORDER BY snapshot_datum DESC LIMIT 1
        ),
        actief_min_week AS (
            SELECT COALESCE(SUM(actieve_minuten_vandaag), 0) AS m
            FROM dashboard_dagelijks
            WHERE medewerker_id = ? AND snapshot_datum >= date({VANDAAG_SQL}, '-7 days')
        ),
        actief_min_prev AS (
            SELECT COALESCE(SUM(actieve_minuten_vandaag), 0) AS m
            FROM dashboard_dagelijks
            WHERE medewerker_id = ?
              AND snapshot_datum >= date({VANDAAG_SQL}, '-14 days')
              AND snapshot_datum <  date({VANDAAG_SQL}, '-7 days')
        ),
        gem_energie AS (
            SELECT AVG(f.energie_na_1tot10) AS e
            FROM feedback f
            JOIN deelnames d ON d.deelname_id = f.deelname_id
            WHERE d.medewerker_id = ?
        ),
        prestaties_n AS (
            SELECT COUNT(*) AS n FROM behaalde_prestaties WHERE medewerker_id = ?
        ),
        kcal_30 AS (
            SELECT COALESCE(SUM(calorieen_vandaag), 0) AS c
            FROM dashboard_dagelijks
            WHERE medewerker_id = ? AND snapshot_datum >= date({VANDAAG_SQL}, '-30 days')
        )
        SELECT
            (SELECT n FROM bijgewoond)        AS total_attended,
            (SELECT n FROM bijgewoond_30)     AS attended_30d,
            (SELECT n FROM bijgewoond_30_prev) AS attended_30d_prev,
            (SELECT totaal_punten FROM laatste_dash) AS total_points,
            (SELECT rang_in_org FROM laatste_dash)   AS rank_in_org,
            (SELECT reeks_weken FROM laatste_dash)   AS streak_weeks,
            (SELECT m FROM actief_min_week)          AS active_minutes_week,
            (SELECT m FROM actief_min_prev)          AS active_minutes_prev,
            (SELECT e FROM gem_energie)              AS avg_energy_after,
            (SELECT n FROM prestaties_n)             AS achievements_earned,
            (SELECT c FROM kcal_30)                  AS calories_30d,
            (SELECT COUNT(*) FROM medewerkers
             WHERE organisatie_id = (SELECT organisatie_id FROM med)) AS org_size
    """
    eid = int(employee_id)
    df = query(sql, (eid, eid, eid, eid, eid, eid, eid, eid, eid, eid))
    return df.iloc[0].to_dict() if len(df) else {}


# ===========================================================================
# Tijdspatronen
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=600)
def hour_of_day_pattern(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT CAST(strftime('%H', a.geplande_tijd) AS INTEGER) AS hour,
               COUNT(*) AS attended_count
        FROM deelnames d
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        WHERE d.medewerker_id = ? AND d.bijgewoond = 1
        GROUP BY hour
        ORDER BY hour
    """
    return query(sql, (int(employee_id),))


@st.cache_data(show_spinner=False, ttl=600)
def day_of_week_pattern(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT CAST(strftime('%w', a.geplande_tijd) AS INTEGER) AS dow,
               COUNT(*) AS attended_count,
               COALESCE(SUM(aw.werkelijke_duur_min), 0) AS total_minutes
        FROM deelnames d
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        LEFT JOIN aanwezigheid aw ON aw.deelname_id = d.deelname_id
        WHERE d.medewerker_id = ? AND d.bijgewoond = 1
        GROUP BY dow
        ORDER BY dow
    """
    return query(sql, (int(employee_id),))


# ===========================================================================
# Sport / locatie breakdown
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=600)
def sport_breakdown(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT sc.sport_naam AS sport_name,
               sc.categorie  AS category,
               COUNT(*) AS times,
               AVG(aw.werkelijke_duur_min) AS avg_duration_min,
               COALESCE(SUM(aw.geschatte_calorieen), 0) AS total_calories
        FROM deelnames d
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        JOIN sportcategorieen sc ON sc.sport_id = a.sport_id
        LEFT JOIN aanwezigheid aw ON aw.deelname_id = d.deelname_id
        WHERE d.medewerker_id = ? AND d.bijgewoond = 1
        GROUP BY sc.sport_id, sc.sport_naam, sc.categorie
        ORDER BY times DESC
    """
    return query(sql, (int(employee_id),))


@st.cache_data(show_spinner=False, ttl=600)
def top_venues(employee_id: int, limit: int = 5) -> pd.DataFrame:
    sql = """
        SELECT l.naam     AS name,
               l.stad     AS city,
               l.locatie_type AS venue_type,
               l.binnen   AS indoor,
               l.beoordeling AS rating,
               COUNT(*)   AS visits
        FROM deelnames d
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        JOIN locaties l ON l.locatie_id = a.locatie_id
        WHERE d.medewerker_id = ? AND d.bijgewoond = 1
        GROUP BY l.locatie_id
        ORDER BY visits DESC
        LIMIT ?
    """
    return query(sql, (int(employee_id), int(limit)))


# ===========================================================================
# Doelen, lichaam, sociaal
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=600)
def goal_progress(employee_id: int) -> dict:
    sql = f"""
        SELECT
            (SELECT weekdoel_minuten FROM medewerker_profielen WHERE medewerker_id = ?) AS weekly_goal,
            (SELECT profiel_volledig_pct FROM medewerker_profielen WHERE medewerker_id = ?) AS profile_pct,
            (SELECT hoofddoel FROM medewerker_profielen WHERE medewerker_id = ?) AS primary_goal,
            (SELECT fitness_niveau FROM medewerker_profielen WHERE medewerker_id = ?) AS fitness_level,
            (SELECT lengte_cm FROM medewerker_profielen WHERE medewerker_id = ?) AS height_cm,
            (SELECT gewicht_kg FROM medewerker_profielen WHERE medewerker_id = ?) AS weight_kg,
            (SELECT voorkeurstijd FROM medewerker_profielen WHERE medewerker_id = ?) AS preferred_time,
            (SELECT COALESCE(SUM(actieve_minuten_vandaag), 0) FROM dashboard_dagelijks
                WHERE medewerker_id = ? AND snapshot_datum >= date({VANDAAG_SQL}, '-7 days')) AS week_active_min,
            (SELECT COALESCE(SUM(activiteiten_vandaag), 0) FROM dashboard_dagelijks
                WHERE medewerker_id = ? AND snapshot_datum >= date({VANDAAG_SQL}, 'start of month')) AS month_activities,
            (SELECT reeks_weken FROM dashboard_dagelijks
                WHERE medewerker_id = ? ORDER BY snapshot_datum DESC LIMIT 1) AS current_streak,
            (SELECT MAX(reeks_weken) FROM dashboard_dagelijks WHERE medewerker_id = ?) AS best_streak
    """
    eid = int(employee_id)
    df = query(sql, (eid,) * 11)
    return df.iloc[0].to_dict() if len(df) else {}


@st.cache_data(show_spinner=False, ttl=600)
def social_summary(employee_id: int) -> dict:
    sql = """
        SELECT
            (SELECT COUNT(*) FROM connecties
                WHERE (medewerker_id_a = ? OR medewerker_id_b = ?) AND status = 'geaccepteerd') AS friends,
            (SELECT COUNT(*) FROM team_lidmaatschappen WHERE medewerker_id = ?) AS teams,
            (SELECT COUNT(*) FROM uitdaging_deelnemers
                WHERE medewerker_id = ? AND voltooid = 1) AS challenges_done,
            (SELECT COUNT(*) FROM uitdaging_deelnemers ud
                JOIN uitdagingen u ON u.uitdaging_id = ud.uitdaging_id
                WHERE ud.medewerker_id = ? AND u.status = 'actief') AS active_challenges,
            (SELECT COUNT(*) FROM team_lidmaatschappen WHERE medewerker_id = ? AND rol = 'aanvoerder') AS captain_of
    """
    eid = int(employee_id)
    df = query(sql, (eid, eid, eid, eid, eid, eid))
    return df.iloc[0].to_dict() if len(df) else {}


# ===========================================================================
# Vergelijkingen
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=600)
def org_comparison(employee_id: int) -> pd.DataFrame:
    sql = """
        WITH med AS (
            SELECT medewerker_id, organisatie_id, afdeling_id FROM medewerkers WHERE medewerker_id = ?
        ),
        my_acts AS (
            SELECT COUNT(*) AS n FROM deelnames
            WHERE medewerker_id = ? AND bijgewoond = 1
        ),
        org_acts AS (
            SELECT AVG(c) AS n FROM (
                SELECT COUNT(*) AS c
                FROM deelnames d
                JOIN medewerkers m ON m.medewerker_id = d.medewerker_id
                WHERE m.organisatie_id = (SELECT organisatie_id FROM med) AND d.bijgewoond = 1
                GROUP BY d.medewerker_id
            )
        ),
        afd_acts AS (
            SELECT AVG(c) AS n FROM (
                SELECT COUNT(*) AS c
                FROM deelnames d
                JOIN medewerkers m ON m.medewerker_id = d.medewerker_id
                WHERE m.afdeling_id = (SELECT afdeling_id FROM med) AND d.bijgewoond = 1
                GROUP BY d.medewerker_id
            )
        ),
        my_min AS (
            SELECT AVG(actieve_minuten_vandaag) AS v FROM dashboard_dagelijks WHERE medewerker_id = ?
        ),
        org_min AS (
            SELECT AVG(dd.actieve_minuten_vandaag) AS v FROM dashboard_dagelijks dd
            JOIN medewerkers m ON m.medewerker_id = dd.medewerker_id
            WHERE m.organisatie_id = (SELECT organisatie_id FROM med)
        ),
        afd_min AS (
            SELECT AVG(dd.actieve_minuten_vandaag) AS v FROM dashboard_dagelijks dd
            JOIN medewerkers m ON m.medewerker_id = dd.medewerker_id
            WHERE m.afdeling_id = (SELECT afdeling_id FROM med)
        ),
        my_steps AS (
            SELECT AVG(gem_stappen_per_dag) AS v FROM gezondheidsmetingen WHERE medewerker_id = ?
        ),
        org_steps AS (
            SELECT AVG(gz.gem_stappen_per_dag) AS v FROM gezondheidsmetingen gz
            JOIN medewerkers m ON m.medewerker_id = gz.medewerker_id
            WHERE m.organisatie_id = (SELECT organisatie_id FROM med)
        ),
        afd_steps AS (
            SELECT AVG(gz.gem_stappen_per_dag) AS v FROM gezondheidsmetingen gz
            JOIN medewerkers m ON m.medewerker_id = gz.medewerker_id
            WHERE m.afdeling_id = (SELECT afdeling_id FROM med)
        ),
        my_stress AS (
            SELECT AVG(stress_1tot10) AS v FROM gezondheidsmetingen WHERE medewerker_id = ?
        ),
        org_stress AS (
            SELECT AVG(gz.stress_1tot10) AS v FROM gezondheidsmetingen gz
            JOIN medewerkers m ON m.medewerker_id = gz.medewerker_id
            WHERE m.organisatie_id = (SELECT organisatie_id FROM med)
        ),
        afd_stress AS (
            SELECT AVG(gz.stress_1tot10) AS v FROM gezondheidsmetingen gz
            JOIN medewerkers m ON m.medewerker_id = gz.medewerker_id
            WHERE m.afdeling_id = (SELECT afdeling_id FROM med)
        ),
        my_energie AS (
            SELECT AVG(energie_1tot10) AS v FROM gezondheidsmetingen WHERE medewerker_id = ?
        ),
        org_energie AS (
            SELECT AVG(gz.energie_1tot10) AS v FROM gezondheidsmetingen gz
            JOIN medewerkers m ON m.medewerker_id = gz.medewerker_id
            WHERE m.organisatie_id = (SELECT organisatie_id FROM med)
        ),
        afd_energie AS (
            SELECT AVG(gz.energie_1tot10) AS v FROM gezondheidsmetingen gz
            JOIN medewerkers m ON m.medewerker_id = gz.medewerker_id
            WHERE m.afdeling_id = (SELECT afdeling_id FROM med)
        )
        SELECT 'Activiteiten (totaal)' AS metric,
               (SELECT n FROM my_acts) AS me,
               (SELECT n FROM afd_acts) AS dept,
               (SELECT n FROM org_acts) AS org
        UNION ALL SELECT 'Gem. actieve min/dag',
               (SELECT v FROM my_min), (SELECT v FROM afd_min), (SELECT v FROM org_min)
        UNION ALL SELECT 'Gem. dagelijkse stappen',
               (SELECT v FROM my_steps), (SELECT v FROM afd_steps), (SELECT v FROM org_steps)
        UNION ALL SELECT 'Gem. stress (1-10)',
               (SELECT v FROM my_stress), (SELECT v FROM afd_stress), (SELECT v FROM org_stress)
        UNION ALL SELECT 'Gem. energie (1-10)',
               (SELECT v FROM my_energie), (SELECT v FROM afd_energie), (SELECT v FROM org_energie)
    """
    eid = int(employee_id)
    return query(sql, (eid, eid, eid, eid, eid, eid))


@st.cache_data(show_spinner=False, ttl=600)
def rank_history(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT week_startdatum AS week_start_date,
               rang             AS rank,
               totaal_punten    AS total_points,
               activiteiten_bijgewoond AS activities_attended,
               actieve_minuten         AS active_minutes
        FROM ranglijst_snapshots
        WHERE medewerker_id = ?
        ORDER BY week_startdatum
    """
    return query(sql, (int(employee_id),))


# ===========================================================================
# Vitaliteit & Verbondenheid composiet-scores
# ===========================================================================
@st.cache_data(show_spinner=False, ttl=600)
def vitality_score(employee_id: int) -> dict:
    sql = """
        WITH h AS (
            SELECT AVG(energie_1tot10) AS energy_avg,
                   AVG(stress_1tot10)  AS stress_avg,
                   AVG(gem_slaap_uren) AS sleep_avg,
                   AVG(actieve_minuten_totaal) AS active_min_avg,
                   AVG(gem_stappen_per_dag)    AS steps_avg
            FROM gezondheidsmetingen
            WHERE medewerker_id = ?
        ),
        f AS (
            SELECT AVG(f.energie_na_1tot10) AS energy_after_avg
            FROM feedback f
            JOIN deelnames d ON d.deelname_id = f.deelname_id
            WHERE d.medewerker_id = ?
        )
        SELECT energy_avg, stress_avg, sleep_avg, active_min_avg, steps_avg,
               (SELECT energy_after_avg FROM f) AS energy_after_avg
        FROM h
    """
    eid = int(employee_id)
    df = query(sql, (eid, eid))
    if df.empty:
        return {}
    r = df.iloc[0].to_dict()

    def _clamp(x): return max(0.0, min(100.0, x))
    energy_n  = _clamp(((r.get("energy_avg") or 0) / 10.0) * 100)
    stress_n  = _clamp(((10 - (r.get("stress_avg") or 5)) / 10.0) * 100)
    sleep_n   = _clamp(((r.get("sleep_avg") or 0) / 8.0) * 100) if r.get("sleep_avg") else 0
    active_n  = _clamp(((r.get("active_min_avg") or 0) / 150.0) * 100)

    composite = (energy_n + stress_n + sleep_n + active_n) / 4
    return {
        **r,
        "score_energy":   round(energy_n, 1),
        "score_stress":   round(stress_n, 1),
        "score_sleep":    round(sleep_n, 1),
        "score_movement": round(active_n, 1),
        "score_total":    round(composite, 1),
    }


@st.cache_data(show_spinner=False, ttl=600)
def connection_score(employee_id: int) -> dict:
    sql = """
        SELECT
            (SELECT AVG(f.verbondenheid_1tot5)
             FROM feedback f
             JOIN deelnames d ON d.deelname_id = f.deelname_id
             WHERE d.medewerker_id = ?) AS social_avg,
            (SELECT COUNT(*) FROM connecties
             WHERE (medewerker_id_a = ? OR medewerker_id_b = ?) AND status = 'geaccepteerd') AS friends,
            (SELECT COUNT(*) FROM team_lidmaatschappen WHERE medewerker_id = ?) AS teams,
            (SELECT COUNT(DISTINCT d2.medewerker_id)
             FROM deelnames d1
             JOIN deelnames d2 ON d2.activiteit_id = d1.activiteit_id
                AND d2.medewerker_id != d1.medewerker_id
             WHERE d1.medewerker_id = ? AND d1.bijgewoond = 1 AND d2.bijgewoond = 1) AS unique_partners
    """
    eid = int(employee_id)
    df = query(sql, (eid, eid, eid, eid, eid))
    if df.empty:
        return {}
    r = df.iloc[0].to_dict()

    def _clamp(x): return max(0.0, min(100.0, x))
    social_n   = _clamp(((r.get("social_avg") or 0) / 5.0) * 100)
    friends_n  = _clamp(((r.get("friends") or 0) / 10.0) * 100)
    teams_n    = _clamp(((r.get("teams") or 0) / 3.0) * 100)
    partners_n = _clamp(((r.get("unique_partners") or 0) / 25.0) * 100)

    # Versimpelde berekening: ongewogen gemiddelde van de vier sub-scores
    # (zelfde structuur als de vitaliteits-score, makkelijker uit te leggen).
    composite = (social_n + partners_n + friends_n + teams_n) / 4
    return {
        **r,
        "score_social":   round(social_n, 1),
        "score_partners": round(partners_n, 1),
        "score_friends":  round(friends_n, 1),
        "score_teams":    round(teams_n, 1),
        "score_total":    round(composite, 1),
    }


@st.cache_data(show_spinner=False, ttl=600)
def health_trends(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT week_startdatum    AS week_start_date,
               gem_stappen_per_dag AS steps,
               actieve_minuten_totaal AS active_minutes,
               gem_slaap_uren      AS sleep_hours,
               rusthartslag_bpm    AS resting_hr,
               stress_1tot10       AS stress,
               energie_1tot10      AS energy
        FROM gezondheidsmetingen
        WHERE medewerker_id = ?
        ORDER BY week_startdatum
    """
    return query(sql, (int(employee_id),))


@st.cache_data(show_spinner=False, ttl=600)
def training_partners(employee_id: int, limit: int = 10) -> pd.DataFrame:
    sql = """
        SELECT m.medewerker_id AS employee_id,
               m.voornaam || ' ' || m.achternaam AS naam,
               m.functie  AS job_role,
               a.afdeling_naam AS dept_name,
               COUNT(*)   AS sessies_samen,
               COUNT(DISTINCT act.sport_id) AS verschillende_sporten
        FROM deelnames d1
        JOIN deelnames d2 ON d2.activiteit_id = d1.activiteit_id
            AND d2.medewerker_id != d1.medewerker_id
        JOIN activiteiten act ON act.activiteit_id = d1.activiteit_id
        JOIN medewerkers m ON m.medewerker_id = d2.medewerker_id
        LEFT JOIN afdelingen a ON a.afdeling_id = m.afdeling_id
        WHERE d1.medewerker_id = ? AND d1.bijgewoond = 1 AND d2.bijgewoond = 1
        GROUP BY d2.medewerker_id
        ORDER BY sessies_samen DESC
        LIMIT ?
    """
    return query(sql, (int(employee_id), int(limit)))


@st.cache_data(show_spinner=False, ttl=600)
def social_connection_trend(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT date(f.ingediend_op, 'weekday 1', '-7 days') AS week_start,
               AVG(f.verbondenheid_1tot5) AS social,
               AVG(f.energie_na_1tot10)   AS energy,
               COUNT(*) AS feedback_n
        FROM feedback f
        JOIN deelnames d ON d.deelname_id = f.deelname_id
        WHERE d.medewerker_id = ?
        GROUP BY week_start
        ORDER BY week_start
    """
    return query(sql, (int(employee_id),))


@st.cache_data(show_spinner=False, ttl=600)
def connection_per_sport(employee_id: int, min_sessies: int = 2) -> pd.DataFrame:
    """Gemiddelde verbondenheids-score per sport voor de medewerker.

    Sporten met minder dan `min_sessies` met feedback worden uitgefilterd
    zodat een eenmalige hoge score geen vals beeld geeft.
    """
    sql = """
        SELECT sc.sport_naam                AS sport,
               AVG(f.verbondenheid_1tot5)   AS gem_verbondenheid,
               COUNT(*)                     AS aantal_feedbacks
        FROM feedback f
        JOIN deelnames d  ON d.deelname_id  = f.deelname_id
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        JOIN sportcategorieen sc ON sc.sport_id = a.sport_id
        WHERE d.medewerker_id = ?
          AND f.verbondenheid_1tot5 IS NOT NULL
        GROUP BY sc.sport_naam
        HAVING COUNT(*) >= ?
        ORDER BY gem_verbondenheid DESC
    """
    return query(sql, (int(employee_id), int(min_sessies)))


@st.cache_data(show_spinner=False, ttl=600)
def category_breakdown(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT sc.categorie AS category,
               COUNT(*)     AS sessies,
               COALESCE(SUM(aw.werkelijke_duur_min), 0) AS totaal_min,
               COALESCE(SUM(aw.geschatte_calorieen), 0) AS totaal_kcal
        FROM deelnames d
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        JOIN sportcategorieen sc ON sc.sport_id = a.sport_id
        LEFT JOIN aanwezigheid aw ON aw.deelname_id = d.deelname_id
        WHERE d.medewerker_id = ? AND d.bijgewoond = 1
        GROUP BY sc.categorie
        ORDER BY sessies DESC
    """
    return query(sql, (int(employee_id),))


@st.cache_data(show_spinner=False, ttl=600)
def indoor_outdoor_split(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT CASE WHEN l.binnen = 1 THEN 'Binnen' ELSE 'Buiten' END AS setting,
               COUNT(*) AS sessies
        FROM deelnames d
        JOIN activiteiten a ON a.activiteit_id = d.activiteit_id
        JOIN locaties l ON l.locatie_id = a.locatie_id
        WHERE d.medewerker_id = ? AND d.bijgewoond = 1
        GROUP BY l.binnen
    """
    return query(sql, (int(employee_id),))


@st.cache_data(show_spinner=False, ttl=600)
def all_achievements(employee_id: int) -> pd.DataFrame:
    sql = """
        SELECT p.prestatie_id AS achievement_id,
               p.naam         AS name,
               p.omschrijving AS description,
               p.niveau       AS tier,
               p.punten       AS points,
               bp.behaald_op  AS earned_date,
               bp.punten_toegekend AS points_awarded,
               CASE WHEN bp.behaalde_prestatie_id IS NULL THEN 0 ELSE 1 END AS earned
        FROM prestaties p
        LEFT JOIN behaalde_prestaties bp
            ON bp.prestatie_id = p.prestatie_id AND bp.medewerker_id = ?
        ORDER BY earned DESC, p.punten DESC
    """
    return query(sql, (int(employee_id),))
