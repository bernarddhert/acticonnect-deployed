"""
Laad alle CSV's uit ./output/ in een SQLite database voor SQL-queries en EDA.
Maakt indexes op de meest gebruikte FK-kolommen voor snelle joins.

Gebruik:
    python load_to_sqlite.py
    -> maakt acticonnect.db

Daarna in Python:
    import sqlite3
    conn = sqlite3.connect("acticonnect.db")
    df = pd.read_sql("SELECT * FROM activiteiten WHERE status='voltooid'", conn)
"""
import csv
import sqlite3
from pathlib import Path

OUTPUT = Path("output")
DB_PATH = "acticonnect.db"

# Schema-definities (Nederlandse tabel- en kolomnamen)
SCHEMA = {
    "organisaties": """
        CREATE TABLE organisaties (
            organisatie_id INTEGER PRIMARY KEY,
            organisatie_naam TEXT,
            branche TEXT,
            grootte_categorie TEXT,
            totaal_medewerkers INTEGER,
            hoofdkantoor_stad TEXT,
            land TEXT,
            opgericht_in INTEGER,
            vitaliteitsbudget_per_medewerker_eur INTEGER,
            contract_startdatum DATE,
            accountmanager TEXT,
            hr_email TEXT
        )""",
    "kantoorlocaties": """
        CREATE TABLE kantoorlocaties (
            kantoor_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            stad TEXT,
            adres TEXT,
            postcode TEXT,
            is_hoofdkantoor INTEGER,
            heeft_sportschool INTEGER,
            heeft_douche INTEGER,
            capaciteit INTEGER,
            FOREIGN KEY (organisatie_id) REFERENCES organisaties(organisatie_id)
        )""",
    "afdelingen": """
        CREATE TABLE afdelingen (
            afdeling_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            afdeling_naam TEXT,
            aantal_medewerkers INTEGER,
            FOREIGN KEY (organisatie_id) REFERENCES organisaties(organisatie_id)
        )""",
    "medewerkers": """
        CREATE TABLE medewerkers (
            medewerker_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            afdeling_id INTEGER,
            kantoor_id INTEGER,
            voornaam TEXT,
            achternaam TEXT,
            email TEXT,
            geslacht TEXT,
            geboortedatum DATE,
            functie TEXT,
            werkwijze TEXT,
            indienst_datum DATE,
            aanmeld_datum DATE,
            laatste_login DATE,
            is_actief INTEGER,
            notificatie_voorkeur TEXT,
            privacy_niveau TEXT
        )""",
    "medewerker_profielen": """
        CREATE TABLE medewerker_profielen (
            profiel_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            lengte_cm REAL,
            gewicht_kg REAL,
            fitness_niveau TEXT,
            hoofddoel TEXT,
            weekdoel_minuten INTEGER,
            voorkeurstijd TEXT,
            bio TEXT,
            profiel_volledig_pct INTEGER
        )""",
    "gezondheidsmetingen": """
        CREATE TABLE gezondheidsmetingen (
            gezondheid_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            week_startdatum DATE,
            gem_stappen_per_dag INTEGER,
            actieve_minuten_totaal INTEGER,
            gem_slaap_uren REAL,
            rusthartslag_bpm INTEGER,
            stress_1tot10 INTEGER,
            energie_1tot10 INTEGER,
            data_bron TEXT
        )""",
    "sportcategorieen": """
        CREATE TABLE sportcategorieen (
            sport_id INTEGER PRIMARY KEY,
            sport_naam TEXT,
            categorie TEXT,
            locatie_type TEXT,
            min_deelnemers INTEGER,
            typische_duur_min INTEGER,
            intensiteit_factor REAL,
            gem_calorieen_per_uur INTEGER
        )""",
    "locaties": """
        CREATE TABLE locaties (
            locatie_id INTEGER PRIMARY KEY,
            naam TEXT,
            stad TEXT,
            locatie_type TEXT,
            capaciteit INTEGER,
            binnen INTEGER,
            beoordeling REAL,
            kosten_per_uur_eur REAL
        )""",
    "sportinteresses": """
        CREATE TABLE sportinteresses (
            interesse_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            sport_id INTEGER,
            vaardigheidsniveau TEXT,
            jaren_ervaring INTEGER,
            toegevoegd_op DATE
        )""",
    "connecties": """
        CREATE TABLE connecties (
            connectie_id INTEGER PRIMARY KEY,
            medewerker_id_a INTEGER,
            medewerker_id_b INTEGER,
            verbonden_sinds DATE,
            status TEXT
        )""",
    "teams": """
        CREATE TABLE teams (
            team_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            team_naam TEXT,
            sport_id INTEGER,
            aanvoerder_id INTEGER,
            aangemaakt_op DATE,
            is_openbaar INTEGER,
            max_leden INTEGER
        )""",
    "team_lidmaatschappen": """
        CREATE TABLE team_lidmaatschappen (
            lidmaatschap_id INTEGER PRIMARY KEY,
            team_id INTEGER,
            medewerker_id INTEGER,
            toegetreden_op DATE,
            rol TEXT
        )""",
    "activiteiten": """
        CREATE TABLE activiteiten (
            activiteit_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            organisator_id INTEGER,
            sport_id INTEGER,
            locatie_id INTEGER,
            team_id INTEGER,
            titel TEXT,
            omschrijving TEXT,
            geplande_tijd DATETIME,
            duur_minuten INTEGER,
            max_deelnemers INTEGER,
            min_deelnemers INTEGER,
            vereist_niveau TEXT,
            is_terugkerend INTEGER,
            kosten_per_persoon_eur REAL,
            status TEXT,
            aangemaakt_op DATETIME
        )""",
    "activiteit_tags": """
        CREATE TABLE activiteit_tags (
            tag_id INTEGER PRIMARY KEY,
            activiteit_id INTEGER,
            tag TEXT
        )""",
    "deelnames": """
        CREATE TABLE deelnames (
            deelname_id INTEGER PRIMARY KEY,
            activiteit_id INTEGER,
            medewerker_id INTEGER,
            aanmeld_tijd DATETIME,
            status TEXT,
            bijgewoond INTEGER,
            is_organisator INTEGER
        )""",
    "aanwezigheid": """
        CREATE TABLE aanwezigheid (
            aanwezigheid_id INTEGER PRIMARY KEY,
            deelname_id INTEGER,
            medewerker_id INTEGER,
            activiteit_id INTEGER,
            check_in_tijd DATETIME,
            check_out_tijd DATETIME,
            werkelijke_duur_min REAL,
            geschatte_calorieen INTEGER,
            hartslag_gem INTEGER,
            hartslag_piek INTEGER
        )""",
    "feedback": """
        CREATE TABLE feedback (
            feedback_id INTEGER PRIMARY KEY,
            deelname_id INTEGER,
            beoordeling INTEGER,
            energie_na_1tot10 INTEGER,
            stemming_na TEXT,
            zou_aanbevelen INTEGER,
            zou_opnieuw_bezoeken INTEGER,
            verbondenheid_1tot5 INTEGER,
            opmerking TEXT,
            ingediend_op DATETIME
        )""",
    "prestaties": """
        CREATE TABLE prestaties (
            prestatie_id INTEGER PRIMARY KEY,
            naam TEXT,
            omschrijving TEXT,
            niveau TEXT,
            punten INTEGER,
            icoon_url TEXT
        )""",
    "behaalde_prestaties": """
        CREATE TABLE behaalde_prestaties (
            behaalde_prestatie_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            prestatie_id INTEGER,
            behaald_op DATE,
            punten_toegekend INTEGER
        )""",
    "uitdagingen": """
        CREATE TABLE uitdagingen (
            uitdaging_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            naam TEXT,
            omschrijving TEXT,
            meting_type TEXT,
            doelwaarde REAL,
            startdatum DATE,
            einddatum DATE,
            beloning_punten INTEGER,
            status TEXT
        )""",
    "uitdaging_deelnemers": """
        CREATE TABLE uitdaging_deelnemers (
            uitdaging_deelnemer_id INTEGER PRIMARY KEY,
            uitdaging_id INTEGER,
            medewerker_id INTEGER,
            toegetreden_op DATE,
            huidige_voortgang REAL,
            voortgang_pct REAL,
            voltooid INTEGER,
            rang INTEGER
        )""",
    "ranglijst_snapshots": """
        CREATE TABLE ranglijst_snapshots (
            ranglijst_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            medewerker_id INTEGER,
            week_startdatum DATE,
            rang INTEGER,
            totaal_punten INTEGER,
            activiteiten_bijgewoond INTEGER,
            actieve_minuten INTEGER
        )""",
    "abonnementen": """
        CREATE TABLE abonnementen (
            abonnement_id INTEGER PRIMARY KEY,
            organisatie_id INTEGER,
            niveau TEXT,
            prijs_per_gebruiker_maand_eur REAL,
            gelicenseerde_gebruikers INTEGER,
            facturatie_cyclus TEXT,
            startdatum DATE,
            verlenging_datum DATE,
            auto_verlengen INTEGER,
            korting_pct REAL,
            totale_contract_waarde_eur REAL
        )""",
    "notificaties": """
        CREATE TABLE notificaties (
            notificatie_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            activiteit_id INTEGER,
            kanaal TEXT,
            notificatie_type TEXT,
            verstuurd_op DATETIME,
            bezorg_status TEXT
        )""",
    "platform_gebeurtenissen": """
        CREATE TABLE platform_gebeurtenissen (
            gebeurtenis_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            gebeurtenis_type TEXT,
            tijdstip DATETIME,
            apparaat TEXT,
            sessie_id TEXT,
            duur_sec INTEGER
        )""",
    "dashboard_dagelijks": """
        CREATE TABLE dashboard_dagelijks (
            dashboard_id INTEGER PRIMARY KEY,
            medewerker_id INTEGER,
            snapshot_datum DATE,
            activiteiten_vandaag INTEGER,
            actieve_minuten_vandaag REAL,
            calorieen_vandaag INTEGER,
            gem_hartslag REAL,
            reeks_weken INTEGER,
            totaal_punten INTEGER,
            rang_in_org INTEGER,
            doel_voortgang_pct REAL
        )""",
}

