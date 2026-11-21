title: WASM plugins
summary: Custom plugin logic as a WebAssembly component – in a sandbox inside the gateway process, with limits for CPU, time and memory, hot reload and optional mandatory Ed25519 signatures.
group: konzept
order: 30
quelle: Concept 17 “WASM plugins” and measurements
de: wasm-plugins
---
The built-in plugins cover the common cases; for custom rules there used to be only the
webhook – with a network round trip per call. WASM plugins close the gap: operators
upload a **WebAssembly component** that ai-gw runs in the plugin chain without a fork and without an
external service – in-process, at a few tens of microseconds per call and also on the
stream path.

```text
Upload (admin API, UI) or file in the startup configuration
   └─► Module in the database ─► Configuration snapshot ─► Plugin chain (hot reload)
Binding  plugin: wasm, module: <name>
   └─► compile (cache per SHA-256) ─► describe(config) ─► instance per call
```

## Interface {#schnittstelle}

The interface is a WIT world (`aigw:plugin@0.1.0`) with two functions:

- `describe(config)` is called once when the chain is built, validates the configuration and
  reports the requested phases (request, response, stream event).
- `handle(input)` receives the phase, payload in the gateway's intermediate representation as JSON,
  request metadata (request ID, entry format, model group, key, team, organisation) and
  only the client headers that have been explicitly allowed.

The result is an action: **pass through**, **modify**, **block** (like a
guardrail rejection), **reject** with an error code, **respond with a fixed reply** (request phase only)
or **discard** (stream only). Plugins can set headers towards the provider and on the response –
sign-in and hop headers remain blocked.

The payload is deliberately JSON instead of fixed WIT records: the intermediate representation has many
optional fields and grows with every provider. This keeps the WIT world stable, and plugins
can use any JSON library of their language. The only host function is `log` – truncated
and limited, with the module name in the gateway log.

## Sandbox and limits {#sandbox}

| Limit | Implementation |
|---|---|
| CPU | **Fuel**: the runtime counts instructions; when the quota is used up, the call is aborted |
| Time | **Epoch interrupt** with a deadline per binding (default 100 ms) |
| Memory | Upper bound per instance (default 32 MiB, at most 256 MiB) |
| Instances | Pooling allocator with a fixed number of concurrent instances |
| WASI | WASI 0.2 **without grants**: no file system, no environment, no network; only clocks and randomness are allowed |
| Imports | only WASI 0.2 and the host interface; anything else fails at load time |
| State | **new instance per call** – no state between requests or tenants |

What happens on an error – quota used up, time expired, memory limit, crash,
invalid output – is decided by the binding's `failMode`; the default is `closed`, because
security plugins should reject when in doubt. The request and response phases run outside the
gateway's async workers, so that a slow module does not hold up other requests.

## Modules, approval and signatures {#signaturen}

- **Upload** via admin API or UI with a mandatory SHA-256; name, size
  and the component format are checked. Replacing and deleting require `If-Match`; deletion is only possible without
  referencing bindings.
- **Only global admins upload**, because a module runs in the gateway process. Organisation and
  team admins may **bind** approved modules at their level.
- Bindings can pin the SHA-256 and thereby allow exactly one version.
- **Signatures:** With configured trusted keys, ai-gw requires an
  Ed25519 signature over the module's hash (with its own domain prefix). The private key
  stays outside the gateway, for example in the build system; `aigw wasm keygen` and `aigw wasm sign`
  help with this. This also protects against write access to the database or a compromised
  admin account.
- Modules from the startup configuration enable a “YAML only” mode; a mismatching hash or
  a missing signature prevents startup.

## Binding {#bindung}

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
    config: {block: [secretproject], mask: [internal]}
    phases: [request]
    includeHeaders: [x-client-app]
    maxMemoryMb: 16
```

If a module reports only the response phase, the gateway buffers streamed responses; if it also reports
stream events, it runs live on every chunk.

## Compilation and hot reload {#hot-reload}

One engine per process compiles each component once per SHA-256 and keeps the result in
a cache; multiple bindings of the same module share the compilation. A new module
under the same name takes effect without a restart via the configuration snapshot; running calls
finish with the old instance. The encrypted snapshot cache contains the modules, so that even
a start without a database can run WASM plugins.

## Measurements {#messwerte}

| Case | Median |
|---|---|
| Empty plugin, request phase (including JSON, fresh instance and result) | ≈ 43 µs |
| Empty plugin, one stream event | ≈ 22 µs |
| “keyword-guard” example, request phase | ≈ 79 µs |

This is well below the gateway's latency budget and three to four orders of magnitude below
a webhook call. The example modules are 70 to 130 KB in size. The feature increases the
binary by around 14 MB; anyone who does not need WASM plugins disables them or builds without the
feature.

## Examples and metrics {#beispiele}

The repository contains the example plugin `keyword-guard` (block or mask keywords,
set response headers) and test plugins. Prometheus metrics count calls by
result, errors by type, duration, fuel consumed, compilations and rejected signatures.

Conceivable later: keyless signatures with a transparency log, approval under the four-eyes principle, further
host functions and asynchronous execution.
