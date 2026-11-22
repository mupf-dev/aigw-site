title: Features
summary: What ai-gw does today – endpoints and providers, routing, tenants and cost analysis, guardrails, cache, MCP gateway, agent identities, observability, GitOps and operations.
toc: ja
de: funktionen
---
ai-gw is an independent AI gateway modeled on well-known products such as LiteLLM, Kong AI
Gateway and Azure AI Gateway (API Management). The focus is a lean, fast hot path and a modern
web administration. Everything runs in **one binary**: the data plane (default port 4000) and the
control plane with admin API, admin UI and metrics (default port 4001).

## Endpoints and formats {#endpunkte}

| Endpoint | Purpose |
|---|---|
| `POST /v1/chat/completions` | OpenAI-compatible chat, with SSE streaming, tools and vision |
| `POST /v1/messages` | Anthropic Messages API |
| `POST /v1/responses` | OpenAI Responses (stateless) |
| `POST /v1/embeddings` | embeddings |
| `POST /v1/images/generations`, `/v1/audio/*` | images, transcription, translation, speech |
| `GET /v1/models` | model groups the key may use |
| `/mcp`, `/mcp/{server}` | MCP gateway (Streamable HTTP) |
| `GET /healthz`, `GET /readyz` | liveness and readiness (including a “degraded” state) |

Every request is translated into a shared intermediate representation and from there into the
provider's format – including tools and function calling, images, streaming events and usage. An
OpenAI client can therefore use a Claude model and vice versa; errors come back in the format of
the incoming request.

## Providers {#anbieter}

OpenAI, Azure OpenAI (API key or Microsoft Entra ID with client secret, certificate, workload
identity or managed identity, including sovereign clouds), Claude in Azure AI Foundry, Anthropic,
AWS Bedrock (SigV4 or API key), Google Gemini API and Vertex AI (service account), Mistral,
Ollama, vLLM, generic OpenAI-compatible endpoints and a built-in mock provider for tests. A
provider overview in the UI shows the authentication method, deployments and health (circuit
breakers, health checks) per provider and endpoint; the overview page also shows the traffic share.

## Routing and resilience {#routing}

- **Model groups** with a public name and aliases (e.g. `gpt-4o`, `openai/gpt-4o`) and any number
  of **deployments** behind them: provider, endpoint, provider model, credentials, weight,
  priority, own capacity in RPM and TPM.
- **Strategies:** weighted, least latency, least busy, lowest cost.
- **Priority groups:** for example reserved capacity (PTU) before pay-as-you-go.
- **Retries** only before the first byte reaches the client, with exponential backoff and respect
  for `Retry-After`; **fallback chains** across model groups, optionally only for certain error
  classes; **circuit breakers** per deployment, health checks and separate timeouts for connect,
  first byte, gaps between chunks and total time.

## Tenants, limits and costs {#mandanten}

- Organizations, teams and users; **virtual API keys** with model access, expiry, rotation,
  suspension and revocation. Keys are stored only as hashes; the plaintext is shown exactly once.
- **Limits** for requests, tokens and concurrent requests per key, team, organization and model
  group – in sliding windows or calendar periods, with `429`, `Retry-After` and `x-ratelimit-*`
  headers. Counters are local, synchronized via Postgres or exact via Redis.
- **Costs and budgets:** price table per model and period (with price suggestions), cost per
  request, strict budgets with reservation or soft budgets, alerts via webhook.
- **Cost analysis (FinOps):** a dedicated “Costs” page in the admin UI with trends per team,
  organization, model group, deployment, provider or key, comparison with the previous period,
  cost per request and per 1,000 tokens, a breakdown into input, cache and output, savings from
  caching, plugin costs, a budget forecast to the end of the period and a chargeback export as CSV
  or JSON (with cost center) – also via the admin API.
- **Team boundaries:** team admins manage keys and budgets within their team's limits.

