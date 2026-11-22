title: Status & Roadmap
summary: Wo ai-gw im November 2026 steht – was umgesetzt ist, was bis zum ersten Release fehlt und welche Themen danach anstehen.
toc: ja
---
## Stand im November 2026 {#stand}

ai-gw ist seit November 2026 öffentlich. Der geplante Funktionsumfang der ersten Version 0.1
ist **umgesetzt und getestet**: Datenebene mit OpenAI- und Anthropic-Eingang, alle genannten
Anbieter, Routing und Resilienz, Mandanten, Limits und Budgets, Plugin-Kette mit Guardrails,
Antwort-Cache, MCP-Gateway, Admin-API und Admin-UI, GitOps, Beobachtung, SQLite und Postgres,
Container-Image. Seitdem sind unter anderem WASM-Plugins mit Signaturen, Tool-Inventar und
Tool-Richtlinien, weitere Guardrails (`prompt-leak`, `link-guard`, `language`, `schema-guard`,
unsichtbare Zeichen), Guardrail-Profile, Microsoft Entra ID an vielen Stellen,
Workload-/Agent-Identitäten (Microsoft Entra Agent ID), die Kostenanalyse mit Budget-Prognose und
Chargeback-Export sowie das Container-Image für arm64 hinzugekommen. Das vollständige
[Changelog](https://github.com/mupf-dev/ai-gw/blob/main/CHANGELOG.md) steht im Repository.

> **Noch kein Release.** Es gibt noch keine veröffentlichte Version und keine fertigen
> Container-Images; gebaut wird aus dem Quellcode. Bis 1.0 können sich Konfiguration,
> Manifest-Format (`aigw/v1alpha1`) und Admin-API zwischen Minor-Versionen inkompatibel ändern.

## Umgesetzt {#umgesetzt}

| Bereich | Stand |
|---|---|
| Endpunkte | Chat Completions, Messages, Responses, Embeddings, Bilder, Audio, Models; Streaming mit Backpressure |
| Anbieter | OpenAI, Azure OpenAI, Claude in Azure AI Foundry, Anthropic, AWS Bedrock, Gemini, Vertex AI, Mistral, Ollama, vLLM, OpenAI-kompatibel |
| Routing | Modellgruppen, vier Strategien, Prioritäten, Retries, Fallbacks, Circuit Breaker, Health Checks |
| Zugriff | Organisationen, Teams, Nutzer, virtuelle Keys, Workload-/Agent-Identitäten (JWT, Entra Agent ID) |
| Limits und Kosten | Anfrage-, Token- und Parallelitäts-Limits, Budgets, Preise mit Vorschlägen, drei Zähler-Backends, Kostenanalyse mit Prognose und Chargeback-Export |
| Guardrails | `pii`, `prompt-filter`, `prompt-leak`, `link-guard`, `language`, `schema-guard`, `content-safety`, Profile |
| Erweiterung | Plugin-Kette, Webhooks, WASM-Plugins in der Sandbox mit Ed25519-Signaturen |
| Tools und MCP | MCP-Gateway mit Freigaben, Tool-Inventar, Tool-Richtlinien |
| Cache | exakt (RAM, Redis) und semantisch (HNSW, pgvector, Redis Search) |
| Betrieb | Admin-UI, Admin-API (OpenAPI), OIDC und Rollen, GitOps, Audit-Log mit Hash-Kette, Prometheus, OpenTelemetry, Compose, Kubernetes |
| Leistung | Lastmessungen und Vergleich mit LiteLLM unter gleichen Bedingungen ([Messwerte](doku/leistung.html)) |

## Bis zum ersten Release {#release}

- Release 0.1.0 mit fertigen Container-Images für amd64 und arm64.
- Rechtliche Bestätigung der Lizenz der eingebetteten Tokenizer-Tabellen (MIT); sie lassen sich
  bereits abschalten.
- Sicherheitsrichtlinie und vertraulicher Meldeweg im Repository.

## Danach {#danach}

Themen, die in den Konzepten als offen oder „später“ markiert sind – ohne feste Reihenfolge:

- **MCP-Server für die Administration**, erzeugt aus der OpenAPI-Spezifikation, damit Admin-API,
  UI und MCP gleichwertig sind.
- **MCP-Gateway:** Sessions über mehrere Instanzen, Wiederaufnahme von SSE-Strömen, OAuth zum
  Upstream, Freigaben auf Ressourcen- und Prompt-Ebene, Plugin-Kette auf Tool-Argumente und
  -Ergebnisse.
- **WASM-Plugins:** keyless-Signaturen mit Transparenz-Log zusätzlich zu eigenen Schlüsseln,
  Freigabe im Vier-Augen-Prinzip, weitere Host-Funktionen, asynchrone Ausführung.
- **Leistung:** schnellerer Stream-Pfad (weniger kleine Allokationen je Chunk), gebündelte
  Zähler-Aufrufe für Redis, Request-Log-Writer auf eigenem Kern.
- **Logs:** optionales Backend für sehr große Log-Mengen.
- **Einbindung in Plattformen:** ai-gw ist API-first, ein Binary und deklarativ konfigurierbar,
  damit Plattformen es einbinden können – etwa [BYOC (Build Your Own Cloud)](https://mupf-dev.github.io/cloud-project-site/),
  dessen Dienstkatalog ein AI-Gateway vorsieht.

Wünsche und Prioritäten aus der Praxis sind willkommen: [Mitmachen](mitmachen.html).
