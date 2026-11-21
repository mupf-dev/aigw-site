title: WASM-Plugins
summary: Eigene Plugin-Logik als WebAssembly-Komponente – in einer Sandbox im Gateway-Prozess, mit Grenzen für CPU, Zeit und Speicher, Hot Reload und optionaler Ed25519-Signaturpflicht.
group: konzept
order: 30
quelle: Konzept 17 „WASM-Plugins“ und Messwerte
---
Die eingebauten Plugins decken die häufigen Fälle ab; für eigene Regeln gab es bisher den
Webhook – mit einer Netzwerk-Rundreise je Aufruf. WASM-Plugins schließen die Lücke: Betreiber
laden eine **WebAssembly-Komponente** hoch, die ai-gw ohne Fork und ohne externen Dienst in der
Plugin-Kette ausführt – im Prozess, mit wenigen zehn Mikrosekunden je Aufruf und auch im
Stream-Pfad.

```text
Upload (Admin-API, UI) oder Datei in der Startkonfiguration
   └─► Modul in der Datenbank ─► Konfigurations-Snapshot ─► Plugin-Kette (Hot Reload)
Bindung  plugin: wasm, module: <name>
   └─► kompilieren (Cache je SHA-256) ─► describe(config) ─► Instanz je Aufruf
```

## Schnittstelle {#schnittstelle}

Die Schnittstelle ist eine WIT-Welt (`aigw:plugin@0.1.0`) mit zwei Funktionen:

- `describe(config)` wird einmal beim Aufbau der Kette aufgerufen, prüft die Konfiguration und
  meldet die gewünschten Phasen (Anfrage, Antwort, Stream-Ereignis).
- `handle(input)` erhält Phase, Nutzdaten in der Zwischendarstellung des Gateways als JSON,
  Metadaten der Anfrage (Request-ID, Eingangsformat, Modellgruppe, Key, Team, Organisation) und
  nur die ausdrücklich freigegebenen Client-Header.

Das Ergebnis ist eine Aktion: **durchlassen**, **ändern**, **blockieren** (wie eine
Guardrail-Ablehnung), **ablehnen** mit Fehlercode, **fest antworten** (nur in der Anfrage-Phase)
oder **verwerfen** (nur im Stream). Plugins können Header zum Anbieter und zur Antwort setzen –
Anmelde- und Hop-Header bleiben gesperrt.

Die Nutzdaten sind bewusst JSON statt fester WIT-Records: Die Zwischendarstellung hat viele
optionale Felder und wächst mit jedem Anbieter. So bleibt die WIT-Welt stabil, und Plugins
können jede JSON-Bibliothek ihrer Sprache nutzen. Die einzige Host-Funktion ist `log` – gekürzt
und begrenzt, mit dem Modulnamen im Gateway-Log.

## Sandbox und Grenzen {#sandbox}

| Grenze | Umsetzung |
|---|---|
| CPU | **Fuel**: die Laufzeit zählt Instruktionen; ist das Kontingent leer, bricht der Aufruf ab |
| Zeit | **Epoch-Interrupt** mit Frist je Bindung (Standard 100 ms) |
| Speicher | Obergrenze je Instanz (Standard 32 MiB, höchstens 256 MiB) |
| Instanzen | Pooling-Allocator mit fester Zahl gleichzeitiger Instanzen |
| WASI | WASI 0.2 **ohne Freigaben**: kein Dateisystem, keine Umgebung, kein Netz; erlaubt sind nur Uhren und Zufall |
| Importe | nur WASI 0.2 und die Host-Schnittstelle; alles andere scheitert schon beim Laden |
| Zustand | **neue Instanz je Aufruf** – kein Zustand zwischen Anfragen oder Mandanten |

Was bei einem Fehler passiert – Kontingent leer, Zeit abgelaufen, Speichergrenze, Absturz,
ungültige Ausgabe –, entscheidet `failMode` der Bindung; Standard ist `closed`, denn
Sicherheits-Plugins sollen im Zweifel ablehnen. Anfrage- und Antwort-Phase laufen außerhalb der
asynchronen Worker des Gateways, damit ein langsames Modul keine anderen Anfragen aufhält.

