from dataclasses import dataclass, field


@dataclass
class Artikel:
    name: str
    preis: float
    bestand: int
    mindestbestand: int = 10

    def muss_nachbestellt_werden(self) -> bool:
        return self.bestand < self.mindestbestand


@dataclass
class Bestellung:
    lieferant: str
    positionen: list[Artikel] = field(default_factory=list)

    def gesamtwert(self) -> float:
        return sum(a.preis * a.mindestbestand for a in self.positionen)


kaffee = Artikel("Kaffee", 12.50, 5)
milch = Artikel("Milch", 1.10, 40)

print(kaffee)
print(kaffee.muss_nachbestellt_werden())
print(milch.muss_nachbestellt_werden())

bestellung = Bestellung("Metro")
for artikel in [kaffee, milch]:
    if artikel.muss_nachbestellt_werden():
        bestellung.positionen.append(artikel)

print(bestellung)
print(bestellung.gesamtwert())
print(Artikel("Kaffee", 12.50, 5) == kaffee)