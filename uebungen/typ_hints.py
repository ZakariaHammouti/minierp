def gesamtpreis(preis: float, menge: int) -> float:
    return preis * menge

print(gesamtpreis(4.20, 100))
print(gesamtpreis("4.20", 100))


def gesamtpreis(preis: float, menge: int, rabatt: float | None = None) -> float:
    summe = preis * menge
    if rabatt is not None:
        summe = summe * (1 - rabatt)
    return summe


artikel: list[str] = ["Kaffee", "Milch", "Zucker"]
preise: dict[str, float] = {"Kaffee": 12.50, "Milch": 1.10, "Zucker": 0.90}

print(gesamtpreis(12.50, 10))
print(gesamtpreis(12.50, 10, 0.1))

for name in artikel:
    print(name, preise[name])