INDEXES = [
    "CREATE INDEX idx_medewerkers_org ON medewerkers(organisatie_id)",
    "CREATE INDEX idx_medewerkers_afd ON medewerkers(afdeling_id)",
    "CREATE INDEX idx_gezondheid_med ON gezondheidsmetingen(medewerker_id, week_startdatum)",
    "CREATE INDEX idx_activiteiten_org ON activiteiten(organisatie_id)",
    "CREATE INDEX idx_activiteiten_org_isr ON activiteiten(organisator_id)",
    "CREATE INDEX idx_activiteiten_sport ON activiteiten(sport_id)",
    "CREATE INDEX idx_activiteiten_dt ON activiteiten(geplande_tijd)",
    "CREATE INDEX idx_dn_act ON deelnames(activiteit_id)",
    "CREATE INDEX idx_dn_med ON deelnames(medewerker_id)",
    "CREATE INDEX idx_aw_med ON aanwezigheid(medewerker_id, check_in_tijd)",
    "CREATE INDEX idx_aw_act ON aanwezigheid(activiteit_id)",
    "CREATE INDEX idx_fb_dn ON feedback(deelname_id)",
    "CREATE INDEX idx_notif_med ON notificaties(medewerker_id, verstuurd_op)",
    "CREATE INDEX idx_geb_med ON platform_gebeurtenissen(medewerker_id, tijdstip)",
    "CREATE INDEX idx_geb_sess ON platform_gebeurtenissen(sessie_id)",
    "CREATE INDEX idx_dash_med ON dashboard_dagelijks(medewerker_id, snapshot_datum)",
    "CREATE INDEX idx_lb_org_wk ON ranglijst_snapshots(organisatie_id, week_startdatum)",
]


