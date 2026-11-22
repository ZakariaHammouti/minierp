import asyncio  # Standardbibliothek für async, muss nicht installiert werden
import time     # zum Messen der Dauer


# "async def" = diese Funktion kann warten, ohne das Programm zu blockieren
async def frage_lieferant(name: str, sekunden: float) -> str:
    print(f"Frage {name} an ...")      # f-String: {name} wird eingesetzt
    await asyncio.sleep(sekunden)       # WARTEN: simuliert z. B. einen LLM-Aufruf
                                        # während dieser Zeit dürfen andere Aufgaben laufen
    print(f"{name} hat geantwortet")
    return f"{name}: Angebot erhalten"


# Variante 1: einer nach dem anderen
async def nacheinander() -> None:
    start = time.perf_counter()                # Stoppuhr starten
    await frage_lieferant("Metro", 2)          # 2 Sekunden warten, DANN weiter
    await frage_lieferant("Transgourmet", 2)   # nochmal 2 Sekunden
    await frage_lieferant("Selgros", 2)        # nochmal 2 Sekunden
    print(f"Nacheinander: {time.perf_counter() - start:.1f} Sekunden\n")
    # :.1f = mit einer Nachkommastelle ausgeben


# Variante 2: alle gleichzeitig
async def gleichzeitig() -> None:
    start = time.perf_counter()
    ergebnisse = await asyncio.gather(         # startet ALLE drei sofort
        frage_lieferant("Metro", 2),           # und wartet, bis alle fertig sind
        frage_lieferant("Transgourmet", 2),    # (wie CompletableFuture.allOf in Java)
        frage_lieferant("Selgros", 2),
    )
    print(ergebnisse)                          # Liste mit allen drei Rückgaben
    print(f"Gleichzeitig: {time.perf_counter() - start:.1f} Sekunden")


# Hauptfunktion: ruft beide Varianten nacheinander auf
async def main() -> None:
    await nacheinander()
    await gleichzeitig()


asyncio.run(main())  # Einstiegspunkt: startet main() – wie public static void main