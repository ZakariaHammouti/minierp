"""Einkaufs-Agent: eigener ReAct-Loop ohne Framework."""

import json
from decimal import Decimal

import httpx
from pydantic import BaseModel, Field, ValidationError

# Verbindung zu Modell und API aus llm.py wiederverwenden (nicht doppelt schreiben)
from src.einkauf.llm import API, MODELL, client

MAX_SCHRITTE = 8  # Sicherung: nach 8 Runden ist Schluss, egal was das Modell will


# =====================================================================
# 1. Echte Funktionen – das, was wirklich passiert
# =====================================================================

def artikel_unter_mindestbestand(mandant_id: int) -> list[dict]:
    artikel = httpx.get(
        f"{API}/einkauf/artikel/unter-mindestbestand",
        headers={"X-Mandant": str(mandant_id)},
    ).json()
    # Bestellmenge im CODE berechnen, nicht vom Modell:
    # wieder auffüllen auf das Doppelte des Mindestbestands
    for a in artikel:
        a["bestellmenge"] = 2 * a["mindestbestand"] - a["bestand"]
    return artikel


def angebote_fuer_artikel(mandant_id: int, artikel_id: int) -> list[dict]:
    return httpx.get(
        f"{API}/einkauf/artikel/{artikel_id}/angebote",
        headers={"X-Mandant": str(mandant_id)},
    ).json()


def bestellentwurf(mandant_id: int, positionen: list[dict]) -> dict:
    """Rechnet einen Bestellentwurf durch. Speichert NICHTS – nur ein Vorschlag."""
    zeilen = []
    gesamt = Decimal("0")  # Decimal für Geld, nie float
    for pos in positionen:
        # Preis nicht vom Modell übernehmen, sondern frisch aus der API holen
        angebote = angebote_fuer_artikel(mandant_id, pos["artikel_id"])
        angebot = next((a for a in angebote if a["lieferant_id"] == pos["lieferant_id"]), None)
        if angebot is None:
            return {"fehler": f"Lieferant {pos['lieferant_id']} führt Artikel {pos['artikel_id']} nicht."}
        betrag = Decimal(str(angebot["preis"])) * pos["menge"]
        gesamt += betrag
        zeilen.append({
            "artikel_id": pos["artikel_id"],
            "lieferant": angebot["lieferant"],
            "menge": pos["menge"],
            "einzelpreis": str(angebot["preis"]),
            "betrag": str(betrag),
        })
    return {"positionen": zeilen, "gesamtsumme": str(gesamt), "hinweis": "Nur Entwurf, nichts bestellt."}


# =====================================================================
# 2. Erlaubte Argumente je Tool – Pydantic prüft, bevor etwas passiert
# =====================================================================

class KeineArgumente(BaseModel):
    pass  # Tool braucht keine Parameter


class AngeboteArgumente(BaseModel):
    artikel_id: int = Field(gt=0, description="ID aus einem vorherigen Tool-Ergebnis")


class Position(BaseModel):
    artikel_id: int = Field(gt=0)
    lieferant_id: int = Field(gt=0, description="lieferant_id aus angebote_fuer_artikel")
    menge: int = Field(gt=0, description="bestellmenge aus artikel_unter_mindestbestand")


class EntwurfArgumente(BaseModel):
    positionen: list[Position] = Field(min_length=1)


# Ein Eintrag pro Tool: (echte Funktion, Argument-Modell, Beschreibung fürs Modell)
WERKZEUGE = {
    "artikel_unter_mindestbestand": (
        artikel_unter_mindestbestand,
        KeineArgumente,
        "Liefert alle Artikel unter Mindestbestand inkl. fertig berechneter bestellmenge. Immer als Erstes benutzen.",
    ),
    "angebote_fuer_artikel": (
        angebote_fuer_artikel,
        AngeboteArgumente,
        "Liefert Lieferantenangebote für EINEN Artikel, günstigster zuerst. artikel_id nie erfinden.",
    ),
    "bestellentwurf": (
        bestellentwurf,
        EntwurfArgumente,
        "Rechnet einen Bestellentwurf durch (speichert nichts). Als Letztes benutzen, mit bestellmenge und günstigster lieferant_id.",
    ),
}

