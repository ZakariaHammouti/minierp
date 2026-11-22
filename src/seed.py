import random
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from faker import Faker
from sqlmodel import Session, SQLModel

from src.controlling.models import Budget
from src.core.db import engine
from src.core.models import Abteilung, Benutzer, Kostenstelle, Mandant, ModulAktiv, Rolle
from src.einkauf.models import (
    Artikel,
    BestellPosition,
    BestellStatus,
    Bestellung,
    Lieferant,
    LieferantArtikel,
)

random.seed(42)
Faker.seed(42)
fake = Faker("de_DE")

# (Artikelnummer, Name, Einheit, Mindestbestand, Grundpreis)
FIRMEN = [
    {
        "name": "Hotel Seeblick",
        "branche": "hotel",
        "abteilungen": {
            "Küche": {
                "kst": "100",
                "budget": 3000,
                "lieferanten": ["Metro", "Transgourmet", "Selgros"],
                "artikel": [
                    ("K-001", "Kaffeebohnen", "kg", 20, 12.50),
                    ("K-002", "Vollmilch", "Liter", 60, 1.10),
                    ("K-003", "Weizenmehl", "kg", 40, 0.80),
                    ("K-004", "Rinderfilet", "kg", 10, 38.00),
                    ("K-005", "Olivenöl", "Liter", 15, 9.50),
                    ("K-006", "Eier", "Stück", 300, 0.30),
                ],
            },
            "Housekeeping": {
                "kst": "200",
                "budget": 5000,
                "lieferanten": ["Hotelwäsche Nord", "Clean Profi", "Metro"],
                "artikel": [
                    ("H-001", "Bettwäsche-Set", "Stück", 20, 24.00),
                    ("H-002", "Handtuch", "Stück", 40, 6.50),
                    ("H-003", "Allzweckreiniger", "Liter", 30, 4.20),
                    ("H-004", "Toilettenpapier", "Packung", 50, 3.80),
                ],
            },
            "Rezeption": {
                "kst": "300",
                "budget": 1100,
                "lieferanten": ["Büro Discount", "Metro"],
                "artikel": [
                    ("R-001", "Druckerpapier", "Packung", 10, 4.50),
                    ("R-002", "Schlüsselkarten", "Stück", 200, 0.60),
                    ("R-003", "Kugelschreiber", "Packung", 5, 2.90),
                ],
            },
        },
    },
    {
        "name": "Klein Maschinenbau GmbH",
        "branche": "maschinenbau",
        "abteilungen": {
            "Entwicklung": {
                "kst": "100",
                "budget": 4500,
                "lieferanten": ["Conrad", "Hoffmann Group"],
                "artikel": [
                    ("E-001", "Prototypen-Platine", "Stück", 10, 45.00),
                    ("E-002", "Messschieber", "Stück", 3, 32.00),
                    ("E-003", "3D-Druck-Filament", "kg", 8, 22.00),
                ],
            },
            "Produktion": {
                "kst": "200",
                "budget": 7000,
                "lieferanten": ["Würth", "Hoffmann Group", "Thyssen Stahlhandel"],
                "artikel": [
                    ("P-001", "Stahlblech 2 mm", "Platte", 20, 58.00),
                    ("P-002", "Schrauben M8", "Packung", 40, 7.40),
                    ("P-003", "Schweißdraht", "kg", 25, 6.90),
                    ("P-004", "Kühlschmierstoff", "Liter", 30, 3.60),
                    ("P-005", "Schutzhandschuhe", "Paar", 50, 2.20),
                ],
            },
            "Verwaltung": {
                "kst": "300",
                "budget": 1500,
                "lieferanten": ["Büro Discount", "Conrad"],
                "artikel": [
                    ("V-001", "Druckerpapier", "Packung", 10, 4.50),
                    ("V-002", "Toner", "Stück", 2, 79.00),
                    ("V-003", "Aktenordner", "Stück", 20, 2.10),
                ],
            },
        },
    },
]


def zufallspreis(grundpreis: float) -> Decimal:
    return Decimal(str(round(grundpreis * random.uniform(0.9, 1.15), 2)))


def monat_vor(monate: int) -> datetime:
    heute = datetime.now(timezone.utc)
    jahr, monat = heute.year, heute.month - monate
    while monat <= 0:
        monat += 12
        jahr -= 1
    return datetime(jahr, monat, 1, tzinfo=timezone.utc)


