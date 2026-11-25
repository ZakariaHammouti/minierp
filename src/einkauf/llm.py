"""LLM-Anbindung des Einkaufs: Verbindung, Tools und ein Agenten-Schritt."""

import json

import httpx
from openai import OpenAI

# ===== Verbindung zum Modell =====
# Zum Wechseln (z. B. auf OpenAI) nur diese zwei Zeilen ändern
BASE_URL = "http://localhost:11434/v1"
MODELL = "llama3.2"

client = OpenAI(base_url=BASE_URL, api_key="ollama")  # Ollama prüft den Key nicht

# ===== Verbindung zur MiniERP-API =====
API = "http://127.0.0.1:8000"


# ===== Echte Funktionen (rufen die API auf) =====
# mandant_id ist ein Parameter statt fest "1" – so geht es für jede Firma
def artikel_unter_mindestbestand(mandant_id: int) -> list[dict]:
    antwort = httpx.get(
        f"{API}/einkauf/artikel/unter-mindestbestand",
        headers={"X-Mandant": str(mandant_id)},
    )
    return antwort.json()


def angebote_fuer_artikel(mandant_id: int, artikel_id: int) -> list[dict]:
    antwort = httpx.get(
        f"{API}/einkauf/artikel/{artikel_id}/angebote",
        headers={"X-Mandant": str(mandant_id)},
    )
    return antwort.json()


# ===== Gebrauchsanweisung für das Modell =====
# mandant_id steht hier absichtlich NICHT drin: Das Modell darf die Firma
# nicht selbst wählen, sonst könnte es fremde Daten abfragen.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "artikel_unter_mindestbestand",
            "description": (
                "Benutze dieses Tool, wenn gefragt wird, was nachbestellt werden muss "
                "oder welche Artikel knapp sind. Braucht keine Parameter. "
                "Liefert alle Artikel unter Mindestbestand mit id, name, einheit, bestand und mindestbestand."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "angebote_fuer_artikel",
            "description": (
                "Liefert die Lieferantenangebote für EINEN Artikel, günstigster zuerst. "
                "Nur benutzen, wenn die artikel_id aus einem vorherigen Tool-Ergebnis bekannt ist. "
                "Niemals eine artikel_id erfinden."
            ),
            "parameters": {
                "type": "object",
                "properties": {"artikel_id": {"type": "integer", "description": "ID aus einem vorherigen Tool-Ergebnis"}},
                "required": ["artikel_id"],
            },
        },
    },
]

# Zuordnung: Tool-Name → echte Funktion
FUNKTIONEN = {
    "artikel_unter_mindestbestand": artikel_unter_mindestbestand,
    "angebote_fuer_artikel": angebote_fuer_artikel,
}

# Grundanweisung an das Modell
SYSTEM = (
    "Du bist der Einkaufsassistent. "
    "Beantworte Fragen nur mit Daten aus den Tools. "
    "Für die Frage, was nachbestellt werden muss, nutze artikel_unter_mindestbestand. "
    "Erfinde niemals IDs oder Daten. Antworte kurz auf Deutsch."
)


def fuehre_tool_aus(name: str, argumente_json: str, mandant_id: int) -> str:
    """Führt ein vom Modell angefordertes Tool aus und gibt das Ergebnis als JSON-Text zurück."""
    funktion = FUNKTIONEN[name]                      # passende Funktion nachschlagen
    argumente = json.loads(argumente_json or "{}")   # JSON-Text → Dictionary
    ergebnis = funktion(mandant_id=mandant_id, **argumente)  # Mandant setzt UNSER Code
    return json.dumps(ergebnis, ensure_ascii=False)  # Liste → JSON-Text fürs Modell


def frage_einmal(frage: str, mandant_id: int) -> str:
    """Ein Agenten-Schritt: Frage → evtl. Tool → Antwort. Genau wie im Notebook."""
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": frage},
    ]

    # 1. Erster Aufruf: Modell antwortet direkt oder fordert Tools an
    antwort = client.chat.completions.create(model=MODELL, messages=messages, tools=TOOLS)
    modell_nachricht = antwort.choices[0].message

    # Kein Tool angefordert? Dann ist der Text schon die Antwort
    if not modell_nachricht.tool_calls:
        return modell_nachricht.content or ""

    # 2. Angeforderte Tools ausführen, Ergebnisse in den Verlauf hängen
    messages.append(modell_nachricht)
    for aufruf in modell_nachricht.tool_calls:
        print(f"  [Tool] {aufruf.function.name} {aufruf.function.arguments}")
        messages.append({
            "role": "tool",
            "tool_call_id": aufruf.id,
            "content": fuehre_tool_aus(aufruf.function.name, aufruf.function.arguments, mandant_id),
        })

    # 3. Zweiter Aufruf: Modell formuliert die Antwort mit den echten Daten
    endantwort = client.chat.completions.create(model=MODELL, messages=messages, tools=TOOLS)
    return endantwort.choices[0].message.content or ""


# Wird nur ausgeführt, wenn du die Datei direkt startest (wie main in Java)
if __name__ == "__main__":
    print(frage_einmal("Welche Artikel müssen wir nachbestellen?", mandant_id=2))