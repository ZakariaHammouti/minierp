from decimal import Decimal

from sqlmodel import Field, SQLModel


class Budget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    kostenstelle_id: int = Field(foreign_key="kostenstelle.id")
    jahr: int
    monat: int
    betrag: Decimal = Field(max_digits=12, decimal_places=2)