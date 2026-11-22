title: Architecture
summary: How ai-gw is built – one binary with data and control plane, an in-memory configuration snapshot, a hot path without database access and streaming with backpressure.
toc: ja
de: architektur
---
## Goals {#ziele}

ai-gw aims to cost as little as possible on the hot path and to stay simple to operate. The
quality goals of the first version:

| Goal | Target |
|---|---|
| Additional latency from the gateway (without plugins and cache) | p50 < 200 µs, p99 < 1 ms |
| Overhead on time to first token | < 1 ms – chunks are passed on immediately |
| Concurrent streams | ≥ 10,000 per instance with 2 vCPU and 1 GB RAM |
| Cold start until ready | < 500 ms (SQLite) |
| Configuration changes take effect | < 1 s on all instances |
| Database access on the hot path | none – authentication, routing, limits and policies come from RAM |
| Database or Redis outage | proxy keeps running with the last snapshot; counters fall back to local |

How far the goals are met is described in [Performance and load comparison](docs/performance.html).

## One binary, two planes {#ebenen}

The `aigw` binary opens two listeners, which can be merged onto one port:

- **Data plane** (default `:4000`): OpenAI-compatible API, Anthropic Messages API and MCP gateway.
- **Control plane** (default `:4001`): admin API at `/admin/api/v1`, admin UI at `/admin/`,
  `/metrics`, `/healthz` and `/readyz`.

The split allows the control plane to be exposed only on the management network. The runtime is
tokio with hyper (HTTP/1.1 and HTTP/2) and rustls; towards the providers ai-gw keeps a connection
pool per endpoint with keep-alive and HTTP/2.

::: html
<figure class="diagram">
<svg class="g" viewBox="0 0 760 250" role="img" aria-labelledby="pipe-t pipe-d">
  <title id="pipe-t">Path of a request through ai-gw</title>
  <desc id="pipe-d">A request passes intake, authentication, context with model access, limit reservation, request plugins and cache. A cache hit answers immediately. Otherwise routing selects a deployment, the adapter translates into the provider format and sends it to the provider; errors before the first byte trigger retry or fallback. The response flows chunk by chunk through adapter and stream plugins to the client; afterwards usage and cost are accounted and a log event is written.</desc>
  <defs><marker id="pp-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-acc" d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box" x="6" y="20" width="96" height="44" rx="5"/><text class="b" x="54" y="40" text-anchor="middle">Intake</text><text class="s" x="54" y="55" text-anchor="middle">headers, size</text>
  <rect class="box" x="114" y="20" width="96" height="44" rx="5"/><text class="b" x="162" y="40" text-anchor="middle">Auth</text><text class="s" x="162" y="55" text-anchor="middle">key hash · JWT</text>
  <rect class="box" x="222" y="20" width="96" height="44" rx="5"/><text class="b" x="270" y="40" text-anchor="middle">Context</text><text class="s" x="270" y="55" text-anchor="middle">access · tools</text>
  <rect class="box" x="330" y="20" width="96" height="44" rx="5"/><text class="b" x="378" y="40" text-anchor="middle">Limits</text><text class="s" x="378" y="55" text-anchor="middle">reserve</text>
  <rect class="soft" x="438" y="20" width="96" height="44" rx="5"/><text class="b" x="486" y="40" text-anchor="middle">Plugins</text><text class="s" x="486" y="55" text-anchor="middle">Guardrails</text>
  <rect class="box" x="546" y="20" width="96" height="44" rx="5"/><text class="b" x="594" y="40" text-anchor="middle">Cache</text><text class="s" x="594" y="55" text-anchor="middle">exact · semantic</text>
  <path class="acc-ln" d="M102 42 H112M210 42 H220M318 42 H328M426 42 H436M534 42 H544" marker-end="url(#pp-ah)"/>
  <path class="acc-ln" d="M642 42 H700 V70" marker-end="url(#pp-ah)"/><text class="s" x="704" y="36">hit</text>
  <path class="acc-ln" d="M594 64 V100" marker-end="url(#pp-ah)"/>
  <rect class="box" x="546" y="104" width="96" height="44" rx="5"/><text class="b" x="594" y="124" text-anchor="middle">Routing</text><text class="s" x="594" y="139" text-anchor="middle">pick deployment</text>
  <rect class="box" x="438" y="104" width="96" height="44" rx="5"/><text class="b" x="486" y="124" text-anchor="middle">Adapter</text><text class="s" x="486" y="139" text-anchor="middle">provider format</text>
  <rect class="solid" x="330" y="104" width="96" height="44" rx="5"/><text class="on" x="378" y="131" text-anchor="middle">Provider</text>
  <path class="acc-ln" d="M546 126 H536M438 126 H428" marker-end="url(#pp-ah)"/>
  <path class="ln" d="M378 104 C378 86 594 86 594 100"/><text class="s" x="460" y="92" text-anchor="middle">retry · fallback before 1st byte</text>
  <path class="acc-ln" d="M378 148 V180" marker-end="url(#pp-ah)"/>
  <rect class="box" x="330" y="184" width="96" height="44" rx="5"/><text class="b" x="378" y="204" text-anchor="middle">Stream</text><text class="s" x="378" y="219" text-anchor="middle">chunk by chunk</text>
  <rect class="soft" x="438" y="184" width="96" height="44" rx="5"/><text class="b" x="486" y="204" text-anchor="middle">Stream-Plugins</text><text class="s" x="486" y="219" text-anchor="middle">check output</text>
  <rect class="box" x="652" y="74" width="100" height="154" rx="5"/><text class="b" x="702" y="146" text-anchor="middle">Client</text><text class="s" x="702" y="162" text-anchor="middle">input format</text>
  <path class="acc-ln" d="M426 206 H436M534 206 H648" marker-end="url(#pp-ah)"/>
  <rect class="box" x="114" y="184" width="200" height="44" rx="5"/><text class="b" x="214" y="204" text-anchor="middle">Accounting · log</text><text class="s" x="214" y="219" text-anchor="middle">usage, cost, ring buffer</text>
  <path class="ln" d="M330 206 H318" marker-end="url(#pp-ah)"/>
