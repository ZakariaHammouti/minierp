from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel


class BestellStatus(str, Enum):
    ENTWURF = "entwurf"
    FREIGEGEBEN = "freigegeben"
    BESTELLT = "bestellt"
    GELIEFERT = "geliefert"


class Artikel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    artikelnummer: str
    name: str
    einheit: str
    bestand: int = 0
    mindestbestand: int = 0


class Lieferant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    name: str
    email: str
    lieferzeit_tage: int


class LieferantArtikel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    lieferant_id: int = Field(foreign_key="lieferant.id")
    artikel_id: int = Field(foreign_key="artikel.id")
    preis: Decimal = Field(max_digits=10, decimal_places=2)


class Bestellung(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    lieferant_id: int = Field(foreign_key="lieferant.id")
    kostenstelle_id: int = Field(foreign_key="kostenstelle.id")
    status: BestellStatus = BestellStatus.ENTWURF
    erstellt_am: datetime = Field(default_factory=datetime.now)


class BestellPosition(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    bestellung_id: int = Field(foreign_key="bestellung.id")
    artikel_id: int = Field(foreign_key="artikel.id")
    menge: int
    einzelpreis: Decimal = Field(max_digits=10, decimal_places=2)