title: Performance and load comparison
summary: Test setup and results of the latency and load tests of ai-gw, plus a comparison with the LiteLLM proxy under identical conditions – with method, raw values and the limits of what the results show.
group: betrieb
order: 10
quelle: Operations manual “Performance” and measurement logs (November 2026)
de: leistung
---
A gateway sits in front of every model request. What it costs – latency, CPU, memory – is paid by every
application. ai-gw therefore measures this regularly with its own scripts, included in the repository.
The figures on this page come from runs in November 2026.

> **Context.** Measurements were taken against a test upstream that responds immediately. With real
> model providers, with response times from hundreds of milliseconds to seconds, the overhead of
> any gateway is small; what matters then is mainly CPU per request, memory, throughput per core
> and behaviour under many concurrent streams.

## Test setup {#aufbau}

- **Machine:** 8 vCPU (AMD EPYC, virtualised), 16 GB RAM, Linux. The machine was not exclusive during
  the measurements; all measurement processes therefore ran at real-time priority on
  fixed cores. Absolute values vary between runs by 20 to 30 percent; ratios
  within a run are reliable.
- **Separate cores:** test upstream (OpenAI-compatible, JSON and SSE) on two cores, the
  gateway on **two cores**, the load generator (keep-alive) on the rest.
- **Realistic chain without plugins:** API key check, organisation, team and key with limits and
  budgets, cost calculation via a price, request log enabled, routing with active retries
  and circuit breakers.
- **Overhead** = gateway minus a direct call to the upstream in the same scenario (percentiles
  subtracted from one another).

## Gateway latency {#latenz}

With the native binary, the overhead on a single connection was **80 to 92 µs (p50)** and
**under 200 µs (p99)**, for JSON as well as for time-to-first-token on streams. The target
“p99 under 1 ms” is met up to 2,000 requests per second over 200 connections (overhead
p99 140 to 380 µs). At 10,000 requests per second on only two cores, the overhead rises to
1.3 to 1.7 ms (p99); according to the measurements, this rate needs around four cores for p99 under 1 ms.

## Load tests {#last}

Long streams (200 chunks at 5 ms intervals) over 1,000 and 4,000 concurrent connections,
gateway still on two cores:

- **No errors** and no aborted streams, even with 4,000 concurrent
  streams. Under overload, backpressure shows up as longer stream duration, not as
  memory growth.
- **Memory stable:** 178 to 187 MiB over three identical rounds; around 85 KiB per open stream
  (client and upstream connection including buffers).
- **CPU per chunk** around 19 µs, mostly system calls; JSON saturation with 1,000 connections
  around 22,500 requests per second.
- For sustained load, Postgres is recommended over SQLite, because the request log and budget reconciliation
  share a write lock on SQLite.

## Comparison with LiteLLM {#litellm}

LiteLLM is one of the models for ai-gw and a widely used, feature-rich
open-source gateway. The comparison is meant to show how the different technical
approaches (Rust with in-memory configuration versus Python) play out under **identical conditions**.
It is not an overall assessment: feature scope, ecosystem and operational experience
are not reflected in the figures.

### Method {#methode}

| Variant | Setup |
|---|---|
| ai-gw with SQLite | Container from the repository; key with organisation, team and key limits, budgets, price, request log |
| ai-gw with Postgres | as above, Postgres 17 |
| LiteLLM without database | official image v1.108.8 (LTS); check against the master key – without a database the only key type |
| LiteLLM with Postgres | official database image v1.108.8; virtual key with models, budget, RPM and TPM limit; spend logs on |

- Each gateway container on the same **two cores**, host network, one instance.
- LiteLLM according to the published recommendations for production operation: two workers (equal
  to the core count), production mode, logging reduced to errors, batched writing of
  spend data, local price list. Redis is omitted with a single instance; ai-gw likewise uses the
  local counter.
- Measured: overhead on one connection and at 200 requests per second over 10
  connections, throughput at saturation with 10, 100 and 500 connections, errors, CPU per
  request (cgroup), memory (as in `docker stats`), cold start until readiness and image size.

### Results {#ergebnisse}

**Overhead compared with direct upstream** (JSON = total time, stream = time-to-first-token;
p50 / p90 / p99):

