"""
ActiConnect Mock Data Generator
==================================================
Genereert realistische mock-data voor alle 26 tabellen van het ActiConnect platform.

Schaal:
- 10 organisaties (mix Middelgroot/Groot/Enterprise)
- ~2.000 medewerkers
- 6 maanden / 26 weken historische data (eindigt 2026-05-04)
- Bewust ingebouwde data-kwaliteits-issues (~3-5%) voor EDA-demo

Output: 26 CSV-bestanden in ./output/

Tabel-namen (NL):
  organisaties, kantoorlocaties, afdelingen, medewerkers,
  medewerker_profielen, gezondheidsmetingen, sportcategorieen, locaties,
  sportinteresses, connecties, teams, team_lidmaatschappen,
  activiteiten, activiteit_tags, deelnames, aanwezigheid, feedback,
  prestaties, behaalde_prestaties, uitdagingen, uitdaging_deelnemers,
  ranglijst_snapshots, abonnementen, notificaties, platform_gebeurtenissen,
  dashboard_dagelijks
"""
import csv
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

from faker import Faker

# ============================================================
# CONFIG
# ============================================================
SEED = 42
random.seed(SEED)
fake = Faker("nl_NL")
Faker.seed(SEED)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

VANDAAG = date(2026, 5, 4)            # maandag — "vandaag" in de simulatie
WEKEN_HISTORIE = 26
WEKEN_TOEKOMST = 3                    # 3 weken aan toekomstige (geplande) activiteiten
START_DATUM = VANDAAG - timedelta(weeks=WEKEN_HISTORIE)
EIND_DATUM = VANDAAG
HORIZON_DATUM = VANDAAG + timedelta(weeks=WEKEN_TOEKOMST)  # tot waar we activiteiten plannen

print(f"Genereren mock-data van {START_DATUM} tot {EIND_DATUM}")

DQ_RATE = 0.03  # baseline-percentage data-kwaliteits-issues


# ============================================================
# UTILITIES
# ============================================================
def schrijf_csv(bestandsnaam: str, kolommen: list[str], rijen: list[dict]) -> None:
    pad = OUTPUT_DIR / bestandsnaam
    with open(pad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=kolommen)
        w.writeheader()
        w.writerows(rijen)
    print(f"  {bestandsnaam}: {len(rijen):,} rijen")


