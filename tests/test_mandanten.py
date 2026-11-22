def test_hotel_sieht_nur_eigene_artikel(client):
    antwort = client.get("/einkauf/artikel", headers={"X-Mandant": "1"})
    assert antwort.status_code == 200
    artikel = antwort.json()
    assert len(artikel) > 0
    assert all(a["mandant_id"] == 1 for a in artikel)


def test_fremde_kostenstelle_liefert_keine_bestellungen(client):
    antwort = client.get(
        "/einkauf/bestellungen",
        params={"kostenstelle_id": 1},
        headers={"X-Mandant": "2"},
    )
    assert antwort.status_code == 200
    assert antwort.json() == []


def test_fremder_artikel_liefert_keine_angebote(client):
    antwort = client.get("/einkauf/artikel/1/angebote", headers={"X-Mandant": "2"})
    assert antwort.status_code == 200
    assert antwort.json() == []


def test_unbekannter_mandant_gibt_404(client):
    antwort = client.get("/einkauf/artikel", headers={"X-Mandant": "99"})
    assert antwort.status_code == 404


def test_ohne_header_gibt_422(client):
    antwort = client.get("/einkauf/artikel")
    assert antwort.status_code == 422