# Gebrauchsanweisung fürs Modell automatisch aus den Pydantic-Modellen erzeugen.
# model_json_schema() macht aus der Klasse das JSON-Schema – kein doppeltes Pflegen.
TOOLS = [
    {
        "type": "function",
        "function": {"name": name, "description": beschreibung, "parameters": modell.model_json_schema()},
    }
    for name, (_, modell, beschreibung) in WERKZEUGE.items()
]

SYSTEM = (
    "Du bist der Einkaufs-Agent. Arbeite Schritt für Schritt mit den Tools: "
    "1) artikel_unter_mindestbestand, 2) für jeden Artikel angebote_fuer_artikel, "
    "3) bestellentwurf mit der bestellmenge aus Schritt 1 und dem günstigsten Lieferanten. "
    "Rechne nicht selbst, übernimm Zahlen nur aus Tool-Ergebnissen. "
    "Erfinde nichts. Fasse am Ende den Entwurf kurz auf Deutsch zusammen."
)


# =====================================================================
# 3. Tool sicher ausführen – dein Code hat das letzte Wort
# =====================================================================

def fuehre_tool_aus(name: str, argumente_json: str, mandant_id: int) -> str:
    # Kontrolle 1: nur bekannte Tools (Allowlist)
    if name not in WERKZEUGE:
        return json.dumps({"fehler": f"Unbekanntes Tool: {name}"})
    funktion, argument_modell, _ = WERKZEUGE[name]

    # Kontrolle 2: lesbares JSON?
    try:
        roh = json.loads(argumente_json or "{}")
    except json.JSONDecodeError:
        return json.dumps({"fehler": "Argumente sind kein gültiges JSON."})

    # Kontrolle 3: gültige Argumente? (Typ, Wertebereich, Pflichtfelder)
    try:
        argumente = argument_modell(**roh).model_dump()
    except ValidationError as fehler:
        return json.dumps({"fehler": f"Ungültige Argumente: {fehler.errors()}"}, default=str)

    # Ausführen – Mandant setzt UNSER Code, nie das Modell
    try:
        ergebnis = funktion(mandant_id=mandant_id, **argumente)
    except httpx.HTTPError as fehler:
        return json.dumps({"fehler": f"API nicht erreichbar: {fehler}"})

    # Kontrolle 4: leeres Ergebnis klar benennen
    if ergebnis == []:
        return json.dumps({"hinweis": "Keine Daten gefunden. Erfinde nichts."})
    return json.dumps(ergebnis, ensure_ascii=False)


# =====================================================================
# 4. Der Loop (ReAct): denken → Tool → Ergebnis → wieder denken …
# =====================================================================

def starte_agent(aufgabe: str, mandant_id: int) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": aufgabe},
    ]

    for schritt in range(1, MAX_SCHRITTE + 1):
        # Modell entscheidet: Tool anfordern oder fertig antworten
        antwort = client.chat.completions.create(model=MODELL, messages=messages, tools=TOOLS)
        nachricht = antwort.choices[0].message

        # Kein Tool mehr angefordert → Aufgabe erledigt, Schleife verlassen
        if not nachricht.tool_calls:
            print(f"[Schritt {schritt}] fertig")
            return nachricht.content or ""

        # Tool-Anfragen in den Verlauf aufnehmen und ausführen
        messages.append(nachricht)
        for aufruf in nachricht.tool_calls:
            print(f"[Schritt {schritt}] Tool: {aufruf.function.name} {aufruf.function.arguments}")
            ergebnis = fuehre_tool_aus(aufruf.function.name, aufruf.function.arguments, mandant_id)
            print(f"            → {ergebnis[:150]}")  # nur Anfang anzeigen, damit es lesbar bleibt
            messages.append({"role": "tool", "tool_call_id": aufruf.id, "content": ergebnis})

    # Schleife ohne Ende verlassen → Notbremse hat gegriffen
    return f"Abgebrochen: nach {MAX_SCHRITTE} Schritten keine fertige Antwort."


if __name__ == "__main__":
    aufgabe = "Erstelle einen Bestellentwurf für alle Artikel unter Mindestbestand, jeweils beim günstigsten Lieferanten."
    print()
    print(starte_agent(aufgabe, mandant_id=1))