## Module, Freigabe und Signaturen {#signaturen}

- **Upload** über Admin-API oder UI mit Pflichtangabe des SHA-256; geprüft werden Name, Größe
  und das Komponenten-Format. Ersetzen und Löschen brauchen `If-Match`; gelöscht wird nur ohne
  verweisende Bindungen.
- **Nur globale Admins laden hoch**, denn ein Modul läuft im Gateway-Prozess. Organisations- und
  Team-Admins dürfen freigegebene Module auf ihrer Ebene **binden**.
- Bindungen können den SHA-256 festschreiben und damit genau eine Version zulassen.
- **Signaturen:** Mit konfigurierten vertrauenswürdigen Schlüsseln verlangt ai-gw eine
  Ed25519-Signatur über den Hash des Moduls (mit eigenem Domänen-Präfix). Der private Schlüssel
  bleibt außerhalb des Gateways, etwa im Build-System; `aigw wasm keygen` und `aigw wasm sign`
  helfen dabei. Das schützt auch gegen Schreibzugriff auf die Datenbank oder ein übernommenes
  Admin-Konto.
- Module aus der Startkonfiguration ermöglichen den Modus „nur YAML“; ein abweichender Hash oder
  eine fehlende Signatur verhindert den Start.

## Bindung {#bindung}

```yaml
apiVersion: aigw/v1alpha1
kind: PluginBinding
metadata: {name: team-keywords}
spec:
  plugin: wasm
  scope: {level: team, target: research}
  failMode: closed
  timeoutMs: 50
  config:
    module: keyword-guard
    config: {block: [geheimprojekt], mask: [intern]}
    phases: [request]
    includeHeaders: [x-client-app]
    maxMemoryMb: 16
```

Meldet ein Modul nur die Antwort-Phase, puffert das Gateway gestreamte Antworten; meldet es auch
Stream-Ereignisse, läuft es live auf jedem Chunk.

## Kompilieren und Hot Reload {#hot-reload}

Eine Engine je Prozess kompiliert jede Komponente einmal je SHA-256 und hält das Ergebnis in
einem Cache; mehrere Bindungen desselben Moduls teilen sich die Kompilierung. Ein neues Modul
unter gleichem Namen wird über den Konfigurations-Snapshot ohne Neustart wirksam; laufende Aufrufe
beenden mit der alten Instanz. Der verschlüsselte Snapshot-Cache enthält die Module, sodass auch
ein Start ohne Datenbank WASM-Plugins ausführen kann.

## Messwerte {#messwerte}

| Fall | Median |
|---|---|
| Leer-Plugin, Anfrage-Phase (inklusive JSON, frischer Instanz und Ergebnis) | ≈ 43 µs |
| Leer-Plugin, ein Stream-Ereignis | ≈ 22 µs |
| Beispiel „keyword-guard“, Anfrage-Phase | ≈ 79 µs |

Das liegt deutlich unter dem Latenzbudget des Gateways und drei bis vier Größenordnungen unter
einem Webhook-Aufruf. Die Beispielmodule sind 70 bis 130 KB groß. Das Feature vergrößert das
Binary um rund 14 MB; wer keine WASM-Plugins braucht, schaltet sie ab oder baut ohne das
Feature.

## Beispiele und Metriken {#beispiele}

Das Repository enthält das Beispiel-Plugin `keyword-guard` (Stichwörter blockieren oder
maskieren, Antwort-Header setzen) und Test-Plugins. Prometheus-Metriken zählen Aufrufe nach
Ergebnis, Fehler nach Art, Dauer, verbrauchtes Fuel, Kompilierungen und abgelehnte Signaturen.

Später denkbar: keyless-Signaturen mit Transparenz-Log, Freigabe im Vier-Augen-Prinzip, weitere
Host-Funktionen und asynchrone Ausführung.