| Scenario | direct | ai-gw SQLite | ai-gw Postgres | LiteLLM | LiteLLM Postgres |
|---|---|---|---|---|---|
| JSON, 1 connection | 51 / 78 / 122 µs | +0.32 / +0.41 / +0.46 ms | +0.30 / +0.42 / +0.50 ms | +8.2 / +12.3 / +17.2 ms | +10.7 / +15.3 / +32.6 ms |
| Stream, 1 connection | 85 / 127 / 248 µs | +0.33 / +0.41 / +0.45 ms | +0.32 / +0.41 / +0.43 ms | +10.4 / +17.7 / +22.2 ms | +11.1 / +18.4 / +26.9 ms |
| JSON, 10 conn., 200 req/s | 211 / 265 / 352 µs | +0.40 / +0.47 / +0.59 ms | +0.45 / +0.51 / +0.82 ms | +11.1 / +28.9 / +44.0 ms | +25.0 / +55.8 / +101 ms ¹ |
| Stream, 10 conn., 200 req/s | 204 / 268 / 368 µs | +0.44 / +0.52 / +0.67 ms | +0.41 / +0.53 / +0.60 ms | +24.8 / +59.6 / +99.3 ms ¹ | +36.5 / +82.2 / +133 ms ¹ |

¹ Target rate not reached; the values include waiting time.

**Throughput at saturation** (requests per second; error rate in parentheses, otherwise no
errors):

| Mode, connections | ai-gw SQLite | ai-gw Postgres | LiteLLM | LiteLLM Postgres |
|---|---|---|---|---|
| JSON, 10 | 16,413 | 18,076 | 269 | 206 |
| JSON, 100 | 26,313 | 20,210 | 151 (0.5%) | 157 |
| JSON, 500 | 17,734 | 24,023 | 144 (3.5%) | 103 (4.6%) |
| Stream, 10 | 14,087 | 15,501 | 122 | 120 |
| Stream, 100 | 15,264 | 16,364 | 155 | 95 |
| Stream, 500 | 9,562 | 9,824 | 136 | 109 |

**Resources:**

| | ai-gw SQLite | ai-gw Postgres | LiteLLM | LiteLLM Postgres |
|---|---|---|---|---|
| CPU per request (JSON, 100 conn.) | 79 µs | 101 µs | 8,810 µs | 10,598 µs |
| CPU per request (stream, 100 conn.) | 134 µs | 124 µs | 13,420 µs | 18,561 µs |
| Memory at idle | 35 MiB | 29 MiB | 1,626 MiB | 1,700 MiB |
| Memory, peak under load | 317 MiB | 180 MiB | 1,959 MiB | 2,323 MiB |
| Cold start, first start (empty DB) | 0.60 s | 0.36 s | 25.6 s | 28.3 s |
| Cold start, restart | 0.27 s | 0.35 s | 22.6 s | 24.2 s |
| Image unpacked / compressed | 111 / 30 MiB | 111 / 30 MiB | 1,730 / 398 MiB | 1,648 / 383 MiB |

### Interpretation {#einordnung}

- On the same two cores, the overhead of ai-gw on a single connection was lower by a factor of 25
  to 35, the throughput at saturation higher by a factor of 60 to 230 and the CPU per
  request lower by a factor of 100 to 150. The differences are considerably larger than the
  fluctuations of the measurement machine.
- From 100 connections, LiteLLM did not complete all requests (connection drops, with Postgres
  at 500 connections additionally `503`); ai-gw remained error-free in all runs.
- The overhead of ai-gw in the container (around 0.3 ms) is above that of the native binary (around
  0.09 ms) – causes are the container cgroup, the shared machine and wake-up costs at
  low rates.

### Limits of the results {#grenzen}

- Test upstream without real model time; OpenAI entry point only, no plugins, guardrails or cache.
- Only two cores and one instance per gateway. LiteLLM scales horizontally via further workers
  and instances (according to its documentation one vCPU and at least 4 GiB per worker); more workers, Redis
  and other ASGI servers were not measured.
- LiteLLM without a database checks only the master key and therefore has less to do than the
  ai-gw chain; the functionally comparable variant is LiteLLM with Postgres.
- The machine was not exclusive; absolute figures vary, the ratios are reliable.

## Measure it yourself {#reproduktion}

The scripts are in the repository under `scripts/` (`bench-e2e.sh`, `bench-latency.sh`,
`bench-coldstart.sh`, `bench-litellm.sh`) and write their results to `target/bench/`.
The raw logs of the runs shown here are under `docs/betrieb/messwerte/`. For
reliable absolute figures, an exclusive machine is recommended.
