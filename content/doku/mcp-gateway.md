title: MCP-Gateway
summary: ai-gw als MCP-Server für Clients und MCP-Client zu angebundenen Servern – mit Freigaben je Team und Key bis auf Tool-Ebene, Zugangsdaten, Limits, Log und SSRF-Schutz.
group: konzept
order: 10
quelle: Konzept 15 „MCP-Gateway“
---
Das Model Context Protocol (MCP) verbindet KI-Anwendungen mit Werkzeugen und Datenquellen.
In Organisationen entsteht schnell ein Wildwuchs aus MCP-Servern, deren Zugangsdaten in jeder
IDE und jedem Agenten einzeln hinterlegt sind. ai-gw bündelt sie: Clients sprechen einen
Endpunkt, sehen genau die für ihren Key freigegebenen Tools, Prompts und Ressourcen, und das
Gateway setzt die Zugangsdaten zum Upstream, wendet Limits an und protokolliert jeden
Tool-Aufruf.

## Rollen {#rollen}

- **MCP-Server** für Clients (Agenten, IDEs) über **Streamable HTTP** unter `/mcp` (alle
  freigegebenen Server zusammengeführt) und `/mcp/{server}` (ein einzelner Server).
- **MCP-Client** zu den angebundenen Upstream-Servern über Streamable HTTP, das ältere HTTP+SSE
  oder **stdio** (als verwalteter Prozess, nur nach ausdrücklicher Freischaltung).

Die Umsetzung ist eine Eigenentwicklung: JSON-RPC 2.0 und die Transporte sind im Gateway selbst
implementiert. Das Gateway braucht beide Seiten gleichzeitig mit eigener Session-, Rechte- und
Pool-Logik und reicht Nachrichten weitgehend unverändert durch – unbekannte Felder bleiben
erhalten. Für ausgehende Verbindungen nutzt es denselben HTTP-Stack mit SSRF-Prüfung wie für die
Modellanbieter.

## Namensraum {#namensraum}

Unter `/mcp` werden Tools und Prompts aller freigegebenen Server zusammengeführt und mit dem
Servernamen präfixiert (`<server>__<tool>`), damit gleichnamige Tools verschiedener Server sich
nicht überdecken. Ressourcen behalten ihre URI; das Gateway merkt sich je Session, welcher Server
sie geliefert hat. Listen der Upstream-Server werden für einige Minuten zwischengespeichert; ein
nicht erreichbarer Server fehlt im zusammengeführten Ergebnis, statt die ganze Liste zu blockieren.

## Freigaben {#freigaben}

```yaml
apiVersion: aigw/v1alpha1
kind: McpGrant
metadata: {name: platform-github}
spec:
  server: github
  subject: {level: team, target: platform}     # team | api-key
  tools: ["get_*", "search_*", "!get_secret*"]  # leer = alle
```

- **Standard: nichts.** Ohne passende Freigabe sieht ein Key keinen Server.
- `tools` sind Glob-Muster auf den Tool-Namen beim Upstream; `!muster` schließt aus. Eine leere
  Liste oder nur Ausschlüsse bedeuten „alle übrigen Tools“.
- **Das Team ist die Obergrenze** – wie bei Modellfreigaben: Gehört ein Key zu einem Team,
  braucht es eine Team-Freigabe für den Server; Key-Freigaben schränken darin weiter ein.
- Aufrufe nicht freigegebener Tools lehnt das Gateway ab, auch wenn ein Client den Namen errät.

## Upstream-Server {#upstream}

Ein `McpServer` beschreibt Transport, Adresse und Zugangsdaten. Geheimnisse (Bearer-Token,
Header-Werte) liegen wie die der Modellanbieter verschlüsselt in der Datenbank oder werden als
Verweis auf Umgebung oder Datei angegeben; beim Speichern prüft das Gateway, ob der Verweis
auflösbar ist. Für stdio-Server startet ai-gw den Prozess selbst und überwacht ihn – das ist
standardmäßig gesperrt und muss in der Startkonfiguration freigeschaltet werden.

## SSRF-Schutz {#ssrf}

Upstream-Adressen werden beim Speichern und bei jedem Verbindungsaufbau nach der Namensauflösung
geprüft. Private, Loopback- und Link-Local-Bereiche sind gesperrt, solange sie nicht ausdrücklich
und eng gefasst freigegeben sind; Weiterleitungen folgt das Gateway nicht. So kann ein
MCP-Server-Eintrag nicht als Sprungbrett ins interne Netz dienen.

## Limits, Log und Metriken {#beobachtung}

- Jeder Tool-Aufruf (und jede Listen-Abfrage) zählt als Anfrage in den Limits von Key, Team und
  Organisation; harte Budgetgrenzen sperren auch Tool-Aufrufe. Zusätzlich gibt es Obergrenzen für
  MCP-Sessions je Key und Team, Zeitlimits und eine maximale Nachrichtengröße.
- Jeder Tool-Aufruf erscheint im Request-Log mit Server, Tool, Status, Dauer und Key; Argumente
  und Ergebnisse nur gemäß Payload-Richtlinie (nur Größen, maskiert oder vollständig).
- Prometheus-Metriken zählen Aufrufe und Dauer je Server, Tool und Status; Traces reichen den
  Trace-Kontext an den Upstream weiter.

## Verwaltung {#verwaltung}

MCP-Server und Freigaben werden über die Admin-API (`mcp-servers`, `mcp-grants`), die Admin-UI
(Seite „MCP-Server“ mit Verbindungszustand und Freigaben) oder als GitOps-Manifest gepflegt. Auch
Agenten, die sich mit einem signierten Token anmelden (siehe
[Workload- und Agent-Identitäten](workload-identitaeten.html)), erhalten die Freigaben des
zugeordneten Keys.

## Abgrenzung zu Tool-Richtlinien {#abgrenzung}

Das MCP-Gateway steuert, welche Tools ein Client **über ai-gw** erreicht. Viele Anwendungen
binden MCP-Server aber selbst an und schicken die Tool-Definitionen nur in der Modellanfrage mit.
Für diesen Fall gibt es das [Tool-Inventar und die Tool-Richtlinien](tool-richtlinien.html).

## Offene Punkte {#offen}

Sessions über mehrere Instanzen (Sticky Sessions oder geteilter Session-Speicher), Wiederaufnahme
von SSE-Strömen, OAuth zum Upstream, Freigaben auf Ressourcen- und Prompt-Ebene und die
Plugin-Kette auf Tool-Argumente und -Ergebnisse sind noch nicht umgesetzt.