def naar_sqlite(v):
    """Lege string -> NULL."""
    if v == "":
        return None
    return v


def main():
    db_file = Path(DB_PATH)
    if db_file.exists():
        db_file.unlink()
        print(f"Bestaande {DB_PATH} verwijderd")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("\nTabellen aanmaken...")
    for naam, ddl in SCHEMA.items():
        cur.execute(ddl)

    print("\nData laden...")
    for naam in SCHEMA.keys():
        csv_pad = OUTPUT / f"{naam}.csv"
        if not csv_pad.exists():
            print(f"  WAARSCHUWING: {csv_pad} niet gevonden")
            continue
        with open(csv_pad, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            kolommen = reader.fieldnames
            placeholders = ",".join("?" * len(kolommen))
            sql = f"INSERT INTO {naam} ({','.join(kolommen)}) VALUES ({placeholders})"
            data = [tuple(naar_sqlite(rij[c]) for c in kolommen) for rij in reader]
            cur.executemany(sql, data)
            print(f"  {naam}: {len(data):,} rijen")

    print("\nIndexes aanmaken...")
    for idx in INDEXES:
        cur.execute(idx)

    conn.commit()
    conn.close()

    grootte_mb = db_file.stat().st_size / 1024 / 1024
    print(f"\nKlaar! {DB_PATH} ({grootte_mb:.1f} MB)")
    print(f"Open met: sqlite3 {DB_PATH}")


if __name__ == "__main__":
    main()
