title: Leistung und Lastvergleich
summary: Messaufbau und Ergebnisse der Latenz- und Lasttests von ai-gw sowie ein Vergleich mit dem LiteLLM-Proxy unter gleichen Bedingungen – mit Methode, Rohwerten und den Grenzen der Aussage.
group: betrieb
order: 10
quelle: Betriebshandbuch „Leistung“ und Messprotokolle (November 2026)
---
Ein Gateway sitzt vor jeder Modellanfrage. Was es kostet – Latenz, CPU, Speicher – zahlt jede
Anwendung mit. ai-gw misst das deshalb regelmäßig mit eigenen, im Repository enthaltenen
Skripten. Die Zahlen auf dieser Seite stammen aus Läufen vom November 2026.

> **Einordnung.** Gemessen wurde gegen einen Test-Upstream, der sofort antwortet. Bei echten
> Modellanbietern mit Antwortzeiten von Hunderten Millisekunden bis Sekunden ist der Aufschlag
> jedes Gateways klein; relevant sind dann vor allem CPU je Anfrage, Speicher, Durchsatz je Kern
> und das Verhalten bei vielen gleichzeitigen Streams.

## Messaufbau {#aufbau}

- **Maschine:** 8 vCPU (AMD EPYC, virtualisiert), 16 GB RAM, Linux. Die Maschine war während
  der Messungen nicht exklusiv; alle Messprozesse liefen deshalb mit Echtzeit-Priorität auf
  festen Kernen. Absolute Werte schwanken zwischen Läufen um 20 bis 30 Prozent, Verhältnisse
  innerhalb eines Laufs sind belastbar.
- **Getrennte Kerne:** Test-Upstream (OpenAI-kompatibel, JSON und SSE) auf zwei Kernen, das
  Gateway auf **zwei Kernen**, der Lastgenerator (Keep-Alive) auf den übrigen.
- **Realistische Kette ohne Plugins:** API-Key-Prüfung, Organisation, Team und Key mit Limits und
  Budgets, Kostenrechnung über einen Preis, Request-Log eingeschaltet, Routing mit aktiven Retries
  und Circuit Breakern.
- **Aufschlag** = Gateway minus direkter Aufruf des Upstreams im selben Szenario (Perzentile
  voneinander abgezogen).

## Latenz des Gateways {#latenz}

Mit dem nativen Binary lag der Aufschlag bei einer Verbindung bei **80 bis 92 µs (p50)** und
**unter 200 µs (p99)**, für JSON wie für die Time-to-first-token bei Streams. Das Ziel
„p99 unter 1 ms“ ist bis 2.000 Anfragen pro Sekunde über 200 Verbindungen erfüllt (Aufschlag
p99 140 bis 380 µs). Bei 10.000 Anfragen pro Sekunde auf nur zwei Kernen steigt der Aufschlag auf
1,3 bis 1,7 ms (p99); nach den Messungen braucht diese Rate rund vier Kerne für p99 unter 1 ms.

## Lasttests {#last}

Lange Streams (200 Chunks im Abstand von 5 ms) über 1.000 und 4.000 gleichzeitige Verbindungen,
Gateway weiterhin auf zwei Kernen:

- **Keine Fehler** und keine abgebrochenen Streams, auch nicht mit 4.000 gleichzeitigen
  Streams. Bei Überlast zeigt sich Backpressure als längere Stream-Dauer, nicht als
  Speicherwachstum.
- **Speicher stabil:** über drei gleiche Runden 178 bis 187 MiB; rund 85 KiB je offenem Stream
  (Client- und Upstream-Verbindung samt Puffern).
- **CPU je Chunk** rund 19 µs, überwiegend Systemaufrufe; JSON-Sättigung mit 1.000 Verbindungen
  rund 22.500 Anfragen pro Sekunde.
- Für Dauerlast empfiehlt sich Postgres statt SQLite, weil sich Request-Log und Budget-Abgleich
  bei SQLite eine Schreibsperre teilen.

