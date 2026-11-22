from pydantic import BaseModel, Field, ValidationError


class Artikel(BaseModel):
    name: str
    preis: float = Field(gt=0)
    bestand: int = Field(ge=0)
    mindestbestand: int = 10


# 1. Normal erzeugen
kaffee = Artikel(name="Kaffee", preis=12.50, bestand=5)
print(kaffee)

# 2. Text wird automatisch umgewandelt
milch = Artikel(name="Milch", preis="1.10", bestand="40")
print(milch.preis, type(milch.preis))

# 3. Aus JSON erzeugen, so liefert ein LLM später Daten
json_text = '{"name": "Zucker", "preis": 0.90, "bestand": 12}'
zucker = Artikel.model_validate_json(json_text)
print(zucker)

# 4. Wieder in JSON umwandeln
print(zucker.model_dump_json())

# 5. Ungültige Daten
try:
    Artikel(name="Tee", preis="abc", bestand=-3)
except ValidationError as fehler:
    print(fehler)