</svg>
<figcaption>Path of a request. All decisions come from the in-memory configuration snapshot.</figcaption>
</figure>
:::

## Path of a request {#hot-path}

1. **Intake:** read headers and parse the body only as far as needed. The body is read only after
   successful authentication; size and headers are limited.
2. **Authentication:** API key from `Authorization`, `api-key` or `x-api-key`, hashed with SHA-256
   and looked up in the snapshot – or a signed token verified against the configured issuer.
3. **Context:** resolve the model alias, check access, apply tool policies. The effective policy
   (organization → team → key → model group) is precomputed when the snapshot is built.
4. **Limits:** counters are reserved; when exceeded, `429` is returned immediately.
5. **Request plugins:** guardrails, PII masking, headers and transformations.
6. **Cache:** exact first, then semantic, if enabled.
7. **Routing:** pick a deployment from the model group; retries and fallbacks only while no byte
   has been sent to the client.
8. **Translation and streaming:** provider format there and back, chunk by chunk.
9. **Accounting:** usage settles the reservation, records costs and checks budgets.
10. **Log:** an event goes into a bounded channel without blocking; the proxy never waits for
    logs. If the channel is full, the event is dropped and counted.

## Configuration snapshot {#snapshot}

Every admin change runs as a database transaction, increments a monotonic configuration version
and writes the audit log. Every instance holds an **immutable snapshot** with precomputed indexes
(key hash → context, alias → model group, assembled plugin chains). Running requests keep their
snapshot; new ones see the new one immediately.

- With SQLite the snapshot is rebuilt after the commit, with Postgres on all instances via
  `LISTEN/NOTIFY`; a periodic version check catches lost notifications.
- Rebuilds are **incremental**: the audit log serves as the change journal and only affected
  objects are reloaded. A periodic consistency check compares against a full rebuild.
- Optionally ai-gw writes the snapshot to disk **encrypted** (AES-256-GCM with the master key). If
  the database is unreachable at startup, the gateway starts from this state and reports
  `degraded` on `/readyz`.

## Formats and provider adapters {#formate}

Incoming requests are translated into a canonical intermediate representation; each provider
adapter translates from there into its format and back. This makes every combination of input
format and provider possible, and plugins, cache and accounting work on a single model. Unknown
fields are preserved where the target format knows them.

## Streaming {#streaming}

- Bytes from the provider pass through an incremental SSE decoder, become events of the
  intermediate representation and are re-encoded in the client's format.
- **Backpressure:** data is read only when the client consumes it; there is no unbounded buffer.
- A **client abort** cancels the provider request immediately; if usage is missing, it is
  estimated and marked as estimated.
- Stream plugins work on a sliding window; if the whole response must be checked, the route can
  be switched to “buffered”.

## Limits, counters and budgets {#zaehler}

Counters are pluggable: **local** (per instance), **postgres-sync** (synchronized every one to two
seconds, slightly fuzzy) and **redis** (exact, distributed). If Redis fails, the gateway keeps
counting locally. Budgets can be strict (reserved before the request) or soft (settled afterwards).

## Storage and high availability {#datenhaltung}

SQLite is the default for a single instance. For multiple instances behind a load balancer,
Postgres serves as the shared database; counters then use `postgres-sync` or Redis, and the
semantic cache optionally pgvector or Redis Search. Provider credentials are stored encrypted with
AES-256-GCM in the database; the master key is never stored there. The request log is buffered and written in
batches and can also be exported via OpenTelemetry or as JSON Lines.

## Technology {#technik}

- **Gateway:** Rust (tokio, hyper/axum, tower, rustls with aws-lc-rs), split into crates for core
  and intermediate representation, proxy, providers, outbound connections with SSRF protection,
  token verification, persistence, counters, costs, plugins and PII detection, WASM plugins,
  cache, MCP, observability, tokenizer, webhooks and admin API.
- **Admin UI:** Svelte 5, Vite, TypeScript, Bits UI and Tailwind; the TypeScript types are
  generated from the admin API's OpenAPI specification.
- **Configuration:** YAML for startup configuration and GitOps resources, every startup value also
  as an `AIGW_…` environment variable.
- **Quality:** formatting, lints without warnings, tests, `cargo deny`, OpenAPI comparison, UI
  checks and REUSE compliance in one check pipeline; a license overview of all dependencies in the
  repository.

Further reading: [MCP gateway](docs/mcp-gateway.html) · [WASM plugins](docs/wasm-plugins.html) ·
[Workload and agent identities](docs/workload-identities.html) ·
[Operations and hardening](docs/operations.html).