## Vergleich mit LiteLLM {#litellm}

LiteLLM ist eines der Vorbilder von ai-gw und ein weit verbreitetes, funktionsreiches
Open-Source-Gateway. Der Vergleich soll zeigen, wie sich die unterschiedlichen technischen
Ansätze (Rust mit Konfiguration im Speicher gegenüber Python) unter **gleichen Bedingungen**
auswirken. Er ist keine Gesamtbewertung: Funktionsumfang, Ökosystem und Betriebserfahrung
gehen in die Zahlen nicht ein.

### Methode {#methode}

| Variante | Aufbau |
|---|---|
| ai-gw mit SQLite | Container aus dem Repository; Key mit Organisations-, Team- und Key-Limits, Budgets, Preis, Request-Log |
| ai-gw mit Postgres | wie oben, Postgres 17 |
| LiteLLM ohne Datenbank | offizielles Image v1.108.8 (LTS); Prüfung gegen den Master-Key – ohne Datenbank die einzige Key-Art |
| LiteLLM mit Postgres | offizielles Datenbank-Image v1.108.8; virtueller Key mit Modellen, Budget, RPM- und TPM-Limit; Spend-Logs an |

- Jeder Gateway-Container auf denselben **zwei Kernen**, Netzwerk des Hosts, eine Instanz.
- LiteLLM nach den veröffentlichten Empfehlungen für den Produktionsbetrieb: zwei Worker (gleich
  der Kernzahl), Produktionsmodus, Logging auf Fehler reduziert, gebündeltes Schreiben der
  Spend-Daten, lokale Preisliste. Redis entfällt bei einer Instanz; ai-gw nutzt ebenfalls den
  lokalen Zähler.
- Gemessen: Aufschlag bei einer Verbindung und bei 200 Anfragen pro Sekunde über 10
  Verbindungen, Durchsatz bei Sättigung mit 10, 100 und 500 Verbindungen, Fehler, CPU je
  Anfrage (cgroup), Speicher (wie `docker stats`), Kaltstart bis zur Readiness und Image-Größe.

### Ergebnisse {#ergebnisse}

**Aufschlag gegenüber direktem Upstream** (JSON = Gesamtzeit, Stream = Time-to-first-token;
p50 / p90 / p99):

| Szenario | direkt | ai-gw SQLite | ai-gw Postgres | LiteLLM | LiteLLM Postgres |
|---|---|---|---|---|---|
| JSON, 1 Verbindung | 51 / 78 / 122 µs | +0,32 / +0,41 / +0,46 ms | +0,30 / +0,42 / +0,50 ms | +8,2 / +12,3 / +17,2 ms | +10,7 / +15,3 / +32,6 ms |
| Stream, 1 Verbindung | 85 / 127 / 248 µs | +0,33 / +0,41 / +0,45 ms | +0,32 / +0,41 / +0,43 ms | +10,4 / +17,7 / +22,2 ms | +11,1 / +18,4 / +26,9 ms |
| JSON, 10 Verb., 200 req/s | 211 / 265 / 352 µs | +0,40 / +0,47 / +0,59 ms | +0,45 / +0,51 / +0,82 ms | +11,1 / +28,9 / +44,0 ms | +25,0 / +55,8 / +101 ms ¹ |
| Stream, 10 Verb., 200 req/s | 204 / 268 / 368 µs | +0,44 / +0,52 / +0,67 ms | +0,41 / +0,53 / +0,60 ms | +24,8 / +59,6 / +99,3 ms ¹ | +36,5 / +82,2 / +133 ms ¹ |

¹ Zielrate nicht erreicht; die Werte enthalten Wartezeit.

**Durchsatz bei Sättigung** (Anfragen pro Sekunde; Fehleranteil in Klammern, sonst keine
Fehler):

