"""Geschäftslogik des Einkaufs – rechnet, unabhängig von API und Agent.
Entspricht der Service-Schicht in Spring Boot."""

from decimal import Decimal

from pydantic import BaseModel
from sqlmodel import Session, select

from src.einkauf.models import Artikel, Lieferant, LieferantArtikel


# ===== Antwortmodelle (DTOs) =====

class VorschlagPosition(BaseModel):
    """Eine Zeile im Bestellvorschlag."""
    artikel_id: int
    artikel: str
    einheit: str
    bestand: int
    mindestbestand: int
    bestellmenge: int       # im Code berechnet, nicht vom Modell
    lieferant_id: int
    lieferant: str          # der günstigste Lieferant
    einzelpreis: Decimal
    betrag: Decimal         # bestellmenge × einzelpreis


class Bestellvorschlag(BaseModel):
    """Der komplette Vorschlag mit allen Positionen und der Gesamtsumme."""
    positionen: list[VorschlagPosition]
    gesamtsumme: Decimal


# ===== Logik =====

def erstelle_bestellvorschlag(session: Session, mandant_id: int) -> Bestellvorschlag:
    # 1. Alle Artikel dieser Firma holen, deren Bestand unter dem Mindestbestand liegt
    knappe_artikel = session.exec(
        select(Artikel).where(
            Artikel.mandant_id == mandant_id,
            Artikel.bestand < Artikel.mindestbestand,
        )
    ).all()

    positionen = []
    for artikel in knappe_artikel:
        # 2. Angebote für diesen Artikel holen, nach Preis sortiert → .first() ist das günstigste
        treffer = session.exec(
            select(LieferantArtikel, Lieferant)
            .join(Lieferant, LieferantArtikel.lieferant_id == Lieferant.id)
            .where(
                LieferantArtikel.mandant_id == mandant_id,
                LieferantArtikel.artikel_id == artikel.id,
            )
            .order_by(LieferantArtikel.preis)
        ).first()

        # Kein Lieferant führt den Artikel → kann nicht bestellt werden, überspringen
        if treffer is None:
            continue
        angebot, lieferant = treffer  # Tupel auspacken: (Preiszeile, Lieferant)

        # 3. Bestellmenge: wieder auffüllen auf das Doppelte des Mindestbestands
        menge = 2 * artikel.mindestbestand - artikel.bestand

        positionen.append(VorschlagPosition(
            artikel_id=artikel.id,
            artikel=artikel.name,
            einheit=artikel.einheit,
            bestand=artikel.bestand,
            mindestbestand=artikel.mindestbestand,
            bestellmenge=menge,
            lieferant_id=lieferant.id,
            lieferant=lieferant.name,
            einzelpreis=angebot.preis,
            betrag=angebot.preis * menge,   # Decimal × int bleibt exakt
        ))

    # 4. Gesamtsumme: alle Beträge addieren, Startwert 0 als Decimal
    gesamt = sum((p.betrag for p in positionen), Decimal("0"))
    return Bestellvorschlag(positionen=positionen, gesamtsumme=gesamt)