from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select

from src.controlling.models import Budget
from src.core.deps import MandantDep, SessionDep
from src.core.models import Kostenstelle
from src.einkauf.models import BestellPosition, Bestellung

router = APIRouter(prefix="/controlling", tags=["Controlling"])


class BudgetAuswertung(BaseModel):
    kostenstelle_id: int
    kostenstelle: str
    jahr: int
    monat: int
    budget: Decimal
    ist: Decimal
    abweichung: Decimal


def ist_kosten(session: Session, mandant_id: int) -> dict[tuple[int, int, int], Decimal]:
    """Ist-Kosten je (Kostenstelle, Jahr, Monat) aus den Bestellungen des Einkaufs."""
    ergebnis: dict[tuple[int, int, int], Decimal] = defaultdict(Decimal)
    abfrage = (
        select(Bestellung, BestellPosition)
        .join(BestellPosition, BestellPosition.bestellung_id == Bestellung.id)
        .where(Bestellung.mandant_id == mandant_id)
    )
    for bestellung, position in session.exec(abfrage).all():
        schluessel = (bestellung.kostenstelle_id, bestellung.erstellt_am.year, bestellung.erstellt_am.month)
        ergebnis[schluessel] += position.menge * position.einzelpreis
    return ergebnis


@router.get("/budget-auswertung")
def budget_auswertung(session: SessionDep, mandant_id: MandantDep) -> list[BudgetAuswertung]:
    ist = ist_kosten(session, mandant_id)
    abfrage = (
        select(Budget, Kostenstelle)
        .join(Kostenstelle, Budget.kostenstelle_id == Kostenstelle.id)
        .where(Budget.mandant_id == mandant_id)
    )
    zeilen = []
    for budget, kostenstelle in session.exec(abfrage).all():
        ist_wert = ist[(kostenstelle.id, budget.jahr, budget.monat)]
        zeilen.append(BudgetAuswertung(
            kostenstelle_id=kostenstelle.id,
            kostenstelle=kostenstelle.name,
            jahr=budget.jahr,
            monat=budget.monat,
            budget=budget.betrag,
            ist=ist_wert,
            abweichung=ist_wert - budget.betrag,
        ))
    return sorted(zeilen, key=lambda z: (z.kostenstelle, z.jahr, z.monat))