title: Funktionen
summary: Was ai-gw heute kann – Endpunkte und Anbieter, Routing, Mandanten und Kosten, Guardrails, Cache, MCP-Gateway, Agent-Identitäten, Beobachtung, GitOps und Betrieb.
toc: ja
---
ai-gw ist ein eigenständiges AI-Gateway nach dem Vorbild bekannter Produkte wie LiteLLM, Kong AI
Gateway und Azure AI Gateway (API Management). Der Schwerpunkt liegt auf einem schlanken,
schnellen heißen Pfad und einer modernen Web-Administration. Alles läuft in **einem Binary**:
Datenebene (Standard-Port 4000) und Steuerebene mit Admin-API, Admin-UI und Metriken (Standard-Port 4001).

## Endpunkte und Formate {#endpunkte}

| Endpunkt | Zweck |
|---|---|
| `POST /v1/chat/completions` | OpenAI-kompatibler Chat, mit SSE-Streaming, Tools und Vision |
| `POST /v1/messages` | Anthropic-Messages-API |
| `POST /v1/responses` | OpenAI Responses (zustandslos) |
| `POST /v1/embeddings` | Embeddings |
| `POST /v1/images/generations`, `/v1/audio/*` | Bilder, Transkription, Übersetzung, Sprachausgabe |
| `GET /v1/models` | für den Key freigegebene Modellgruppen |
| `/mcp`, `/mcp/{server}` | MCP-Gateway (Streamable HTTP) |
| `GET /healthz`, `GET /readyz` | Liveness und Readiness (auch Zustand „degraded“) |

Jede Anfrage wird in eine gemeinsame Zwischendarstellung übersetzt und von dort in das Format
des Anbieters – Tools und Function Calling, Bilder, Streaming-Ereignisse und Usage eingeschlossen.
Ein OpenAI-Client kann so ein Claude-Modell nutzen und umgekehrt; Fehler kommen im Format des
Eingangs zurück.

## Anbieter {#anbieter}

OpenAI, Azure OpenAI (API-Key oder Microsoft Entra ID mit Client-Secret, Zertifikat, Workload
Identity oder Managed Identity, auch für Sovereign Clouds), Claude in Azure AI Foundry, Anthropic,
AWS Bedrock (SigV4 oder API-Key), Google Gemini API und Vertex AI (Service-Account), Mistral,
Ollama, vLLM, generische OpenAI-kompatible Endpunkte und ein eingebauter Mock-Anbieter für Tests.
Eine Anbieter-Übersicht in der UI zeigt Zustand und Verkehrsanteil je Anbieter.

## Routing und Resilienz {#routing}

- **Modellgruppen** mit öffentlichem Namen und Aliasen (z. B. `gpt-4o`, `openai/gpt-4o`) und
  beliebig vielen **Deployments** dahinter: Anbieter, Endpunkt, Anbieter-Modell, Zugangsdaten,
  Gewicht, Priorität, eigene Kapazität in RPM und TPM.
- **Strategien:** gewichtet, geringste Latenz, geringste Last, geringste Kosten.
- **Prioritätsgruppen:** etwa reservierte Kapazität (PTU) vor nutzungsbasierter Abrechnung.
- **Retries** nur vor dem ersten Byte an den Client, mit exponentiellem Backoff und Beachtung von
  `Retry-After`; **Fallback-Ketten** über Modellgruppen hinweg, wahlweise nur für bestimmte
  Fehlerklassen; **Circuit Breaker** je Deployment, Health Checks und getrennte Timeouts für
  Verbindungsaufbau, erstes Byte, Pausen zwischen Chunks und Gesamtzeit.

## Mandanten, Limits und Kosten {#mandanten}

- Organisationen, Teams und Nutzer; **virtuelle API-Keys** mit Modellfreigaben, Ablauf, Rotation,
  Sperre und Widerruf. Keys werden nur als Hash gespeichert, der Klartext erscheint genau einmal.
- **Limits** für Anfragen, Tokens und gleichzeitige Anfragen je Key, Team, Organisation und
  Modellgruppe – in gleitenden Fenstern oder Kalenderzeiträumen, mit `429`, `Retry-After` und
  `x-ratelimit-*`-Headern. Zähler lokal, abgeglichen über Postgres oder exakt über Redis.
- **Kosten und Budgets:** Preistabelle je Modell und Zeitraum (mit Preisvorschlägen),
  Kostenrechnung je Anfrage, Budgets strikt mit Reservierung oder weich, Warnungen per Webhook.
- **Team-Grenzen:** Team-Admins verwalten Keys und Budgets im Rahmen ihres Teams.

## Guardrails und Plugins {#guardrails}

