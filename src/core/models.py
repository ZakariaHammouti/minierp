from enum import Enum

from sqlmodel import Field, SQLModel


class Rolle(str, Enum):
    MITARBEITER = "mitarbeiter"
    ABTEILUNGSLEITUNG = "abteilungsleitung"
    GESCHAEFTSFUEHRUNG = "geschaeftsfuehrung"


class Mandant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    branche: str


class Abteilung(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    name: str


class ModulAktiv(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    modul: str
    aktiv: bool = True


class Benutzer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mandant_id: int = Field(foreign_key="mandant.id", index=True)
    abteilung_id: int | None = Field(default=None, foreign_key="abteilung.id")
    name: str
    email: str
    rolle: Rolle = Rolle.MITARBEITER

class Kostenstelle(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        mandant_id: int = Field(foreign_key="mandant.id", index=True)
        abteilung_id: int = Field(foreign_key="abteilung.id")
        nummer: str
        name: str