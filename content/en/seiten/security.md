title: Guardrails & security
summary: How ai-gw inspects prompts and responses – PII, prompt injection, system-prompt leaks, data exfiltration via links, languages, structured output, external content safety – and which protections apply inside the gateway itself.
toc: ja
de: sicherheit
---
An AI gateway sees every request and every response. That makes it the right place for
protective rules – and obliges it to handle data, keys and outbound connections carefully
itself. This page covers both.

## Guardrails as plugins {#guardrails}

Guardrails are ordinary plugins in the chain. They are bound globally or per organization, team,
key or model group, inherit inwards, can be locked against overrides and have a defined failure
behavior (`failMode: closed` rejects, `open` lets through). A typical order: cheap checks that
reject early first, then masking, then external services on the already masked text.

| Plugin | Phase | Purpose |
|---|---|---|
| `prompt-filter` | request, optionally response and stream | word and phrase lists, regex rules, prompt-injection heuristics, length and count limits, invisible Unicode characters |
| `pii` | request, response, stream | detect personal data and secrets; mask, remove, reject, pseudonymize (with re-identification) or count |
| `prompt-leak` | request, response, stream | system-prompt leaks via a canary token, optionally verbatim excerpts |
| `link-guard` | response, stream, optionally request | prevent exfiltration via links and images to foreign domains |
| `language` | request, optionally response | allowed or blocked languages |
| `schema-guard` | response, stream | validate structured output (JSON schema, JSON mode, forced tools) against its schema |
| `content-safety` | request, response, stream | external checks via Azure AI Content Safety, OpenAI Moderation or a custom guard model |

Rejected responses come back in the client's format (e.g. `finish_reason: content_filter` or a
refusal in Anthropic format) and carry the `x-aigw-guardrail` header naming the triggering plugin.

## PII and secrets {#pii}

PII detection is a dedicated rule-based engine without an external model. It detects e-mail
addresses, phone numbers (international and German), IBANs (with checksum for 75 countries),
credit cards (BIN ranges and Luhn), German tax IDs, social security, ID card and passport numbers
(each with check digit), IP addresses, credentials in URLs and API keys and tokens of common
services – plus an entropy heuristic for unknown secrets.

- **Actions per category:** mask (`[EMAIL_1]`), remove, reject, pseudonymize with
  re-identification in the response, or only count.
- **Allowlist** for known, harmless values (such as your own support address).
- **Fast:** a 4 KB prompt with findings is checked in about 23 µs (median, one core).
- On request the same engine masks content in the request log.

The engine deliberately does not detect names and postal addresses – without a language model they
would be too error-prone. An external service or guard model can be plugged in via
`content-safety` or a webhook instead.

## Prompt injection and invisible characters {#injection}

`prompt-filter` weighs known injection signals (“ignore all previous instructions”, role
switches, chat-template tokens …) and rejects above a threshold or only flags. It also detects
**invisible Unicode characters** – tag characters (“ASCII smuggling”), zero-width, bidi and format
characters – and strips them or rejects; legitimate cases such as emoji sequences or joiners in
Persian and Indic scripts are preserved. Word and regex rules can also check the output, in
streams across chunk boundaries.

## System-prompt leaks {#prompt-leak}

`prompt-leak` inserts a random **canary token** into the system prompt – new per request or stable,
so that providers' prompt caching keeps working. If the token appears in the response, stream,
tool arguments or reasoning, the output is blocked or the token removed; it never reaches the
client or the log. Optionally the plugin detects verbatim excerpts of the system prompt via word
n-grams.

## Exfiltration via links {#link-guard}

An injected instruction – for example in a tool result or a document – can make a model write
confidential data into an image URL. The chat client loads the image when rendering, without a
click, and the data ends up with the attacker. `link-guard` removes images pointing to foreign
domains and can defuse links, query parameters or long paths; allowed domains are configured
explicitly.

## Languages and structured output {#language}

`language` admits only allowed languages or blocks specific ones (ISO 639-1) – on the input and,
if desired, on the output. Detection runs locally without an external service; texts that are too
short or ambiguous can be exempted via a minimum length and minimum confidence.

`schema-guard` validates responses for which the client requested a JSON schema (OpenAI
`response_format`, Anthropic `output_config.format`), checks JSON-mode responses for valid JSON
and validates the arguments of forced tool calls against their parameter schema. On a violation
the response is flagged, rejected or requested again up to three times; retries are billed as
plugin costs. Schemas are limited in size and depth and evaluated without network or file access.

## External content safety {#content-safety}

`content-safety` queries Azure AI Content Safety (via API key or Microsoft Entra ID), OpenAI
Moderation or a **custom guard model** (e.g. Llama Guard) through a model group of the gateway.
Thresholds per category, checks on input, output or both, output buffered or sentence by sentence
in streams; tool-call arguments are checked too. The guard model's costs are recorded and can be
capped.

## Default profiles {#profile}

| Profile | Contents |
|---|---|
| **Basic** | injection heuristics with rejection, size limits, strip invisible characters; PII masking for e-mail, phone, IBAN, cards, API keys and URL credentials |
| **Strict** | locked bindings: stricter threshold, reject invisible characters, canary token, reject cards and secrets, mask further PII, remove images to foreign domains, optional external content safety; payload logging at most masked |
| **Open** | generous size limits only; payload logging metadata only |

Profiles are applied to a level via UI or admin API – with diff and dry run.

## Tools and MCP {#tools}

Applications send the tools a model may call with every request. ai-gw inventories them, detects
descriptions changed after the fact (“rug pull”), checks descriptions for injection signals and
enforces **tool policies**: allow, strip, reject, observe or approval required – including tool
calls in the response. MCP servers behind the gateway are invisible to everyone by default; grants
apply per team and key down to individual tools. More: [Tool policies](docs/tool-policies.html),
[MCP gateway](docs/mcp-gateway.html).

## Security of the gateway {#gateway}

- **Secrets:** credentials encrypted (AES-256-GCM), master key never in the database, rotation via
  `aigw config rekey`. API keys only as hashes; logs never contain `Authorization` or key headers,
  and incoming tokens are never forwarded to providers.
- **Outbound connections:** a shared component with **SSRF protection** – the URL is checked on
  save and the target address on every connection after name resolution (against DNS rebinding),
  no redirects, size and time limits. Private targets only after an explicit, narrowly scoped
  approval by global admins.
- **Listeners:** maximum concurrent connections, read timeouts against Slowloris, HTTP/2 limits,
  body limits; running streams are unaffected.
- **Admin access:** OIDC with PKCE, session cookies with the `__Host-` prefix, `SameSite=Strict` and
  CSRF tokens, a role model with team boundaries, a one-time bootstrap token valid only until the
  first admin.
- **Sandboxed plugins:** WASM modules without file system, network or environment, with limits on
  CPU, time and memory and optional Ed25519 signature enforcement – see
  [WASM plugins](docs/wasm-plugins.html).
- **Traceability:** audit log with hash chain, verifiable via API, UI and `aigw audit verify`.
- **Supply chain:** `cargo deny` with license and advisory checks, pinned UI dependencies with a
  minimum age for new packages, a license overview of all dependencies.

The project has gone through an internal security review; the resulting operational
recommendations are under [Operations and hardening](docs/operations.html). Please report
vulnerabilities confidentially: [Report a vulnerability](contribute.html#security).