Eine **Plugin-Kette** läuft je Anfrage, Antwort und Stream-Chunk und wird auf den Ebenen global,
Organisation, Team, Key und Modellgruppe gebunden – mit Vererbung, Reihenfolge, Sperre gegen
Überschreiben und festgelegtem Verhalten im Fehlerfall. Eingebaut sind unter anderem `pii`,
`prompt-filter`, `prompt-leak`, `content-safety`, `link-guard`, `language`, `header`,
`request-transform`, `webhook` und `cache`. Eigene Logik lässt sich als signiertes
[WASM-Plugin](doku/wasm-plugins.html) in einer Sandbox ausführen.

Drei **Guardrail-Profile** (Basis, Streng, Offen) dienen als Startpunkt und zeigen vor dem
Anwenden einen Diff. Details: [Guardrails & Sicherheit](sicherheit.html).

## Antwort-Cache {#cache}

- **Exakt:** Schlüssel über Modellgruppe und normalisierte Anfrage, im Speicher (LRU mit
  Größengrenze) oder zusätzlich in Redis; gestreamte Antworten werden als Stream wiedergegeben.
- **Semantisch:** Embedding der letzten Nutzernachricht, Systemprompt als harter Filter; als
  Index ein eigener HNSW-Index im Speicher, pgvector oder Redis Search.
- Immer getrennt je Team (oder enger), nie mandantenübergreifend. Der Header
  `x-aigw-cache` zeigt Treffer oder Fehlschlag.

## MCP-Gateway und Tools {#mcp}

ai-gw ist MCP-Server für Clients und MCP-Client für angebundene MCP-Server. Clients sehen über
einen Endpunkt alle für ihren Key freigegebenen Tools, Prompts und Ressourcen; Freigaben gelten
je Team und Key bis auf Tool-Ebene. Zusätzlich führt ai-gw ein **Inventar aller Tools**, die
Anwendungen in ihren Anfragen mitschicken, erkennt Änderungen an Beschreibungen und setzt
**Tool-Richtlinien** durch. Mehr: [MCP-Gateway](doku/mcp-gateway.html),
[Tool-Inventar und Tool-Richtlinien](doku/tool-richtlinien.html).

## Agent- und Workload-Identitäten {#identitaeten}

Neben API-Keys nimmt ai-gw signierte Access-Tokens (JWT) vertrauenswürdiger Aussteller an –
vor allem aus **Microsoft Entra Agent ID**, aber auch von anderen OAuth-2.0-Ausstellern. Ein
Token wirkt genau wie der Key, dem die Identität zugeordnet ist. Mehr:
[Workload- und Agent-Identitäten](doku/workload-identitaeten.html).

## Beobachtung {#beobachtung}

- **Request-Log** mit Modell, Deployment, Tokens, Kosten, Latenz, Cache-Status und
  Fallback-Versuchen; Inhalte nur, wenn konfiguriert, und dann maskiert. Minuten-Rollups für die
  Dashboards, Aufbewahrungsfristen für Rohdaten.
- **Prometheus** unter `/metrics`, **OpenTelemetry**-Traces und -Logs (OTLP/HTTP) mit Spans für
  Anmeldung, Plugins, Upstream und Time-to-first-token, Export als JSON-Lines und Webhook.
- **Audit-Log** jeder Admin-Änderung mit Vorher/Nachher und Hash-Kette, prüfbar per API und UI.

## Administration und GitOps {#administration}

- **Admin-API** mit OpenAPI-Spezifikation, ETag/If-Match, Cursor-Pagination und Fehlern nach
  RFC 9457; die Typen der UI werden daraus erzeugt.
- **Admin-UI** (Svelte 5, eingebettet): Ressourcen-Editoren, Analytics, Log-Explorer, Playground,
  Befehlspalette, YAML-Import/-Export. Ansicht: [Die Oberfläche](oberflaeche.html).
- **Anmeldung** per OIDC (generisch oder Microsoft Entra ID), Rollen `admin`, `org-admin`,
  `team-admin`, `viewer`, `auditor`, `gitops`; Admin-API-Keys für Automatisierung, einmaliges
  Bootstrap-Token für die Erstinstallation.
- **GitOps:** `aigw config export | diff | apply | validate`, Trockenlauf und Prune, Modus „nur
  YAML“. Geheimnisse stehen im YAML nur als Verweis auf Umgebung oder Datei.

## Betrieb {#betrieb}

- **Datenhaltung:** SQLite als Standard, Postgres für mehrere Instanzen (Änderungen per
  LISTEN/NOTIFY), verschlüsselter Snapshot-Cache für den Start ohne Datenbank.
- **Container-Image** distroless, ohne Root, mit schreibgeschütztem Dateisystem und Healthcheck,
  für amd64 und arm64; Docker-Compose-Beispiele mit Postgres, Redis und OpenTelemetry-Collector,
  Kubernetes-Grundgerüst, Betriebshandbuch und geprüfte Beispielkonfigurationen.
- **Werkzeuge:** `aigw keygen`, `aigw config check`, `aigw config rekey` (Rotation des
  Master-Keys), `aigw audit verify`, `aigw healthcheck`.

Einstieg: [Schnellstart](schnellstart.html) · Hintergründe: [Architektur](architektur.html).
