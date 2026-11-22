title: Operations and hardening
summary: Recommendations for operating ai-gw – network and listeners, secrets, data storage and multiple instances, admin access, data plane, plugins, monitoring and audit.
group: betrieb
order: 20
quelle: Operations manual (installation, data storage, monitoring, hardening)
de: betrieb
---
The operations manual in the repository (`docs/betrieb/`) describes installation, configuration,
data storage, monitoring, sign-in via OIDC, troubleshooting, hardening and performance in detail.
This page summarizes the most important recommendations.

## Network and listeners {#netz}

- **Separate data plane and control plane.** The data plane (port 4000) is for applications; the
  control plane (port 4001) with admin API, UI and metrics belongs in the management network or behind
  an ingress with access restrictions.
- **Put a reverse proxy in front of the data plane:** TLS termination (ai-gw itself speaks plaintext HTTP/1.1
  and h2c), HSTS, connection and rate limits per client IP.
- **Connection protection in the gateway:** maximum number of concurrent connections per listener (beyond that
  immediately `503`), read timeouts for request head and body against Slowloris, keep-alive idle
  and HTTP/2 limits. Running responses – including streams lasting minutes – are not aborted by these timeouts.
  Choose the idle timeout larger than that of an upstream load balancer.
- **Outbound**, in addition to the SSRF check, an egress firewall: allow only providers, IdP, webhook and
  MCP targets, and block cloud metadata endpoints at the network level.
- Keep exceptions for private upstreams (e.g. a vLLM in your own network) as narrow as possible:
  individual hosts rather than large ranges. They apply only to resources created by global admins or
  GitOps.

## Secrets {#geheimnisse}

- Generate the master key with `aigw keygen`, mount it as a file secret and keep it **separate from
  database backups** – whoever has both has all credentials.
- Rotate via a list of previous keys and `aigw config rekey`; remove old keys after
  re-encryption.
- In GitOps manifests, use only references to environment variables (`AIGW_SECRET_*`) or files,
  never plaintext.
- Store the optional snapshot cache only on a path that nobody but the gateway user can write;
  its maximum age limits how long the gateway can start without a database from an old state.

## Data storage and multiple instances {#datenhaltung}

| Setup | Database | Counters | Note |
|---|---|---|---|
| Single instance | SQLite in a volume | local | simplest operation |
| Multiple instances | Postgres | Redis (exact) or reconciliation via Postgres | changes take effect everywhere in under a second via LISTEN/NOTIFY |
| High load | Postgres | Redis | otherwise the request log writer competes with budget reconciliation |

Database migrations run at startup; database backups contain credentials only in
encrypted form. If the database fails during operation, the gateway continues with the last snapshot;
if Redis fails, it continues counting locally.

## Admin access {#admin}

- Prefer **OIDC** (Microsoft Entra ID, Keycloak or another IdP) and bind roles to
  IdP groups; keep sessions short.
- The **bootstrap token** is valid only until the first global admin exists via OIDC or admin API key, and
  then expires automatically.
- The `gitops` role by default does not write users with roles or admin keys.
- Allow Entra sign-in to providers via workload or managed identity only by explicit opt-in;
  store certificate keys encrypted where possible.
- Invitation links are bearer tokens and belong in a confidential channel.

## Data plane {#datenebene}

- Keys with expiry date, limits and budgets per organization and team; revoked keys take effect
  immediately, across instances as well.
- With multiple instances, operate limits for concurrent requests with Redis counters; with
  reconciliation via Postgres they apply per instance.
- Limit MCP sessions per key and team to match usage.
- Guardrails with external services on `failMode: closed`; give a checking model its own
  capacity limit and limit the number of checks per request. Connect Azure AI Content
  Safety preferably with Entra ID instead of an API key.
- **Payload logging** only where necessary. Only `admin` and `auditor` read contents; where
  compliance obligations exist, set an upper bound at the organization and lock it.

## Plugins {#plugins}

- Have webhook plugins sign with a secret and set them to `failMode: closed`.
- WASM modules only from a trusted source, with mandatory signatures using your own Ed25519 keys
  (private key outside the gateway) and a pinned SHA-256 in the binding. Anyone who does not
  need WASM plugins disables them. Details: [WASM plugins](wasm-plugins.html).

## Monitoring {#monitoring}

- `/healthz` (liveness) and `/readyz` (readiness, with state `degraded` for a stale snapshot or one loaded from
  the cache) on both listeners.
- Prometheus metrics at `/metrics` – including requests, latencies, tokens, costs,
  upstream errors, circuit breakers, cache, dropped log events, connections and
  timeouts of the listeners, plugins, MCP and WASM. Alerts are particularly worthwhile for rejected
  connections, dropped log events and `degraded`.
- OpenTelemetry traces and logs via OTLP/HTTP, request log additionally as a JSON Lines file with
  rotation.

## Audit {#audit}

- Every admin change appears in the audit log with before/after; secrets are redacted.
- Verify the hash chain regularly (admin API, UI or `aigw audit verify`) and store the head hash
  externally.
- Write access to the database only for the gateway user.

## Dependencies {#abhaengigkeiten}

The check chain runs `cargo deny` (licenses and security advisories); for the UI additionally
`pnpm audit`. Deliberately accepted exceptions are documented with reasons and a review date in the
repository's configuration.

Performance data and recommendations for high load: [Performance and load comparison](performance.html).
