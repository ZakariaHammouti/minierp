from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from src.core.deps import MandantDep, SessionDep
from src.einkauf.models import Artikel, Lieferant, LieferantArtikel

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