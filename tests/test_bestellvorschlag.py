from decimal import Decimal


def test_bestellvorschlag_hotel(client):
    # Vorschlag für das Hotel abrufen (Mandant 1)
    antwort = client.get("/einkauf/bestellvorschlag", headers={"X-Mandant": "1"})
    assert antwort.status_code == 200
    daten = antwort.json()

    # Genau diese fünf Artikel liegen in den Demo-Daten unter Mindestbestand
    namen = {p["artikel"] for p in daten["positionen"]}
    assert namen == {"Weizenmehl", "Rinderfilet", "Eier", "Handtuch", "Allzweckreiniger"}

    # Rinderfilet: Bestand 0, Mindestbestand 10 → 2 × 10 − 0 = 20
    rinderfilet = next(p for p in daten["positionen"] if p["artikel"] == "Rinderfilet")
    assert rinderfilet["bestellmenge"] == 20

    # Gesamtsumme muss exakt der Summe aller Beträge entsprechen
    # str(...) vorher, weil Decimal aus Text exakt ist, aus float nicht
    summe = sum(Decimal(str(p["betrag"])) for p in daten["positionen"])
    assert Decimal(str(daten["gesamtsumme"])) == summe


def test_bestellvorschlag_nur_eigene_firma(client):
    # Maschinenbau (Mandant 2) darf keine Hotel-Artikel im Vorschlag sehen
    antwort = client.get("/einkauf/bestellvorschlag", headers={"X-Mandant": "2"})
    namen = {p["artikel"] for p in antwort.json()["positionen"]}
    assert "Rinderfilet" not in namen