## Guardrails and plugins {#guardrails}

A **plugin chain** runs per request, response and stream chunk and is bound at the global,
organization, team, key and model-group level – with inheritance, ordering, locking against
overrides and a defined failure behavior. Built-ins include `pii`, `prompt-filter`,
`prompt-leak`, `content-safety`, `link-guard`, `language`, `schema-guard` (validates structured
output against its JSON schema), `header`, `request-transform`, `webhook` and `cache`. Custom logic can run as a signed [WASM plugin](docs/wasm-plugins.html) in a
sandbox.

Three **guardrail profiles** (basic, strict, open) serve as a starting point and show a diff
before they are applied. Details: [Guardrails & security](security.html).

## Response cache {#cache}

- **Exact:** key over model group and normalized request, in memory (LRU with a size limit) or
  additionally in Redis; streamed responses are replayed as a stream.
- **Semantic:** embedding of the last user message, the system prompt as a hard filter; the index
  is a built-in in-memory HNSW index, pgvector or Redis Search.
- Always partitioned per team (or narrower), never across tenants. The `x-aigw-cache` header shows
  hit or miss.

## MCP gateway and tools {#mcp}

ai-gw is an MCP server for clients and an MCP client for connected MCP servers. Through one
endpoint, clients see all tools, prompts and resources granted to their key; grants apply per
team and key down to individual tools. In addition, ai-gw keeps an **inventory of all tools**
that applications send in their requests, detects changed descriptions and enforces **tool
policies**. More: [MCP gateway](docs/mcp-gateway.html),
[Tool inventory and tool policies](docs/tool-policies.html).

## Agent and workload identities {#identitaeten}

Besides API keys, ai-gw accepts signed access tokens (JWT) from trusted issuers – above all from
**Microsoft Entra Agent ID**, but also from other OAuth 2.0 issuers. A token acts exactly like
the key its identity is mapped to. More: [Workload and agent identities](docs/workload-identities.html).

## Observability {#beobachtung}

- **Request log** with model, deployment, tokens, cost, latency, cache status and fallback
  attempts; content only if configured, and then masked. Per-minute rollups for the dashboards,
  retention periods for raw data.
- **Prometheus** at `/metrics`, **OpenTelemetry** traces and logs (OTLP/HTTP) with spans for
  authentication, plugins, upstream and time to first token, export as JSON Lines and webhook.
- **Audit log** of every admin change with before/after and a hash chain, verifiable via API and
  UI.

## Administration and GitOps {#administration}

- **Admin API** with an OpenAPI specification, ETag/If-Match, cursor pagination and RFC 9457
  errors; the UI's types are generated from it.
- **Admin UI** (Svelte 5, embedded): resource editors, analytics, log explorer, playground,
  command palette, YAML import/export. See [The admin UI](admin-ui.html).
- **Sign-in** via OIDC (generic or Microsoft Entra ID), roles `admin`, `org-admin`,
  `team-admin`, `viewer`, `auditor`, `gitops`; admin API keys for automation, a one-time
  bootstrap token for the initial setup.
- **GitOps:** `aigw config export | diff | apply | validate`, dry run and prune, a “YAML only”
  mode. Secrets appear in YAML only as references to environment variables or files.

## Operations {#betrieb}

- **Storage:** SQLite by default, Postgres for multiple instances (changes via LISTEN/NOTIFY), an
  encrypted snapshot cache for starting without a database.
- **Container image** distroless, non-root, with a read-only file system and health check, for
  amd64 and arm64; Docker Compose examples with Postgres, Redis and an OpenTelemetry collector, a
  Kubernetes baseline, an operations handbook and validated example configurations.
- **Tools:** `aigw keygen`, `aigw config check`, `aigw config rekey` (master key rotation),
  `aigw audit verify`, `aigw healthcheck`.

Get started: [Quickstart](quickstart.html) · Background: [Architecture](architecture.html).