| Modus, Verbindungen | ai-gw SQLite | ai-gw Postgres | LiteLLM | LiteLLM Postgres |
|---|---|---|---|---|
| JSON, 10 | 16.413 | 18.076 | 269 | 206 |
| JSON, 100 | 26.313 | 20.210 | 151 (0,5 %) | 157 |
| JSON, 500 | 17.734 | 24.023 | 144 (3,5 %) | 103 (4,6 %) |
| Stream, 10 | 14.087 | 15.501 | 122 | 120 |
| Stream, 100 | 15.264 | 16.364 | 155 | 95 |
| Stream, 500 | 9.562 | 9.824 | 136 | 109 |

**Ressourcen:**

| | ai-gw SQLite | ai-gw Postgres | LiteLLM | LiteLLM Postgres |
|---|---|---|---|---|
| CPU je Anfrage (JSON, 100 Verb.) | 79 µs | 101 µs | 8.810 µs | 10.598 µs |
| CPU je Anfrage (Stream, 100 Verb.) | 134 µs | 124 µs | 13.420 µs | 18.561 µs |
| Speicher im Leerlauf | 35 MiB | 29 MiB | 1.626 MiB | 1.700 MiB |
| Speicher, Höchststand unter Last | 317 MiB | 180 MiB | 1.959 MiB | 2.323 MiB |
| Kaltstart, erster Start (leere DB) | 0,60 s | 0,36 s | 25,6 s | 28,3 s |
| Kaltstart, Neustart | 0,27 s | 0,35 s | 22,6 s | 24,2 s |
| Image entpackt / komprimiert | 111 / 30 MiB | 111 / 30 MiB | 1.730 / 398 MiB | 1.648 / 383 MiB |

### Einordnung {#einordnung}

- Auf denselben zwei Kernen lag der Aufschlag von ai-gw bei einer Verbindung um den Faktor 25
  bis 35 niedriger, der Durchsatz bei Sättigung um den Faktor 60 bis 230 höher und die CPU je
  Anfrage um den Faktor 100 bis 150 niedriger. Die Unterschiede sind deutlich größer als die
  Schwankungen der Messmaschine.
- LiteLLM erreichte ab 100 Verbindungen nicht alle Anfragen (Verbindungsabbrüche, mit Postgres
  bei 500 Verbindungen zusätzlich `503`); ai-gw blieb in allen Läufen fehlerfrei.
- Der Aufschlag von ai-gw im Container (rund 0,3 ms) liegt über dem des nativen Binarys (rund
  0,09 ms) – Ursachen sind Container-cgroup, die geteilte Maschine und Aufwachkosten bei
  geringer Rate.

### Grenzen der Aussage {#grenzen}

- Test-Upstream ohne echte Modellzeit; nur OpenAI-Eingang, keine Plugins, Guardrails oder Cache.
- Nur zwei Kerne und eine Instanz je Gateway. LiteLLM skaliert horizontal über weitere Worker
  und Instanzen (laut Dokumentation eine vCPU und mindestens 4 GiB je Worker); mehr Worker, Redis
  und andere ASGI-Server wurden nicht gemessen.
- LiteLLM ohne Datenbank prüft nur den Master-Key und hat damit weniger zu tun als die
  ai-gw-Kette; die funktional vergleichbare Variante ist LiteLLM mit Postgres.
- Die Maschine war nicht exklusiv; absolute Zahlen schwanken, die Verhältnisse sind belastbar.

## Selbst messen {#reproduktion}

Die Skripte liegen im Repository unter `scripts/` (`bench-e2e.sh`, `bench-latency.sh`,
`bench-coldstart.sh`, `bench-litellm.sh`) und schreiben ihre Ergebnisse nach `target/bench/`.
Die Rohprotokolle der hier gezeigten Läufe liegen unter `docs/betrieb/messwerte/`. Für
belastbare absolute Zahlen empfiehlt sich eine exklusive Maschine.