def lege_firma_an(session: Session, firma: dict) -> None:
    mandant = Mandant(name=firma["name"], branche=firma["branche"])
    session.add(mandant)
    session.flush()  # schickt den Datensatz an die DB und vergibt die ID
    mid = mandant.id

    for modul in ["einkauf", "controlling"]:
        session.add(ModulAktiv(mandant_id=mid, modul=modul))

    session.add(Benutzer(mandant_id=mid, name=fake.name(), email=fake.email(),
                         rolle=Rolle.GESCHAEFTSFUEHRUNG))

    lieferanten: dict[str, Lieferant] = {}

    for index, (abt_name, abt) in enumerate(firma["abteilungen"].items()):
        abteilung = Abteilung(mandant_id=mid, name=abt_name)
        session.add(abteilung)
        session.flush()

        kst = Kostenstelle(mandant_id=mid, abteilung_id=abteilung.id,
                           nummer=abt["kst"], name=abt_name)
        session.add(kst)
        session.flush()

        session.add(Benutzer(mandant_id=mid, abteilung_id=abteilung.id, name=fake.name(),
                             email=fake.email(), rolle=Rolle.ABTEILUNGSLEITUNG))
        session.add(Benutzer(mandant_id=mid, abteilung_id=abteilung.id, name=fake.name(),
                             email=fake.email(), rolle=Rolle.MITARBEITER))

        for name in abt["lieferanten"]:
            if name not in lieferanten:
                lieferant = Lieferant(
                    mandant_id=mid,
                    name=name,
                    email=f"einkauf@{name.lower().replace(' ', '-')}.de",
                    lieferzeit_tage=random.randint(1, 7),
                )
                session.add(lieferant)
                session.flush()
                lieferanten[name] = lieferant

        angebote: list[tuple[Artikel, Lieferant, Decimal]] = []
        for nummer, name, einheit, mindest, grundpreis in abt["artikel"]:
            artikel = Artikel(mandant_id=mid, artikelnummer=nummer, name=name, einheit=einheit,
                              mindestbestand=mindest, bestand=random.randint(0, mindest * 3))
            session.add(artikel)
            session.flush()
            for lname in abt["lieferanten"]:
                preis = zufallspreis(grundpreis)
                session.add(LieferantArtikel(mandant_id=mid, lieferant_id=lieferanten[lname].id,
                                             artikel_id=artikel.id, preis=preis))
                angebote.append((artikel, lieferanten[lname], preis))

        for monate_zurueck in range(6, 0, -1):
            monatsanfang = monat_vor(monate_zurueck)
            session.add(Budget(mandant_id=mid, kostenstelle_id=kst.id, jahr=monatsanfang.year,
                               monat=monatsanfang.month, betrag=Decimal(abt["budget"])))

            anzahl = random.randint(3, 6)
            if index == 0 and monate_zurueck == 3:
                anzahl *= 2  # absichtlicher Ausreißer: erste Abteilung, vor 3 Monaten

            for _ in range(anzahl):
                lieferant = lieferanten[random.choice(abt["lieferanten"])]
                passende = [(a, p) for a, l, p in angebote if l is lieferant]
                bestellung = Bestellung(
                    mandant_id=mid,
                    lieferant_id=lieferant.id,
                    kostenstelle_id=kst.id,
                    status=BestellStatus.GELIEFERT,
                    erstellt_am=monatsanfang + timedelta(days=random.randint(0, 27)),
                )
                session.add(bestellung)
                session.flush()
                for artikel, preis in random.sample(passende, k=min(len(passende), random.randint(1, 3))):
                    session.add(BestellPosition(
                        mandant_id=mid,
                        bestellung_id=bestellung.id,
                        artikel_id=artikel.id,
                        menge=artikel.mindestbestand * random.randint(1, 3),
                        einzelpreis=preis,
                    ))


def befuelle(ziel_engine) -> None:
    SQLModel.metadata.drop_all(ziel_engine)
    SQLModel.metadata.create_all(ziel_engine)
    with Session(ziel_engine) as session:
        for firma in FIRMEN:
            lege_firma_an(session, firma)
        session.commit()


def main() -> None:
    befuelle(engine)
    print("Demo-Daten angelegt.")