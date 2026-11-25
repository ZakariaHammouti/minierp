from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import col, select

from src.einkauf.service import Bestellvorschlag, erstelle_bestellvorschlag

from src.core.deps import MandantDep, SessionDep
from src.einkauf.models import (
    Artikel,
    BestellPosition,
    BestellStatus,
    Bestellung,
    Lieferant,
    LieferantArtikel,
)

router = APIRouter(prefix="/einkauf", tags=["Einkauf"])


class Angebot(BaseModel):
    lieferant_id: int
    lieferant: str
    preis: Decimal
    lieferzeit_tage: int


@router.get("/artikel")
def alle_artikel(session: SessionDep, mandant_id: MandantDep) -> list[Artikel]:
    abfrage = select(Artikel).where(Artikel.mandant_id == mandant_id)
    return list(session.exec(abfrage).all())


@router.get("/artikel/unter-mindestbestand")
def artikel_unter_mindestbestand(session: SessionDep, mandant_id: MandantDep) -> list[Artikel]:
    abfrage = select(Artikel).where(
        Artikel.mandant_id == mandant_id,
        Artikel.bestand < Artikel.mindestbestand,
    )
    return list(session.exec(abfrage).all())


@router.get("/artikel/{artikel_id}/angebote")
def angebote_fuer_artikel(artikel_id: int, session: SessionDep, mandant_id: MandantDep) -> list[Angebot]:
    abfrage = (
        select(LieferantArtikel, Lieferant)
        .join(Lieferant, LieferantArtikel.lieferant_id == Lieferant.id)
        .where(LieferantArtikel.mandant_id == mandant_id, LieferantArtikel.artikel_id == artikel_id)
        .order_by(LieferantArtikel.preis)
    )
    return [
        Angebot(lieferant_id=l.id, lieferant=l.name, preis=la.preis, lieferzeit_tage=l.lieferzeit_tage)
        for la, l in session.exec(abfrage).all()
    ]


@router.get("/lieferanten")
def alle_lieferanten(session: SessionDep, mandant_id: MandantDep) -> list[Lieferant]:
    abfrage = select(Lieferant).where(Lieferant.mandant_id == mandant_id)
    return list(session.exec(abfrage).all())

class BestellUebersicht(BaseModel):
    id: int
    lieferant: str
    kostenstelle_id: int
    status: BestellStatus
    erstellt_am: datetime
    summe: Decimal


@router.get("/bestellungen")
def alle_bestellungen(
    session: SessionDep,
    mandant_id: MandantDep,
    kostenstelle_id: int | None = None,
) -> list[BestellUebersicht]:
    abfrage = (
        select(Bestellung, Lieferant)
        .join(Lieferant, Bestellung.lieferant_id == Lieferant.id)
        .where(Bestellung.mandant_id == mandant_id)
    )
    if kostenstelle_id is not None:
        abfrage = abfrage.where(Bestellung.kostenstelle_id == kostenstelle_id)
    abfrage = abfrage.order_by(col(Bestellung.erstellt_am).desc())

    summen: dict[int, Decimal] = defaultdict(Decimal)
    positionen = session.exec(select(BestellPosition).where(BestellPosition.mandant_id == mandant_id)).all()
    for position in positionen:
        summen[position.bestellung_id] += position.menge * position.einzelpreis

    return [
        BestellUebersicht(
            id=bestellung.id,
            lieferant=lieferant.name,
            kostenstelle_id=bestellung.kostenstelle_id,
            status=bestellung.status,
            erstellt_am=bestellung.erstellt_am,
            summe=summen[bestellung.id],
        )
        for bestellung, lieferant in session.exec(abfrage).all()
    ]

# Controller ruft nur den Service auf – die Rechenlogik steckt in service.py
@router.get("/bestellvorschlag")
def bestellvorschlag(session: SessionDep, mandant_id: MandantDep) -> Bestellvorschlag:
    return erstelle_bestellvorschlag(session, mandant_id)