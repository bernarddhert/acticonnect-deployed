# ActiConnect — EDA & Streamlit Dashboard

Eindoplevering. Twee deliverables:

- **`EDA.ipynb`** — verkennende data-analyse van de ActiConnect mock-database (~430.000 rijen over 26 tabellen).
- **`streamlit_app/`** — persoonlijk medewerkers-dashboard (4 tabs: Vitaliteit, Verbondenheid, Mijn sport, Prestaties).

## Vereisten

Python 3.10 of nieuwer. Installeer dependencies:

```bash
pip install -r requirements.txt
```

## EDA bekijken

```bash
jupyter notebook EDA.ipynb
```

Of open het bestand direct in VS Code / GitHub — outputs (grafieken) zijn al ingebed.

De notebook leest CSV-bestanden uit `output/` (al meegeleverd, geen extra stappen nodig).

## Dashboard starten

Het dashboard leest van een SQLite-database (`acticonnect.db`). Die zit niet in de repo (te groot voor GitHub), maar wordt **automatisch opgebouwd** uit de meegeleverde CSV's bij de eerste run:

```bash
cd streamlit_app
streamlit run app.py
```

Bij de allereerste start duurt het ongeveer 30 seconden, daarna start het meteen. Het script `load_to_sqlite.py` wordt eenmalig automatisch getriggerd vanuit `app.py`.

Browser opent op <http://localhost:8501>.

In de zijbalk kun je een organisatie en medewerker selecteren. Voor de demo is **Bakker Retail Holding → Adam van Veen** een goede keuze — die heeft een rijk profiel met teams, prestaties en een hoge verbondenheids-score.

## Optioneel: nieuwe mock-data genereren

Wil je een nieuwe set CSV's genereren met andere willekeurige getallen?

```bash
python generate_mockdata.py
```

Het script overschrijft alle bestanden in `output/`. Daarna `load_to_sqlite.py` opnieuw draaien om de database bij te werken.

Niet nodig om dit voor de inlevering te doen, de meegeleverde CSV's zijn de versie waarop de EDA en het dashboard zijn gebouwd.

## Online versie

Het dashboard is ook live gedeployed op Streamlit Community Cloud:

> _(URL toevoegen zodra je gedeployed hebt)_

## Mapstructuur

```
├── README.md              (dit bestand)
├── .gitignore             (uitsluitingen voor git)
├── requirements.txt       (Python dependencies)
├── generate_mockdata.py   (script dat output/*.csv genereert)
├── load_to_sqlite.py      (script dat acticonnect.db opbouwt vanuit CSV's)
├── EDA.ipynb              (de notebook)
├── output/                (26 CSV-bestanden, bron voor EDA + database)
└── streamlit_app/         (dashboard-code)
    ├── app.py
    ├── .streamlit/config.toml
    └── utils/
        ├── db.py
        ├── theme.py
        └── components.py
```