def random_datum(start: date, einde: date) -> date:
    delta = (einde - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def random_datetime(start: date, einde: date) -> datetime:
    d = random_datum(start, einde)
    return datetime.combine(d, time(random.randint(0, 23), random.randint(0, 59)))


def gewogen_keuze(keuzes_met_gewichten):
    """Kies een waarde uit [(waarde, gewicht), ...]."""
    waarden, gewichten = zip(*keuzes_met_gewichten)
    return random.choices(waarden, weights=gewichten, k=1)[0]


def soms_null(waarde, kans=DQ_RATE):
    """DQ-injectie: maakt een waarde NULL met de gegeven kans."""
    return None if random.random() < kans else waarde


def csv_waarde(v):
    """Converteer Python None -> lege string voor CSV-export."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    return v


# ============================================================
# 1. ORGANISATIES
# ============================================================
ORG_DEFINITIES = [
    # (naam, branche, grootte, totaal_medewerkers, hoofdkantoor_stad, opgericht_jaar, vit_budget)
    ("Vossen Tech Solutions",   "Technologie",       "Groot",      850, "Eindhoven", 2008, 500),
    ("De Boer & Partners",      "Financieel",        "Enterprise", 3200, "Amsterdam", 1987, 750),
    ("Mediq Healthcare Group",  "Gezondheidszorg",   "Enterprise", 4100, "Utrecht",   1976, 600),
    ("PolderData Analytics",    "Technologie",       "Middelgroot", 220, "Rotterdam", 2015, 450),
    ("Janssen Logistics BV",    "Logistiek",         "Groot",     1400, "Tilburg",   2001, 350),
    ("Greenfield Energy",       "Energie",           "Groot",      980, "Groningen", 2011, 550),
    ("Tulip Marketing Group",   "Marketing",         "Middelgroot", 180, "Amsterdam", 2017, 400),
    ("Kraan Engineering",       "Engineering",       "Groot",     1100, "Delft",     1994, 500),
    ("Bakker Retail Holding",   "Retail",            "Enterprise", 5500, "Zaandam",   1962, 300),
    ("Nieuwland Consulting",    "Consultancy",       "Middelgroot", 310, "Den Haag",  2013, 600),
]

# Aantal medewerkers per organisatie (totaal ~2000)
MEDEWERKERS_PER_ORG = [220, 380, 320, 110, 240, 200, 90, 200, 180, 130]


def genereer_organisaties():
    rijen = []
    for i, (naam, branche, grootte, totaal, stad, opgericht, budget) in enumerate(ORG_DEFINITIES, 1):
        contract_start = random_datum(date(2022, 1, 1), date(2025, 6, 1))
        rijen.append({
            "organisatie_id": i,
            "organisatie_naam": naam,
            "branche": branche,
            "grootte_categorie": grootte,
            "totaal_medewerkers": totaal,
            "hoofdkantoor_stad": stad,
            "land": "Nederland",
            "opgericht_in": opgericht,
            "vitaliteitsbudget_per_medewerker_eur": budget,
            "contract_startdatum": contract_start,
            "accountmanager": fake.name(),
            "hr_email": f"hr@{naam.lower().replace(' ', '').replace('&', 'en').replace('.', '')[:20]}.nl",
        })
    return rijen


# ============================================================
# 2. KANTOORLOCATIES
# ============================================================
NL_STEDEN = ["Eindhoven", "Amsterdam", "Utrecht", "Rotterdam", "Tilburg", "Groningen",
             "Delft", "Zaandam", "Den Haag", "Nijmegen", "Breda", "Arnhem", "Leiden",
             "Maastricht", "Haarlem", "'s-Hertogenbosch", "Almere", "Enschede"]


def genereer_kantoorlocaties(organisaties):
    rijen = []
    kantoor_id = 1
    for org in organisaties:
        grootte = org["grootte_categorie"]
        if grootte == "Middelgroot":
            n = random.randint(1, 2)
        elif grootte == "Groot":
            n = random.randint(2, 4)
        else:  # Enterprise
            n = random.randint(4, 7)

        for j in range(n):
            is_hk = (j == 0)
            stad = org["hoofdkantoor_stad"] if is_hk else random.choice(NL_STEDEN)
            rijen.append({
                "kantoor_id": kantoor_id,
                "organisatie_id": org["organisatie_id"],
                "stad": stad,
                "adres": fake.street_address(),
                "postcode": fake.postcode(),
                "is_hoofdkantoor": is_hk,
                "heeft_sportschool": random.random() < (0.6 if grootte == "Enterprise" else 0.3 if grootte == "Groot" else 0.1),
                "heeft_douche": random.random() < (0.85 if grootte == "Enterprise" else 0.6 if grootte == "Groot" else 0.4),
                "capaciteit": random.randint(50, 80) if grootte == "Middelgroot"
                              else random.randint(150, 400) if grootte == "Groot"
                              else random.randint(300, 800),
            })
            kantoor_id += 1
    return rijen


# ============================================================
# 3. AFDELINGEN
# ============================================================
AFDELING_NAMEN = ["Engineering", "Sales", "Marketing", "HR", "Financiën", "Operations",
                  "Klantenservice", "Product", "IT", "Juridisch", "R&D", "Inkoop"]


def genereer_afdelingen(organisaties):
    rijen = []
    afdeling_id = 1
    for org in organisaties:
        grootte = org["grootte_categorie"]
        n = random.randint(4, 6) if grootte == "Middelgroot" else random.randint(6, 9) if grootte == "Groot" else random.randint(8, 11)
        gekozen = random.sample(AFDELING_NAMEN, n)
        for naam in gekozen:
            rijen.append({
                "afdeling_id": afdeling_id,
                "organisatie_id": org["organisatie_id"],
                "afdeling_naam": naam,
                "aantal_medewerkers": random.randint(8, 50),
            })
            afdeling_id += 1
    return rijen


# ============================================================
# 4. MEDEWERKERS
# ============================================================
FUNCTIES = [("Junior", 0.25), ("Medior", 0.35), ("Senior", 0.25), ("Lead", 0.08),
            ("Manager", 0.05), ("Directeur", 0.02)]
WERKWIJZEN = [("Hybride", 0.55), ("Op locatie", 0.30), ("Thuis", 0.15)]
GESLACHTEN = [("M", 0.52), ("V", 0.46), ("X", 0.02)]
NOTIFICATIE_VOORKEUREN = [("email", 0.55), ("beide", 0.25), ("sms", 0.10), ("geen", 0.10)]
PRIVACY_NIVEAUS = [("collegas", 0.55), ("openbaar", 0.30), ("prive", 0.15)]


def genereer_medewerkers(organisaties, afdelingen, kantoren):
    rijen = []
    medewerker_id = 1

    afdelingen_per_org = {}
    for d in afdelingen:
        afdelingen_per_org.setdefault(d["organisatie_id"], []).append(d)
    kantoren_per_org = {}
    for o in kantoren:
        kantoren_per_org.setdefault(o["organisatie_id"], []).append(o)

    for org, n_medewerkers in zip(organisaties, MEDEWERKERS_PER_ORG):
        org_id = org["organisatie_id"]
        contract_start = org["contract_startdatum"]

        for _ in range(n_medewerkers):
            geslacht = gewogen_keuze(GESLACHTEN)
            if geslacht == "M":
                voornaam = fake.first_name_male()
            elif geslacht == "V":
                voornaam = fake.first_name_female()
            else:
                voornaam = fake.first_name()
            achternaam = fake.last_name()

            domein = org["hr_email"].split("@")[1]
            email = f"{voornaam.lower()}.{achternaam.lower().replace(' ', '')}@{domein}".replace("'", "")

            indienst_datum = random_datum(date(2015, 1, 1), EIND_DATUM - timedelta(days=30))

            # Aanmeld-datum spreidt zich vanaf contract_start (langzame adoptie)
            aanmeld_min = max(indienst_datum, contract_start)
            if aanmeld_min >= EIND_DATUM:
                aanmeld_datum = EIND_DATUM - timedelta(days=random.randint(1, 30))
            else:
                dagen_beschikbaar = (EIND_DATUM - aanmeld_min).days
                bias = random.random() ** 0.5
                aanmeld_datum = aanmeld_min + timedelta(days=int(bias * dagen_beschikbaar))

            # Last login: actieve gebruikers loggen recent in
            activiteit_score = random.random()  # 0-1, hoger = actiever
            if activiteit_score > 0.3:
                dagen_sinds_login = int(random.expovariate(0.3))
                dagen_sinds_login = min(dagen_sinds_login, 90)
            else:
                dagen_sinds_login = random.randint(30, 180)
            laatste_login = EIND_DATUM - timedelta(days=dagen_sinds_login)
            if laatste_login < aanmeld_datum:
                laatste_login = aanmeld_datum

            is_actief = dagen_sinds_login < 60

            afd_voor_org = afdelingen_per_org.get(org_id, [])
            knt_voor_org = kantoren_per_org.get(org_id, [])

            rijen.append({
                "medewerker_id": medewerker_id,
                "organisatie_id": org_id,
                "afdeling_id": random.choice(afd_voor_org)["afdeling_id"] if afd_voor_org else None,
                "kantoor_id": random.choice(knt_voor_org)["kantoor_id"] if knt_voor_org else None,
                "voornaam": voornaam,
                "achternaam": achternaam,
                "email": email,
                "geslacht": soms_null(geslacht, kans=0.04),  # ~4% missing geslacht
                "geboortedatum": fake.date_of_birth(minimum_age=22, maximum_age=64),
                "functie": gewogen_keuze(FUNCTIES),
                "werkwijze": gewogen_keuze(WERKWIJZEN),
                "indienst_datum": indienst_datum,
                "aanmeld_datum": aanmeld_datum,
                "laatste_login": laatste_login,
                "is_actief": is_actief,
                "notificatie_voorkeur": gewogen_keuze(NOTIFICATIE_VOORKEUREN),
                "privacy_niveau": gewogen_keuze(PRIVACY_NIVEAUS),
                "_activiteit_score": activiteit_score,  # interne hint voor andere generators
            })
            medewerker_id += 1

    return rijen


# ============================================================
# 5. SPORTCATEGORIEEN
# ============================================================
SPORTEN = [
    # (naam, categorie, locatie_type, min_deelnemers, duur_min, intensiteit, kcal/uur)
    ("Padel",            "Racket",   "Beide",  4, 60, 1.0, 450),
    ("Tennis",           "Racket",   "Beide",  2, 60, 1.0, 480),
    ("Squash",           "Racket",   "Binnen", 2, 45, 1.2, 600),
    ("Tafeltennis",      "Racket",   "Binnen", 2, 45, 0.6, 250),
    ("Badminton",        "Racket",   "Binnen", 2, 60, 0.9, 420),
    ("Hardlopen",        "Cardio",   "Buiten", 1, 45, 1.1, 600),
    ("Wandelen",         "Cardio",   "Buiten", 1, 60, 0.5, 220),
    ("Wielrennen",       "Cardio",   "Buiten", 1, 90, 1.0, 500),
    ("Spinning",         "Cardio",   "Binnen", 1, 45, 1.2, 580),
    ("Zwemmen",          "Cardio",   "Binnen", 1, 45, 1.0, 480),
    ("Voetbal",          "Team",     "Beide", 10, 90, 1.0, 550),
    ("Volleybal",        "Team",     "Binnen", 8, 60, 0.8, 380),
    ("Basketbal",        "Team",     "Beide",  6, 60, 1.1, 580),
    ("Hockey",           "Team",     "Buiten",10, 60, 1.0, 520),
    ("Ultimate Frisbee", "Team",     "Buiten", 8, 60, 0.9, 460),
    ("Yoga",             "Mentaal",  "Binnen", 1, 60, 0.4, 200),
    ("Pilates",          "Mentaal",  "Binnen", 1, 60, 0.5, 240),
    ("Mindful Wandelen", "Mentaal",  "Buiten", 1, 30, 0.4, 150),
    ("CrossFit",         "Kracht",   "Binnen", 1, 60, 1.4, 700),
    ("Bootcamp",         "Kracht",   "Beide",  4, 45, 1.3, 620),
    ("Krachttraining",   "Kracht",   "Binnen", 1, 60, 0.9, 400),
    ("Boksen",           "Kracht",   "Binnen", 1, 45, 1.3, 650),
    ("Klimmen",          "Kracht",   "Binnen", 2, 90, 1.0, 500),
]


def genereer_sportcategorieen():
    rijen = []
    for i, (naam, cat, loc, mn, duur, inten, kcal) in enumerate(SPORTEN, 1):
        rijen.append({
            "sport_id": i,
            "sport_naam": naam,
            "categorie": cat,
            "locatie_type": loc,
            "min_deelnemers": mn,
            "typische_duur_min": duur,
            "intensiteit_factor": inten,
            "gem_calorieen_per_uur": kcal,
        })
    return rijen


# ============================================================
# 6. LOCATIES
# ============================================================
LOCATIE_TYPES = ["Sportschool", "Sportpark", "Padel Club", "Park", "Zwembad",
                 "Tennisclub", "Voetbalveld", "Yogastudio", "Klimhal", "Kantoor Sportschool"]


def genereer_locaties():
    rijen = []
    locatie_id = 1
    for stad in NL_STEDEN:
        n = random.randint(2, 5)
        for _ in range(n):
            ltype = random.choice(LOCATIE_TYPES)
            binnen = ltype not in ["Sportpark", "Park", "Voetbalveld"]
            rijen.append({
                "locatie_id": locatie_id,
                "naam": f"{ltype} {fake.last_name()}" if random.random() < 0.5 else f"{stad} {ltype}",
                "stad": stad,
                "locatie_type": ltype,
                "capaciteit": random.choice([10, 15, 20, 30, 40, 50, 80, 100, 200]),
                "binnen": binnen,
                "beoordeling": round(random.uniform(3.2, 4.9), 1),
                "kosten_per_uur_eur": round(random.choice([0, 0, 15, 25, 35, 45, 60, 75, 90]), 2),
            })
            locatie_id += 1
    return rijen


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n=== Identiteit-domein ===")
    organisaties = genereer_organisaties()
    schrijf_csv("organisaties.csv",
                ["organisatie_id", "organisatie_naam", "branche", "grootte_categorie",
                 "totaal_medewerkers", "hoofdkantoor_stad", "land", "opgericht_in",
                 "vitaliteitsbudget_per_medewerker_eur", "contract_startdatum",
                 "accountmanager", "hr_email"],
                organisaties)

    kantoren = genereer_kantoorlocaties(organisaties)
    schrijf_csv("kantoorlocaties.csv",
                ["kantoor_id", "organisatie_id", "stad", "adres", "postcode",
                 "is_hoofdkantoor", "heeft_sportschool", "heeft_douche", "capaciteit"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in kantoren])

    afdelingen = genereer_afdelingen(organisaties)
    schrijf_csv("afdelingen.csv",
                ["afdeling_id", "organisatie_id", "afdeling_naam", "aantal_medewerkers"],
                afdelingen)

    medewerkers = genereer_medewerkers(organisaties, afdelingen, kantoren)
    medewerker_kolommen = [
        "medewerker_id", "organisatie_id", "afdeling_id", "kantoor_id",
        "voornaam", "achternaam", "email", "geslacht", "geboortedatum",
        "functie", "werkwijze", "indienst_datum", "aanmeld_datum", "laatste_login",
        "is_actief", "notificatie_voorkeur", "privacy_niveau",
    ]
    schrijf_csv("medewerkers.csv", medewerker_kolommen,
                [{k: csv_waarde(r.get(k)) for k in medewerker_kolommen} for r in medewerkers])

    print(f"\nIdentiteit klaar: {len(organisaties)} organisaties, "
          f"{len(kantoren)} kantoren, {len(afdelingen)} afdelingen, "
          f"{len(medewerkers)} medewerkers")

    # ============================================================
    # 7. MEDEWERKER_PROFIELEN (~75% vult in)
    # ============================================================
    print("\n=== Profielen & Gezondheid ===")
    FITNESS_NIVEAUS = [("Beginner", 0.30), ("Gemiddeld", 0.45), ("Gevorderd", 0.20), ("Elite", 0.05)]
    HOOFDDOELEN = [("Algemene fitheid", 0.30), ("Stressvermindering", 0.20), ("Sociaal", 0.15),
                   ("Gewichtsverlies", 0.15), ("Uithoudingsvermogen", 0.12), ("Spieropbouw", 0.08)]
    VOORKEURSTIJDEN = [("Lunch", 0.30), ("Avond", 0.30), ("Ochtend", 0.20), ("Middag", 0.20)]

    profielen = []
    profiel_id = 1
    for med in medewerkers:
        if med["_activiteit_score"] < 0.25:  # ~25% vult niet in
            continue
        g = med["geslacht"]
        if g == "M":
            lengte = round(random.gauss(180, 7), 1)
            gewicht = round(random.gauss(82, 11), 1)
        elif g == "V":
            lengte = round(random.gauss(168, 6), 1)
            gewicht = round(random.gauss(68, 9), 1)
        else:
            lengte = round(random.gauss(174, 8), 1)
            gewicht = round(random.gauss(75, 10), 1)
        lengte = max(150, min(210, lengte))
        gewicht = max(45, min(140, gewicht))

        # 0.5% data-kwaliteits-issue: extreme outlier — ofwel een typfout
        # tijdens invoer (75 → 175), ofwel ernstige obesitas. Hoe dan ook
        # duidelijk afwijkend van het normale bereik (45-140 kg).
        if random.random() < 0.005:
            gewicht = round(random.uniform(170, 240), 1)

        profielen.append({
            "profiel_id": profiel_id,
            "medewerker_id": med["medewerker_id"],
            "lengte_cm": lengte,
            "gewicht_kg": gewicht,
            "fitness_niveau": gewogen_keuze(FITNESS_NIVEAUS),
            "hoofddoel": gewogen_keuze(HOOFDDOELEN),
            "weekdoel_minuten": random.choice([90, 120, 150, 180, 210, 240, 300]),
            "voorkeurstijd": gewogen_keuze(VOORKEURSTIJDEN),
            "bio": fake.sentence(nb_words=12) if random.random() < 0.4 else None,
            "profiel_volledig_pct": random.choice([60, 70, 80, 90, 100]),
        })
        profiel_id += 1

    schrijf_csv("medewerker_profielen.csv",
                ["profiel_id", "medewerker_id", "lengte_cm", "gewicht_kg", "fitness_niveau",
                 "hoofddoel", "weekdoel_minuten", "voorkeurstijd", "bio", "profiel_volledig_pct"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in profielen])

    profiel_per_med = {p["medewerker_id"]: p for p in profielen}

    # Gezondheidsmetingen worden later gegenereerd (na deelnames), zodat
    # stress en energie kunnen koppelen aan WERKELIJKE deelname-aantallen
    # i.p.v. alleen aan het abstracte _activiteit_score. Zie blok §8b
    # verderop.
    DATA_BRONNEN = [("Fitbit", 0.30), ("Apple Watch", 0.25), ("Garmin", 0.20),
                    ("Google Fit", 0.15), ("Handmatig", 0.10)]

    # ============================================================
    # SPORTCATEGORIEEN + LOCATIES
    # ============================================================
    print("\n=== Catalogus ===")
    sporten = genereer_sportcategorieen()
    schrijf_csv("sportcategorieen.csv",
                ["sport_id", "sport_naam", "categorie", "locatie_type", "min_deelnemers",
                 "typische_duur_min", "intensiteit_factor", "gem_calorieen_per_uur"],
                sporten)

    locaties = genereer_locaties()
    schrijf_csv("locaties.csv",
                ["locatie_id", "naam", "stad", "locatie_type", "capaciteit", "binnen",
                 "beoordeling", "kosten_per_uur_eur"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in locaties])
    print(f"Catalogus klaar: {len(sporten)} sporten, {len(locaties)} locaties")

    # ============================================================
    # 9. SPORTINTERESSES
    # ============================================================
    print("\n=== Engagement-domein ===")
    VAARDIGHEIDSNIVEAUS = [("Beginner", 0.30), ("Gemiddeld", 0.45), ("Gevorderd", 0.20), ("Expert", 0.05)]

    interesses = []
    interesse_id = 1
    interesses_per_med = {}
    for med in medewerkers:
        if med["_activiteit_score"] < 0.15:
            continue
        n = random.choices([1, 2, 3, 4, 5], weights=[10, 25, 35, 20, 10])[0]
        gekozen = random.sample(sporten, n)
        med_int = []
        for sp in gekozen:
            interesses.append({
                "interesse_id": interesse_id,
                "medewerker_id": med["medewerker_id"],
                "sport_id": sp["sport_id"],
                "vaardigheidsniveau": gewogen_keuze(VAARDIGHEIDSNIVEAUS),
                "jaren_ervaring": random.choices(
                    [0, 1, 2, 3, 5, 8, 12, 20], weights=[15, 25, 20, 15, 12, 8, 4, 1])[0],
                "toegevoegd_op": random_datum(med["aanmeld_datum"], EIND_DATUM),
            })
            med_int.append(sp["sport_id"])
            interesse_id += 1
        interesses_per_med[med["medewerker_id"]] = med_int

    schrijf_csv("sportinteresses.csv",
                ["interesse_id", "medewerker_id", "sport_id", "vaardigheidsniveau",
                 "jaren_ervaring", "toegevoegd_op"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in interesses])

    # ============================================================
    # 10. CONNECTIES (vriendschappen)
    # ============================================================
    med_per_org = {}
    for e in medewerkers:
        med_per_org.setdefault(e["organisatie_id"], []).append(e)

    connecties_raw = []
    for org in organisaties:
        org_meds = med_per_org[org["organisatie_id"]]
        for med in org_meds:
            if med["_activiteit_score"] < 0.20:
                continue
            n_conn = max(0, min(20, int(random.gauss(6, 2.5))))
            potentieel = [e for e in org_meds if e["medewerker_id"] != med["medewerker_id"]]
            if len(potentieel) < n_conn:
                continue
            partners = random.sample(potentieel, n_conn)
            for partner in partners:
                a, b = sorted([med["medewerker_id"], partner["medewerker_id"]])
                verbonden = random_datum(max(med["aanmeld_datum"], partner["aanmeld_datum"]), EIND_DATUM)
                connecties_raw.append({
                    "medewerker_id_a": a,
                    "medewerker_id_b": b,
                    "verbonden_sinds": verbonden,
                    "status": "geaccepteerd" if random.random() < 0.92 else "in_afwachting",
                })

    # Deduplicatie
    gezien = set()
    connecties = []
    for c in connecties_raw:
        sleutel = (c["medewerker_id_a"], c["medewerker_id_b"])
        if sleutel in gezien:
            continue
        gezien.add(sleutel)
        connecties.append(c)
    for i, c in enumerate(connecties, 1):
        c["connectie_id"] = i

    schrijf_csv("connecties.csv",
                ["connectie_id", "medewerker_id_a", "medewerker_id_b", "verbonden_sinds", "status"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in connecties])

    # ============================================================
    # 11. TEAMS
    # ============================================================
    teams = []
    team_id = 1
    teams_per_org = {}
    TEAM_PREFIXES = ["The", "Team", "Squad", ""]
    TEAM_SUFFIXES = ["Strikers", "Champions", "Eagles", "Wolves", "Lightning", "Thunder",
                     "Allstars", "Crew", "Force", "United", "Riders", "Warriors"]

    for org in organisaties:
        org_meds = med_per_org[org["organisatie_id"]]
        actieve = [e for e in org_meds if e["_activiteit_score"] > 0.4]
        if len(actieve) < 5:
            continue
        # Iets meer teams + grotere bezetting zodat ook mid-actieve medewerkers
        # in een team passen (10-25% van actieve werknemers, was 5-15%)
        n_teams = max(2, int(len(actieve) * random.uniform(0.10, 0.25)))
        teams_per_org[org["organisatie_id"]] = []
        for _ in range(n_teams):
            sp = random.choice(sporten)
            aanvoerder = random.choice(actieve)
            naam = f"{random.choice(TEAM_PREFIXES)} {sp['sport_naam']} {random.choice(TEAM_SUFFIXES)}".strip()
            teams.append({
                "team_id": team_id,
                "organisatie_id": org["organisatie_id"],
                "team_naam": naam,
                "sport_id": sp["sport_id"],
                "aanvoerder_id": aanvoerder["medewerker_id"],
                "aangemaakt_op": random_datum(START_DATUM, EIND_DATUM - timedelta(days=14)),
                "is_openbaar": random.random() < 0.7,
                "max_leden": random.choice([15, 20, 25, 30, 35]),
            })
            teams_per_org[org["organisatie_id"]].append(
                (team_id, sp["sport_id"], aanvoerder["medewerker_id"]))
            team_id += 1

    schrijf_csv("teams.csv",
                ["team_id", "organisatie_id", "team_naam", "sport_id", "aanvoerder_id",
                 "aangemaakt_op", "is_openbaar", "max_leden"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in teams])

    # ============================================================
    # 12. TEAM_LIDMAATSCHAPPEN
    # ============================================================
    lidmaatschappen = []
    lid_id = 1
    leden_per_team = {}
    # Tracker: welke medewerkers zitten al in een team binnen deze organisatie?
    # Voorkomt dat steeds dezelfde top-spelers in alle teams belanden.
    in_team_per_org: dict[int, set[int]] = {}

    for team in teams:
        org_id = team["organisatie_id"]
        sport_id = team["sport_id"]
        aanv_id = team["aanvoerder_id"]
        in_team_per_org.setdefault(org_id, set()).add(aanv_id)

        # Aanvoerder altijd lid
        lidmaatschappen.append({
            "lidmaatschap_id": lid_id,
            "team_id": team["team_id"],
            "medewerker_id": aanv_id,
            "toegetreden_op": team["aangemaakt_op"],
            "rol": "aanvoerder",
        })
        lid_id += 1

        # Bredere kandidaten-pool: alle actieve medewerkers (score > 0.3),
        # waarbij interesse-match én "nog-niet-in-een-team" de kans op selectie
        # boost. Resultaat: teams krijgen verschillende leden, niet steeds
        # dezelfde top-spelers.
        org_meds = med_per_org[org_id]
        kandidaten = [e for e in org_meds
                      if e["medewerker_id"] != aanv_id
                      and e["_activiteit_score"] > 0.30]

        org_in_team = in_team_per_org[org_id]

        def _kandidaat_score(e):
            base = e["_activiteit_score"]
            if sport_id in interesses_per_med.get(e["medewerker_id"], []):
                base += 0.6   # interesse-match wint
            if e["medewerker_id"] not in org_in_team:
                base += 0.5   # voorrang voor wie nog geen team heeft
            return base + random.random() * 0.30  # ruis voor variatie

        kandidaten.sort(key=_kandidaat_score, reverse=True)

        doel_grootte = random.randint(team["max_leden"] // 2, team["max_leden"])
        n = min(doel_grootte - 1, len(kandidaten))
        leden = kandidaten[:n]

        team_leden = [aanv_id]
        for m in leden:
            joined = random_datum(team["aangemaakt_op"], EIND_DATUM)
            lidmaatschappen.append({
                "lidmaatschap_id": lid_id,
                "team_id": team["team_id"],
                "medewerker_id": m["medewerker_id"],
                "toegetreden_op": joined,
                "rol": "lid",
            })
            team_leden.append(m["medewerker_id"])
            org_in_team.add(m["medewerker_id"])  # tracker bijwerken
            lid_id += 1
        leden_per_team[team["team_id"]] = team_leden

    # ----- Fairness-pass: zorg dat actieve medewerkers (score > 0.40)
    # die nog nergens in zitten, alsnog aan een team met ruimte worden
    # toegevoegd. Voorkomt dat top-spelers alle teamplekken vullen en
    # mid-actieve medewerkers nooit in een team komen.
    teams_per_orgid_voor_fairness = {}
    for t in teams:
        teams_per_orgid_voor_fairness.setdefault(t["organisatie_id"], []).append(t)

    for org in organisaties:
        org_id = org["organisatie_id"]
        teams_in_org = teams_per_orgid_voor_fairness.get(org_id, [])
        if not teams_in_org:
            continue
        org_in_team = in_team_per_org.setdefault(org_id, set())
        # Drempel verlaagd naar 0.20 — ook mid-actieve medewerkers krijgen kans
        losse_actieven = [e for e in med_per_org[org_id]
                          if e["_activiteit_score"] > 0.20
                          and e["medewerker_id"] not in org_in_team]
        # Sorteer op activiteits-score descending, zodat actiefste eerst aankomt
        losse_actieven.sort(key=lambda e: -e["_activiteit_score"])

        for med in losse_actieven:
            med_int = interesses_per_med.get(med["medewerker_id"], [])
            # Voorkeur: team met interesse-match én ruimte
            match = [t for t in teams_in_org if t["sport_id"] in med_int
                     and len(leden_per_team.get(t["team_id"], [])) < t["max_leden"]]
            ruim = [t for t in teams_in_org
                    if len(leden_per_team.get(t["team_id"], [])) < t["max_leden"]]
            if match:
                chosen = random.choice(match)
            elif ruim:
                chosen = random.choice(ruim)
            else:
                # Geen ruimte? Pak het kleinste team en breidt het +5 leden uit.
                chosen = min(teams_in_org,
                             key=lambda t: len(leden_per_team.get(t["team_id"], [])))
                chosen["max_leden"] += 5

            joined = random_datum(chosen["aangemaakt_op"], EIND_DATUM)
            lidmaatschappen.append({
                "lidmaatschap_id": lid_id,
                "team_id": chosen["team_id"],
                "medewerker_id": med["medewerker_id"],
                "toegetreden_op": joined,
                "rol": "lid",
            })
            leden_per_team.setdefault(chosen["team_id"], []).append(med["medewerker_id"])
            org_in_team.add(med["medewerker_id"])
            lid_id += 1

    schrijf_csv("team_lidmaatschappen.csv",
                ["lidmaatschap_id", "team_id", "medewerker_id", "toegetreden_op", "rol"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in lidmaatschappen])

    print(f"Engagement klaar: {len(interesses)} interesses, {len(connecties)} connecties, "
          f"{len(teams)} teams, {len(lidmaatschappen)} lidmaatschappen")

    # ============================================================
    # 13. ACTIVITEITEN
    # ============================================================
    print("\n=== Activiteiten-domein ===")
    VEREIST_NIVEAU = [("Allemaal", 0.50), ("Beginner", 0.20), ("Gemiddeld", 0.20), ("Gevorderd", 0.10)]
    ACTIVITEIT_TAGS = ["na-werk", "lunchpauze", "sociaal", "competitief", "beginner-vriendelijk",
                       "buiten", "teambuilding", "weekend", "vroege-vogel", "hoge-intensiteit"]

    locaties_per_stad = {}
    for v in locaties:
        locaties_per_stad.setdefault(v["stad"], []).append(v)
    kantoor_per_id = {o["kantoor_id"]: o for o in kantoren}
    teams_per_orgid = {}
    for t in teams:
        teams_per_orgid.setdefault(t["organisatie_id"], []).append(t)

    med_index = {e["medewerker_id"]: e for e in medewerkers}

    activiteiten = []
    activiteit_id = 1
    activiteit_tags_rijen = []
    tag_id = 1

    for org in organisaties:
        org_meds = med_per_org[org["organisatie_id"]]
        organisatoren = [e for e in org_meds if e["_activiteit_score"] > 0.30]
        if not organisatoren:
            continue

        gem_score = sum(e["_activiteit_score"] for e in org_meds) / len(org_meds)
        per_week = max(3, int(len(org_meds) / 8 * (0.6 + gem_score)))

        for week_offset in range(WEKEN_HISTORIE + WEKEN_TOEKOMST):
            week_start = START_DATUM + timedelta(weeks=week_offset)
            is_toekomst_week = week_start > EIND_DATUM
            wk_num = week_start.isocalendar()[1]
            if wk_num in [52, 1, 30, 31]:  # vakantie-dip
                week_acts = int(per_week * 0.4)
            elif is_toekomst_week:
                # Toekomstige weken: minder activiteiten (mensen plannen niet
                # alles van tevoren). 60% van het normale volume.
                week_acts = max(1, int(random.gauss(per_week * 0.6, 2)))
            else:
                week_acts = max(0, int(random.gauss(per_week, 2)))

            for _ in range(week_acts):
                organisator = random.choice(organisatoren)
                org_int = interesses_per_med.get(organisator["medewerker_id"], [])
                if org_int and random.random() < 0.7:
                    sp_id = random.choice(org_int)
                    sp = next(s for s in sporten if s["sport_id"] == sp_id)
                else:
                    sp = random.choice(sporten)

                day_offset = random.randint(0, 6)
                act_datum = week_start + timedelta(days=day_offset)
                if act_datum < organisator["aanmeld_datum"] or act_datum > HORIZON_DATUM:
                    continue
                wd = act_datum.weekday()
                if wd < 5:
                    uur = gewogen_keuze([(12, 0.30), (17, 0.25), (18, 0.25), (7, 0.10), (19, 0.10)])
                else:
                    uur = gewogen_keuze([(9, 0.20), (10, 0.30), (11, 0.20), (14, 0.20), (15, 0.10)])
                minuut = random.choice([0, 15, 30, 45])
                geplande_tijd = datetime.combine(act_datum, time(uur, minuut))

                org_kantoor = kantoor_per_id.get(organisator["kantoor_id"])
                stad = org_kantoor["stad"] if org_kantoor else random.choice(NL_STEDEN)
                stad_locaties = locaties_per_stad.get(stad, []) or random.choice(list(locaties_per_stad.values()))
                loc = random.choice(stad_locaties) if random.random() < 0.85 else None

                team_id_voor_act = None
                org_teams = teams_per_orgid.get(org["organisatie_id"], [])
                matching = [t for t in org_teams if t["sport_id"] == sp["sport_id"]]
                if matching and random.random() < 0.30:
                    team_id_voor_act = random.choice(matching)["team_id"]

                if geplande_tijd > datetime.combine(EIND_DATUM, time(23, 59, 59)):
                    # Toekomstige activiteit — zo goed als altijd 'gepland',
                    # heel af en toe alvast geannuleerd
                    status = gewogen_keuze([("gepland", 0.95), ("geannuleerd", 0.05)])
                else:
                    status = gewogen_keuze([
                        ("voltooid",     0.78),
                        ("geannuleerd",  0.12),
                        ("niet_gekomen", 0.10),
                    ])

                duur = sp["typische_duur_min"] + random.choice([-15, 0, 0, 0, 15, 30])
                max_dn = max(sp["min_deelnemers"] + 2,
                             random.choice([8, 10, 12, 15, 20, 25, 30]))
                titels = [
                    f"{sp['sport_naam']} {random.choice(['na werk', 'in de lunch', 'sessie', 'club', 'meetup'])}",
                    f"Wekelijkse {sp['sport_naam']}",
                    f"{sp['sport_naam']} voor beginners",
                    f"{sp['sport_naam']} groep {stad}",
                    f"{sp['sport_naam']} - {act_datum.strftime('%a %d/%m')}",
                ]
                titel = random.choice(titels)

                activiteiten.append({
                    "activiteit_id": activiteit_id,
                    "organisatie_id": org["organisatie_id"],
                    "organisator_id": organisator["medewerker_id"],
                    "sport_id": sp["sport_id"],
                    "locatie_id": loc["locatie_id"] if loc else None,
                    "team_id": team_id_voor_act,
                    "titel": titel,
                    "omschrijving": fake.sentence(nb_words=10) if random.random() < 0.6 else None,
                    "geplande_tijd": geplande_tijd,
                    "duur_minuten": duur,
                    "max_deelnemers": max_dn,
                    "min_deelnemers": sp["min_deelnemers"],
                    "vereist_niveau": gewogen_keuze(VEREIST_NIVEAU),
                    "is_terugkerend": random.random() < 0.15,
                    "kosten_per_persoon_eur": round(random.choice([0, 0, 0, 5, 7.5, 10, 15]), 2),
                    "status": status,
                    # Een activiteit wordt 2-14 dagen voor de geplande tijd aangemaakt,
                    # maar nooit later dan 'vandaag' (anders zou je 'm niet kennen)
                    "aangemaakt_op": min(
                        geplande_tijd - timedelta(days=random.randint(2, 14)),
                        datetime.combine(EIND_DATUM, time(23, 59, 59)),
                    ),
                    "_team_id_link": team_id_voor_act,
                    "_max_dn": max_dn,
                })

                n_tags = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
                gekozen_tags = random.sample(ACTIVITEIT_TAGS, n_tags)
                for t in gekozen_tags:
                    activiteit_tags_rijen.append({
                        "tag_id": tag_id,
                        "activiteit_id": activiteit_id,
                        "tag": t,
                    })
                    tag_id += 1
                activiteit_id += 1

    activiteit_kolommen = [
        "activiteit_id", "organisatie_id", "organisator_id", "sport_id", "locatie_id", "team_id",
        "titel", "omschrijving", "geplande_tijd", "duur_minuten", "max_deelnemers",
        "min_deelnemers", "vereist_niveau", "is_terugkerend", "kosten_per_persoon_eur",
        "status", "aangemaakt_op",
    ]
    schrijf_csv("activiteiten.csv", activiteit_kolommen,
                [{k: csv_waarde(r.get(k)) for k in activiteit_kolommen} for r in activiteiten])

    schrijf_csv("activiteit_tags.csv",
                ["tag_id", "activiteit_id", "tag"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in activiteit_tags_rijen])

    # ============================================================
    # 14. DEELNAMES + AANWEZIGHEID + FEEDBACK
    # ============================================================
    deelnames = []
    deelname_id = 1
    aanwezigheid_rijen = []
    aanwezigheid_id = 1
    feedback_rijen = []
    feedback_id = 1

    STEMMINGEN = [("Energiek", 0.30), ("Blij", 0.30), ("Ontspannen", 0.20),
                  ("Moe", 0.15), ("Gestrest", 0.05)]

    for act in activiteiten:
        org_id = act["organisatie_id"]
        org_meds = med_per_org[org_id]
        sp_id = act["sport_id"]
        geplande_tijd = act["geplande_tijd"]
        max_dn = act["_max_dn"]

        kandidaten = set([act["organisator_id"]])
        if act["_team_id_link"]:
            kandidaten.update(leden_per_team.get(act["_team_id_link"], []))
        geinteresseerd = [e["medewerker_id"] for e in org_meds
                          if sp_id in interesses_per_med.get(e["medewerker_id"], [])]
        kandidaten.update(geinteresseerd)
        # Bredere candidate-pool: medewerkers met score > 0.25 (was 0.4),
        # en sample tot 25 random actieven (was 15). Voorkomt dat mid-actieve
        # medewerkers nooit aan toekomstige activiteiten worden gekoppeld.
        actieven = [e["medewerker_id"] for e in org_meds if e["_activiteit_score"] > 0.25]
        kandidaten.update(random.sample(actieven, min(25, len(actieven))))

        doel = int(random.gauss(max_dn * 0.75, max_dn * 0.20))
        doel = max(act["min_deelnemers"] - 2, min(int(max_dn * 1.2), doel))
        kand_lijst = list(kandidaten)
        if len(kand_lijst) < doel:
            doel = len(kand_lijst)
        if doel <= 0:
            continue

        aanmelders = random.sample(kand_lijst, doel)

        for med_id in aanmelders:
            med = med_index.get(med_id)
            if not med:
                continue

            aanmeld_window_start = max(
                datetime.combine(med["aanmeld_datum"], time(8, 0)),
                act["aangemaakt_op"],
            )
            # Aanmelden kan tot vlak voor de activiteit, maar nooit later dan
            # 'vandaag' — toekomstige activiteiten kun je vandaag al boeken,
            # niet morgen.
            aanmeld_window_eind = min(
                geplande_tijd,
                datetime.combine(EIND_DATUM, time(23, 59, 59)),
            )
            if aanmeld_window_start >= aanmeld_window_eind:
                continue
            sec_window = (aanmeld_window_eind - aanmeld_window_start).total_seconds()
            aanmeld_tijd = aanmeld_window_start + timedelta(seconds=random.randint(0, int(sec_window)))

            is_organisator = (med_id == act["organisator_id"])

            if act["status"] == "geannuleerd":
                d_status = gewogen_keuze([("geannuleerd", 0.80), ("bevestigd", 0.20)])
                bijgewoond = False
            elif act["status"] == "gepland":
                d_status = gewogen_keuze([("bevestigd", 0.85), ("wachtlijst", 0.10), ("geannuleerd", 0.05)])
                bijgewoond = None
            else:  # voltooid of niet_gekomen
                d_status = gewogen_keuze([("bevestigd", 0.90), ("geannuleerd", 0.07), ("wachtlijst", 0.03)])
                if d_status == "bevestigd":
                    bijgewoond = random.random() < 0.88 if act["status"] == "voltooid" else False
                else:
                    bijgewoond = False

            deelnames.append({
                "deelname_id": deelname_id,
                "activiteit_id": act["activiteit_id"],
                "medewerker_id": med_id,
                "aanmeld_tijd": aanmeld_tijd,
                "status": d_status,
                "bijgewoond": bijgewoond,
                "is_organisator": is_organisator,
            })

            if bijgewoond:
                check_in = geplande_tijd + timedelta(minutes=random.randint(-10, 15))
                werkelijke_duur = round(act["duur_minuten"] + random.gauss(0, 5), 1)
                werkelijke_duur = max(15, min(180, werkelijke_duur))
                check_out = check_in + timedelta(minutes=werkelijke_duur)

                sp = next(s for s in sporten if s["sport_id"] == sp_id)
                kcal = int(sp["gem_calorieen_per_uur"] * (werkelijke_duur / 60) * sp["intensiteit_factor"])
                leeftijd = (EIND_DATUM - med["geboortedatum"]).days // 365 if med["geboortedatum"] else 35
                max_hr = 220 - leeftijd
                hr_avg = max(70, min(180, int(max_hr * (0.55 + sp["intensiteit_factor"] * 0.15) + random.gauss(0, 5))))
                hr_piek = min(max_hr + 5, hr_avg + random.randint(10, 35))

                aanwezigheid_rijen.append({
                    "aanwezigheid_id": aanwezigheid_id,
                    "deelname_id": deelname_id,
                    "medewerker_id": med_id,
                    "activiteit_id": act["activiteit_id"],
                    "check_in_tijd": check_in,
                    "check_out_tijd": check_out,
                    "werkelijke_duur_min": werkelijke_duur,
                    "geschatte_calorieen": kcal,
                    "hartslag_gem": soms_null(hr_avg, 0.10),
                    "hartslag_piek": soms_null(hr_piek, 0.10),
                })
                aanwezigheid_id += 1

                if random.random() < 0.55:
                    beoordeling = random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 38, 40])[0]
                    energie_na = max(1, min(10, random.randint(beoordeling + 2, beoordeling + 5)))
                    ingediend = check_out + timedelta(hours=random.randint(1, 48))
                    if beoordeling >= 3:
                        stemming = gewogen_keuze(STEMMINGEN)
                    else:
                        stemming = gewogen_keuze([("Moe", 0.4), ("Gestrest", 0.3), ("Ontspannen", 0.3)])
                    feedback_rijen.append({
                        "feedback_id": feedback_id,
                        "deelname_id": deelname_id,
                        "beoordeling": beoordeling,
                        "energie_na_1tot10": energie_na,
                        "stemming_na": stemming,
                        "zou_aanbevelen": beoordeling >= 4,
                        "zou_opnieuw_bezoeken": beoordeling >= 3,
                        "verbondenheid_1tot5": random.choices([1, 2, 3, 4, 5], weights=[5, 10, 25, 35, 25])[0],
                        "opmerking": fake.sentence(nb_words=8) if random.random() < 0.35 else None,
                        "ingediend_op": ingediend,
                    })
                    feedback_id += 1

            deelname_id += 1

    schrijf_csv("deelnames.csv",
                ["deelname_id", "activiteit_id", "medewerker_id", "aanmeld_tijd", "status",
                 "bijgewoond", "is_organisator"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in deelnames])

    schrijf_csv("aanwezigheid.csv",
                ["aanwezigheid_id", "deelname_id", "medewerker_id", "activiteit_id",
                 "check_in_tijd", "check_out_tijd", "werkelijke_duur_min", "geschatte_calorieen",
                 "hartslag_gem", "hartslag_piek"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in aanwezigheid_rijen])

    schrijf_csv("feedback.csv",
                ["feedback_id", "deelname_id", "beoordeling", "energie_na_1tot10", "stemming_na",
                 "zou_aanbevelen", "zou_opnieuw_bezoeken", "verbondenheid_1tot5", "opmerking",
                 "ingediend_op"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in feedback_rijen])

    print(f"Activiteiten klaar: {len(activiteiten)} activiteiten, {len(activiteit_tags_rijen)} tags, "
          f"{len(deelnames)} aanmeldingen, {len(aanwezigheid_rijen)} aanwezigheden, "
          f"{len(feedback_rijen)} feedback")

    # ============================================================
    # 8b. GEZONDHEIDSMETINGEN (verplaatst — gebruikt werkelijke deelname-data)
    # ============================================================
    # We genereren stress/energie NU pas omdat we ze willen koppelen aan
    # hoeveel iemand daadwerkelijk heeft bijgewoond. Iemand die veel sport
    # rapporteert lagere stress en hogere energie — dit is wat de literatuur
    # uit het bedrijfsadvies (§2.2, Stults-Kolehmainen & Sinha 2014) voorspelt.

    # Tel werkelijke aanwezigheden per medewerker
    aanwezigheden_per_med = {}
    for d in deelnames:
        if d["bijgewoond"]:
            aanwezigheden_per_med[d["medewerker_id"]] = (
                aanwezigheden_per_med.get(d["medewerker_id"], 0) + 1
            )

    gezondheid_rijen = []
    gezondheid_id = 1
    for med in medewerkers:
        if med["_activiteit_score"] < 0.20:  # ~20% heeft geen wearable data
            continue

        # Persoonlijke baselines
        stappen_basis = int(random.gauss(7500, 2500))
        stappen_basis = max(2000, min(15000, stappen_basis))
        actieve_min_basis = int(random.gauss(180, 60))
        slaap_basis = round(random.gauss(7.2, 0.7), 1)
        rhr_basis = max(45, min(95, int(random.gauss(68, 8))))
        stress_basis = random.randint(3, 7)
        energie_basis = random.randint(4, 8)
        bron = gewogen_keuze(DATA_BRONNEN)

        # === Koppeling aan werkelijke aanwezigheid ===
        n_bijgewoond = aanwezigheden_per_med.get(med["medewerker_id"], 0)
        # Centreren rond gemiddelde (12 sessies in 26 weken ≈ 1×/2wk).
        # Schaal: 6 sessies ≈ 1 factor-punt swing.
        att_factor = (n_bijgewoond - 12) / 6
        att_factor = max(-2.0, min(2.5, att_factor))

        # Stappen positief, stress negatief, energie positief. Multipliers
        # gekalibreerd zodat de relatie zichtbaar maar niet perfect is —
        # in echte HR-data is r doorgaans ~ -0.3 tot -0.5.
        stappen_basis  += int(att_factor * 900)
        stress_basis   -= round(att_factor * 1.0)
        energie_basis  += round(att_factor * 0.9)
        stappen_basis  = max(2000, min(16000, stappen_basis))
        stress_basis   = max(1, min(10, stress_basis))
        energie_basis  = max(1, min(10, energie_basis))

        aanmeld = med["aanmeld_datum"]
        for week_offset in range(WEKEN_HISTORIE):
            week_start = START_DATUM + timedelta(weeks=week_offset)
            if week_start < aanmeld:
                continue
            if random.random() > 0.85:  # ~85% compliance
                continue

            stappen = max(500, int(random.gauss(stappen_basis, 1500)))
            actieve_min = max(30, int(random.gauss(actieve_min_basis, 50)))
            slaap = round(max(4.0, min(10.0, random.gauss(slaap_basis, 0.6))), 1)
            rhr = max(40, min(105, int(random.gauss(rhr_basis, 4))))
            stress = max(1, min(10, stress_basis + random.randint(-2, 2)))
            energie = max(1, min(10, energie_basis + random.randint(-2, 2)))

            if random.random() < 0.005:  # DQ-issue: 0 stappen-uitschieter
                stappen = 0

            gezondheid_rijen.append({
                "gezondheid_id": gezondheid_id,
                "medewerker_id": med["medewerker_id"],
                "week_startdatum": week_start,
                "gem_stappen_per_dag": stappen,
                "actieve_minuten_totaal": actieve_min,
                "gem_slaap_uren": slaap,
                "rusthartslag_bpm": rhr,
                "stress_1tot10": soms_null(stress, 0.05),
                "energie_1tot10": soms_null(energie, 0.05),
                "data_bron": bron,
            })
            gezondheid_id += 1

    schrijf_csv("gezondheidsmetingen.csv",
                ["gezondheid_id", "medewerker_id", "week_startdatum", "gem_stappen_per_dag",
                 "actieve_minuten_totaal", "gem_slaap_uren", "rusthartslag_bpm",
                 "stress_1tot10", "energie_1tot10", "data_bron"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in gezondheid_rijen])
    print(f"Gezondheidsmetingen klaar: {len(gezondheid_rijen)} wekelijkse rijen")

    # ============================================================
    # 15. PRESTATIES (achievements)
    # ============================================================
    print("\n=== Gamification-domein ===")
    PRESTATIE_DEFINITIES = [
        ("Eerste Stappen",          "Je eerste activiteit voltooid",                 "brons",   50),
        ("Sport Ontdekker",         "5 verschillende sporten geprobeerd",            "zilver", 200),
        ("Reeksmeester",            "8 weken op rij minstens 1 activiteit",          "goud",   500),
        ("Sociale Vlinder",         "Met 10 verschillende collega's gesport",        "zilver", 250),
        ("Vroege Vogel",            "10 ochtendactiviteiten voltooid (vóór 9u)",     "zilver", 200),
        ("Nachtuil",                "10 avondactiviteiten voltooid (na 18u)",        "zilver", 200),
        ("Marathonloper",           "100 km hardlopen totaal",                       "goud",   600),
        ("Teamspeler",              "Lid van 3 teams",                               "zilver", 250),
        ("Aanvoerdersmateriaal",    "Aanvoerder van een team",                       "goud",   400),
        ("Feedback Held",           "20 beoordelingen gegeven",                      "zilver", 200),
        ("Calorie Crusher",         "10.000 calorieën verbrand",                     "goud",   500),
        ("Stappenkampioen",         "1 miljoen stappen totaal",                      "goud",   700),
        ("Padel Pro",               "25 padelactiviteiten voltooid",                 "goud",   450),
        ("Yoga Meester",            "20 yogasessies voltooid",                       "zilver", 300),
        ("Uitdaging Aanvaard",      "Eerste uitdaging voltooid",                     "brons",  100),
        ("Uitdagingskampioen",      "5 uitdagingen voltooid",                        "goud",   800),
        ("Consistent",              "4 weken op rij actief",                         "brons",  100),
        ("Welkom Aan Boord",        "Profiel volledig ingevuld",                     "brons",   50),
        ("Verbinder",               "10 collega's toegevoegd als connectie",         "zilver", 200),
        ("Veteraan",                "1 jaar lid van ActiConnect",                    "goud",   500),
    ]
    prestaties = []
    for i, (naam, oms, niv, pt) in enumerate(PRESTATIE_DEFINITIES, 1):
        prestaties.append({
            "prestatie_id": i,
            "naam": naam,
            "omschrijving": oms,
            "niveau": niv,
            "punten": pt,
            "icoon_url": f"https://acticonnect.nl/badges/{naam.lower().replace(' ', '_')}.png",
        })
    schrijf_csv("prestaties.csv",
                ["prestatie_id", "naam", "omschrijving", "niveau", "punten", "icoon_url"],
                prestaties)

    # ============================================================
    # 16. BEHAALDE_PRESTATIES
    # ============================================================
    aanwezigheid_per_med = {}
    for a in aanwezigheid_rijen:
        aanwezigheid_per_med[a["medewerker_id"]] = aanwezigheid_per_med.get(a["medewerker_id"], 0) + 1

    behaalde_prestaties = []
    bp_id = 1
    for med in medewerkers:
        n_aw = aanwezigheid_per_med.get(med["medewerker_id"], 0)
        if n_aw == 0:
            continue
        mogelijk = []
        if n_aw >= 1: mogelijk.append(1)
        if n_aw >= 5 and med["_activiteit_score"] > 0.4: mogelijk.append(2)
        if n_aw >= 8 and med["_activiteit_score"] > 0.6: mogelijk.append(3)
        if n_aw >= 5:
            mogelijk += [4, 5, 6]
        if n_aw >= 10: mogelijk.append(10)
        if n_aw >= 4: mogelijk.append(17)
        if profiel_per_med.get(med["medewerker_id"]):
            mogelijk.append(18)
        if random.random() < 0.3:
            mogelijk.append(19)
        if (EIND_DATUM - med["aanmeld_datum"]).days > 300:
            mogelijk.append(20)

        n_behaald = min(len(mogelijk), random.randint(1, max(1, len(mogelijk))))
        gekozen = random.sample(mogelijk, n_behaald)
        for prestatie_id in gekozen:
            pres = prestaties[prestatie_id - 1]
            behaalde_prestaties.append({
                "behaalde_prestatie_id": bp_id,
                "medewerker_id": med["medewerker_id"],
                "prestatie_id": prestatie_id,
                "behaald_op": random_datum(med["aanmeld_datum"], EIND_DATUM),
                "punten_toegekend": pres["punten"],
            })
            bp_id += 1

    schrijf_csv("behaalde_prestaties.csv",
                ["behaalde_prestatie_id", "medewerker_id", "prestatie_id", "behaald_op", "punten_toegekend"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in behaalde_prestaties])

    # ============================================================
    # 17. UITDAGINGEN
    # ============================================================
    METING_TYPES = ["stappen", "activiteiten", "diversiteit", "reeks", "minuten", "punten"]
    UITDAGING_TEMPLATES = [
        ("Stappen Uitdaging {q}",  "Loop minstens {target} stappen per dag",        "stappen"),
        ("Sport Variatie {q}",     "Probeer {target} verschillende sporten",        "diversiteit"),
        ("Activiteiten Boost {q}", "Voltooi {target} activiteiten in deze periode", "activiteiten"),
        ("Reeksmeester {q}",       "{target} weken op rij actief",                  "reeks"),
        ("Beweegchallenge {q}",    "{target} actieve minuten totaal",               "minuten"),
        ("Punten Race {q}",        "Verdien {target} punten in deze periode",       "punten"),
        ("New Year, New Me",       "Begin het jaar goed met {target} activiteiten", "activiteiten"),
        ("Lente Challenge",        "Voltooi {target} buitenactiviteiten",           "activiteiten"),
    ]

    uitdagingen = []
    uitdaging_id = 1
    for org in organisaties:
        n = random.randint(2, 6)
        for _ in range(n):
            tn, td, m = random.choice(UITDAGING_TEMPLATES)
            kw = random.choice(["Q1", "Q2", "Q3", "Q4"])
            naam = tn.format(q=kw)
            if   m == "stappen":      doel = random.choice([7000, 8000, 10000, 12000])
            elif m == "diversiteit":  doel = random.choice([3, 4, 5, 6])
            elif m == "activiteiten": doel = random.choice([5, 8, 10, 15])
            elif m == "reeks":        doel = random.choice([4, 6, 8, 10])
            elif m == "minuten":      doel = random.choice([300, 500, 750, 1000])
            else:                     doel = random.choice([500, 1000, 1500, 2000])
            oms = td.format(target=doel)

            duur_wkn = random.choice([4, 6, 8, 12])
            start_d = random_datum(START_DATUM, EIND_DATUM - timedelta(weeks=2))
            eind_d = start_d + timedelta(weeks=duur_wkn)

            if eind_d < EIND_DATUM:
                status = "voltooid"
            elif start_d > EIND_DATUM:
                status = "aankomend"
            else:
                status = "actief"

            uitdagingen.append({
                "uitdaging_id": uitdaging_id,
                "organisatie_id": org["organisatie_id"],
                "naam": naam,
                "omschrijving": oms,
                "meting_type": m,
                "doelwaarde": float(doel),
                "startdatum": start_d,
                "einddatum": eind_d,
                "beloning_punten": random.choice([100, 200, 300, 500, 750]),
                "status": status,
            })
            uitdaging_id += 1

    schrijf_csv("uitdagingen.csv",
                ["uitdaging_id", "organisatie_id", "naam", "omschrijving", "meting_type",
                 "doelwaarde", "startdatum", "einddatum", "beloning_punten", "status"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in uitdagingen])

    # ============================================================
    # 18. UITDAGING_DEELNEMERS
    # ============================================================
    uitdaging_deelnemers = []
    ud_id = 1
    for u in uitdagingen:
        org_meds = med_per_org[u["organisatie_id"]]
        eligible = [e for e in org_meds if e["_activiteit_score"] > 0.25]
        n_dn = int(len(eligible) * random.uniform(0.20, 0.60))
        if n_dn == 0:
            continue
        dn = random.sample(eligible, min(n_dn, len(eligible)))
        for med in dn:
            doel = u["doelwaarde"]
            if u["status"] == "voltooid":
                if med["_activiteit_score"] > 0.6:
                    pct = round(random.uniform(85, 130), 1)
                elif med["_activiteit_score"] > 0.4:
                    pct = round(random.uniform(50, 100), 1)
                else:
                    pct = round(random.uniform(15, 70), 1)
            elif u["status"] == "actief":
                tot_dagen = (u["einddatum"] - u["startdatum"]).days
                verlopen = (EIND_DATUM - u["startdatum"]).days
                verwacht = (verlopen / tot_dagen) * 100
                pct = round(verwacht * random.uniform(0.3, 1.4), 1)
                pct = max(0, min(150, pct))
            else:
                pct = 0.0

            huidig = round((pct / 100) * doel, 1)
            voltooid = pct >= 100

            uitdaging_deelnemers.append({
                "uitdaging_deelnemer_id": ud_id,
                "uitdaging_id": u["uitdaging_id"],
                "medewerker_id": med["medewerker_id"],
                "toegetreden_op": random_datum(u["startdatum"], min(u["einddatum"], EIND_DATUM)),
                "huidige_voortgang": huidig,
                "voortgang_pct": pct,
                "voltooid": voltooid,
                "rang": None,
            })
            ud_id += 1

    # Bereken rangs per uitdaging
    per_uitdaging = {}
    for ud in uitdaging_deelnemers:
        per_uitdaging.setdefault(ud["uitdaging_id"], []).append(ud)
    for _, deelns in per_uitdaging.items():
        deelns.sort(key=lambda x: -x["voortgang_pct"])
        for i, p in enumerate(deelns, 1):
            p["rang"] = i

    schrijf_csv("uitdaging_deelnemers.csv",
                ["uitdaging_deelnemer_id", "uitdaging_id", "medewerker_id", "toegetreden_op",
                 "huidige_voortgang", "voortgang_pct", "voltooid", "rang"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in uitdaging_deelnemers])

    # ============================================================
    # 19. RANGLIJST_SNAPSHOTS (top 20 per org per week)
    # ============================================================
    weekly_aanwezigheid = {}
    for a in aanwezigheid_rijen:
        ci = a["check_in_tijd"]
        ci_d = ci.date() if isinstance(ci, datetime) else ci
        wk_start = ci_d - timedelta(days=ci_d.weekday())
        sleutel = (a["medewerker_id"], wk_start)
        if sleutel not in weekly_aanwezigheid:
            weekly_aanwezigheid[sleutel] = {"count": 0, "minuten": 0.0}
        weekly_aanwezigheid[sleutel]["count"] += 1
        weekly_aanwezigheid[sleutel]["minuten"] += a["werkelijke_duur_min"]

    ranglijst_rijen = []
    rl_id = 1
    for org in organisaties:
        org_id = org["organisatie_id"]
        org_med_ids = {e["medewerker_id"] for e in med_per_org[org_id]}
        for week_offset in range(WEKEN_HISTORIE):
            wk_start = START_DATUM + timedelta(weeks=week_offset)
            week_scores = []
            for med_id in org_med_ids:
                stats = weekly_aanwezigheid.get((med_id, wk_start), {"count": 0, "minuten": 0})
                if stats["count"] == 0:
                    continue
                pt = stats["count"] * 50 + int(stats["minuten"]) // 5
                week_scores.append({
                    "med_id": med_id, "punten": pt,
                    "count": stats["count"], "minuten": int(stats["minuten"]),
                })
            week_scores.sort(key=lambda x: -x["punten"])
            for rang, s in enumerate(week_scores[:20], 1):
                ranglijst_rijen.append({
                    "ranglijst_id": rl_id,
                    "organisatie_id": org_id,
                    "medewerker_id": s["med_id"],
                    "week_startdatum": wk_start,
                    "rang": rang,
                    "totaal_punten": s["punten"],
                    "activiteiten_bijgewoond": s["count"],
                    "actieve_minuten": s["minuten"],
                })
                rl_id += 1

    schrijf_csv("ranglijst_snapshots.csv",
                ["ranglijst_id", "organisatie_id", "medewerker_id", "week_startdatum", "rang",
                 "totaal_punten", "activiteiten_bijgewoond", "actieve_minuten"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in ranglijst_rijen])

    print(f"Gamification klaar: {len(prestaties)} prestaties, {len(behaalde_prestaties)} behaald, "
          f"{len(uitdagingen)} uitdagingen, {len(uitdaging_deelnemers)} deelnames, "
          f"{len(ranglijst_rijen)} ranglijst-rijen")

    # ============================================================
    # 20. ABONNEMENTEN
    # ============================================================
    print("\n=== Business Operations ===")
    NIVEAUS = [("Starter", 4.0, "Middelgroot"), ("Growth", 4.5, "Groot"), ("Enterprise", 5.0, "Enterprise")]
    FACTURATIE = [("jaarlijks", 0.65), ("maandelijks", 0.35)]

    abonnementen = []
    for i, org in enumerate(organisaties, 1):
        if org["grootte_categorie"] == "Middelgroot":
            niv = NIVEAUS[0]
        elif org["grootte_categorie"] == "Groot":
            niv = NIVEAUS[1]
        else:
            niv = NIVEAUS[2]
        niv_naam, basis_prijs, _ = niv

        n_users = MEDEWERKERS_PER_ORG[i - 1]
        gelicenseerd = int(n_users * random.uniform(1.05, 1.30))
        cyclus = gewogen_keuze(FACTURATIE)
        korting = round(random.choice([0, 0, 0, 5, 10, 15]) if cyclus == "jaarlijks" else 0, 2)
        prijs = round(basis_prijs * (1 - korting / 100), 2)

        start_d = org["contract_startdatum"]
        if cyclus == "jaarlijks":
            verlenging = start_d + timedelta(days=365)
            while verlenging < VANDAAG:
                verlenging += timedelta(days=365)
        else:
            verlenging = start_d + timedelta(days=30)
            while verlenging < VANDAAG:
                verlenging += timedelta(days=30)

        contract_mnd = (verlenging - start_d).days // 30
        tcv = round(prijs * gelicenseerd * contract_mnd, 2)

        abonnementen.append({
            "abonnement_id": i,
            "organisatie_id": org["organisatie_id"],
            "niveau": niv_naam,
            "prijs_per_gebruiker_maand_eur": prijs,
            "gelicenseerde_gebruikers": gelicenseerd,
            "facturatie_cyclus": cyclus,
            "startdatum": start_d,
            "verlenging_datum": verlenging,
            "auto_verlengen": random.random() < 0.85,
            "korting_pct": korting,
            "totale_contract_waarde_eur": tcv,
        })

    schrijf_csv("abonnementen.csv",
                ["abonnement_id", "organisatie_id", "niveau", "prijs_per_gebruiker_maand_eur",
                 "gelicenseerde_gebruikers", "facturatie_cyclus", "startdatum", "verlenging_datum",
                 "auto_verlengen", "korting_pct", "totale_contract_waarde_eur"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in abonnementen])

    # ============================================================
    # 21. NOTIFICATIES
    # ============================================================
    notificaties = []
    notif_id = 1
    BEZORG_STATUS = [("bezorgd", 0.40), ("geopend", 0.30), ("geklikt", 0.18),
                     ("mislukt", 0.05), ("geweigerd", 0.03), ("bezorgd", 0.04)]

    deelnames_per_act = {}
    for d in deelnames:
        deelnames_per_act.setdefault(d["activiteit_id"], []).append(d)

    for act in activiteiten:
        act_dn = deelnames_per_act.get(act["activiteit_id"], [])
        for d in act_dn:
            med = med_index.get(d["medewerker_id"])
            if not med:
                continue
            voorkeur = med["notificatie_voorkeur"]
            if voorkeur == "geen":
                continue
            kanalen = []
            if voorkeur == "beide":
                kanalen = ["email", "push"]
            elif voorkeur == "sms":
                kanalen = ["sms"]
            elif voorkeur == "email":
                kanalen = ["email"]
            else:
                kanalen = ["push"]

            for kanaal in kanalen:
                if d["status"] == "bevestigd":
                    notificaties.append({
                        "notificatie_id": notif_id,
                        "medewerker_id": d["medewerker_id"],
                        "activiteit_id": act["activiteit_id"],
                        "kanaal": kanaal,
                        "notificatie_type": "bevestiging",
                        "verstuurd_op": d["aanmeld_tijd"] + timedelta(minutes=random.randint(1, 5)),
                        "bezorg_status": gewogen_keuze(BEZORG_STATUS),
                    })
                    notif_id += 1

                    if act["geplande_tijd"] > d["aanmeld_tijd"] + timedelta(days=1):
                        notificaties.append({
                            "notificatie_id": notif_id,
                            "medewerker_id": d["medewerker_id"],
                            "activiteit_id": act["activiteit_id"],
                            "kanaal": kanaal,
                            "notificatie_type": "herinnering",
                            "verstuurd_op": act["geplande_tijd"] - timedelta(days=1, hours=random.randint(0, 6)),
                            "bezorg_status": gewogen_keuze(BEZORG_STATUS),
                        })
                        notif_id += 1

                if act["status"] == "geannuleerd":
                    notificaties.append({
                        "notificatie_id": notif_id,
                        "medewerker_id": d["medewerker_id"],
                        "activiteit_id": act["activiteit_id"],
                        "kanaal": kanaal,
                        "notificatie_type": "annulering",
                        "verstuurd_op": act["geplande_tijd"] - timedelta(hours=random.randint(2, 48)),
                        "bezorg_status": gewogen_keuze(BEZORG_STATUS),
                    })
                    notif_id += 1

                if act["status"] == "voltooid" and d["bijgewoond"] and random.random() < 0.30:
                    notificaties.append({
                        "notificatie_id": notif_id,
                        "medewerker_id": d["medewerker_id"],
                        "activiteit_id": act["activiteit_id"],
                        "kanaal": kanaal,
                        "notificatie_type": "follow_up",
                        "verstuurd_op": act["geplande_tijd"] + timedelta(hours=random.randint(2, 24)),
                        "bezorg_status": gewogen_keuze(BEZORG_STATUS),
                    })
                    notif_id += 1

    # Generieke notificaties zonder activiteit
    for med in random.sample(medewerkers, 200):
        if med["notificatie_voorkeur"] == "geen":
            continue
        for _ in range(random.randint(1, 4)):
            notificaties.append({
                "notificatie_id": notif_id,
                "medewerker_id": med["medewerker_id"],
                "activiteit_id": None,
                "kanaal": "email",
                "notificatie_type": random.choice(["herinnering", "follow_up", "uitnodiging"]),
                "verstuurd_op": random_datetime(med["aanmeld_datum"], EIND_DATUM),
                "bezorg_status": gewogen_keuze(BEZORG_STATUS),
            })
            notif_id += 1

    schrijf_csv("notificaties.csv",
                ["notificatie_id", "medewerker_id", "activiteit_id", "kanaal", "notificatie_type",
                 "verstuurd_op", "bezorg_status"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in notificaties])

    # ============================================================
    # 22. PLATFORM_GEBEURTENISSEN
    # ============================================================
    GEBEURTENIS_TYPES = [
        ("login", 0.20),
        ("dashboard_bekeken", 0.18),
        ("activiteit_bekeken", 0.20),
        ("rsvp_ja", 0.10),
        ("rsvp_nee", 0.04),
        ("zoeken", 0.08),
        ("profiel_bekeken", 0.06),
        ("ranglijst_bekeken", 0.05),
        ("team_bekeken", 0.04),
        ("activiteit_aangemaakt", 0.02),
        ("uitdagingen_bekeken", 0.03),
    ]
    APPARATEN = [("mobiel", 0.55), ("desktop", 0.35), ("tablet", 0.10)]

    platform_gebeurtenissen = []
    geb_id = 1
    cutoff_90d = EIND_DATUM - timedelta(days=90)

    for med in medewerkers:
        if med["laatste_login"] < cutoff_90d:
            continue
        n_geb = max(0, min(150, int(random.gauss(med["_activiteit_score"] * 80, 20))))
        if n_geb == 0:
            continue

        resterend = n_geb
        while resterend > 0:
            sessie_id = f"sess_{med['medewerker_id']}_{random.randint(10000, 99999)}"
            sessie_grootte = min(resterend, random.randint(2, 12))
            sessie_start_d = random_datum(max(med["aanmeld_datum"], cutoff_90d), EIND_DATUM)
            sessie_start = datetime.combine(sessie_start_d,
                time(random.randint(7, 22), random.randint(0, 59)))
            apparaat = gewogen_keuze(APPARATEN)
            current = sessie_start
            for s_idx in range(sessie_grootte):
                et = "login" if s_idx == 0 else gewogen_keuze(GEBEURTENIS_TYPES)
                duur = random.randint(5, 180)
                platform_gebeurtenissen.append({
                    "gebeurtenis_id": geb_id,
                    "medewerker_id": med["medewerker_id"],
                    "gebeurtenis_type": et,
                    "tijdstip": current,
                    "apparaat": apparaat,
                    "sessie_id": sessie_id,
                    "duur_sec": duur,
                })
                geb_id += 1
                current = current + timedelta(seconds=duur + random.randint(2, 30))
            resterend -= sessie_grootte

    schrijf_csv("platform_gebeurtenissen.csv",
                ["gebeurtenis_id", "medewerker_id", "gebeurtenis_type", "tijdstip",
                 "apparaat", "sessie_id", "duur_sec"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in platform_gebeurtenissen])

    print(f"Business Ops klaar: {len(abonnementen)} abonnementen, {len(notificaties)} notificaties, "
          f"{len(platform_gebeurtenissen)} platform-gebeurtenissen")

    # ============================================================
    # 23. DASHBOARD_DAGELIJKS
    # ============================================================
    print("\n=== Aggregatie ===")
    dagelijks = {}
    for a in aanwezigheid_rijen:
        med_id = a["medewerker_id"]
        d = a["check_in_tijd"].date() if isinstance(a["check_in_tijd"], datetime) else a["check_in_tijd"]
        sleutel = (med_id, d)
        if sleutel not in dagelijks:
            dagelijks[sleutel] = {"act": 0, "min": 0.0, "kcal": 0, "hr_sum": 0, "hr_n": 0}
        dagelijks[sleutel]["act"] += 1
        dagelijks[sleutel]["min"] += a["werkelijke_duur_min"]
        dagelijks[sleutel]["kcal"] += a["geschatte_calorieen"]
        if a["hartslag_gem"]:
            dagelijks[sleutel]["hr_sum"] += a["hartslag_gem"]
            dagelijks[sleutel]["hr_n"] += 1

    punten_per_med = {}
    for bp in behaalde_prestaties:
        punten_per_med[bp["medewerker_id"]] = punten_per_med.get(bp["medewerker_id"], 0) + bp["punten_toegekend"]

    weken_actief_per_med = {}
    for (med_id, ws), v in weekly_aanwezigheid.items():
        weken_actief_per_med.setdefault(med_id, set()).add(ws)

    profiel_doelen = {p["medewerker_id"]: p["weekdoel_minuten"] for p in profielen}

    dashboard_rijen = []
    dash_id = 1

    for (med_id, d), stats in dagelijks.items():
        med = med_index.get(med_id)
        if not med:
            continue
        deze_week = d - timedelta(days=d.weekday())
        weken_actief = weken_actief_per_med.get(med_id, set())
        reeks = 0
        check_wk = deze_week
        while check_wk in weken_actief:
            reeks += 1
            check_wk -= timedelta(weeks=1)

        org_id = med["organisatie_id"]
        relevante_lb = [lb for lb in ranglijst_rijen
                        if lb["organisatie_id"] == org_id and lb["medewerker_id"] == med_id
                        and lb["week_startdatum"] <= d]
        rang_in_org = relevante_lb[-1]["rang"] if relevante_lb else random.randint(20, len(med_per_org[org_id]))

        doel = profiel_doelen.get(med_id)
        if doel:
            wk_min = sum(dagelijks.get((med_id, deze_week + timedelta(days=i)), {"min": 0})["min"] for i in range(7))
            doel_pct = round(min(150, (wk_min / doel) * 100), 1)
        else:
            doel_pct = None

        gem_hr = round(stats["hr_sum"] / stats["hr_n"], 1) if stats["hr_n"] > 0 else None

        dashboard_rijen.append({
            "dashboard_id": dash_id,
            "medewerker_id": med_id,
            "snapshot_datum": d,
            "activiteiten_vandaag": stats["act"],
            "actieve_minuten_vandaag": round(stats["min"], 1),
            "calorieen_vandaag": stats["kcal"],
            "gem_hartslag": gem_hr,
            "reeks_weken": reeks,
            "totaal_punten": punten_per_med.get(med_id, 0),
            "rang_in_org": rang_in_org,
            "doel_voortgang_pct": doel_pct,
        })
        dash_id += 1

    schrijf_csv("dashboard_dagelijks.csv",
                ["dashboard_id", "medewerker_id", "snapshot_datum", "activiteiten_vandaag",
                 "actieve_minuten_vandaag", "calorieen_vandaag", "gem_hartslag", "reeks_weken",
                 "totaal_punten", "rang_in_org", "doel_voortgang_pct"],
                [{k: csv_waarde(v) for k, v in r.items()} for r in dashboard_rijen])

    print(f"Aggregatie klaar: {len(dashboard_rijen)} dashboard-snapshots")

    # ============================================================
    # SAMENVATTING
    # ============================================================
    print("\n" + "=" * 60)
    print("KLAAR! Alle 26 CSV-bestanden zijn gegenereerd in ./output/")
    print("=" * 60)
    totaal_rijen = (
        len(organisaties) + len(kantoren) + len(afdelingen) + len(medewerkers)
        + len(profielen) + len(gezondheid_rijen) + len(sporten) + len(locaties)
        + len(interesses) + len(connecties) + len(teams) + len(lidmaatschappen)
        + len(activiteiten) + len(activiteit_tags_rijen) + len(deelnames)
        + len(aanwezigheid_rijen) + len(feedback_rijen)
        + len(prestaties) + len(behaalde_prestaties) + len(uitdagingen)
        + len(uitdaging_deelnemers) + len(ranglijst_rijen)
        + len(abonnementen) + len(notificaties) + len(platform_gebeurtenissen)
        + len(dashboard_rijen)
    )
    print(f"Totaal: {totaal_rijen:,} rijen verdeeld over 26 tabellen.")
